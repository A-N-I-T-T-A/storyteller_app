from flask import Flask, render_template, request, send_file, jsonify
from transformers import pipeline
from gtts import gTTS
import io
import tempfile
import os
import threading
import time

app = Flask(__name__)

# Available models for story generation
AVAILABLE_MODELS = {
    "original": {
        "name": "Original Story Generator",
        "model": "pranavpsv/gpt2-genre-story-generator",
        "description": "Specialized for story generation"
    }
}

# Load default model - only the original generator
current_model = "original"
generator = pipeline("text-generation", model=AVAILABLE_MODELS[current_model]["model"])

def clean_and_complete_story(story):
    """Clean up the generated story and ensure it has a proper ending"""
    if not story:
        return "Sorry, I couldn't generate a story this time. Please try again."
    
    # Remove any remaining prompt fragments
    story = story.strip()
    
    # Check if the story ends abruptly (common issues)
    incomplete_endings = [
        "The old woman then asks the girl if she will",
        "and is eventually caught up in the story line",
        "taken away by the evil witch",
        "However, Jyao has trouble finding out",
        "and is later captured by the Fairy Godmother"
    ]
    
    # If the story ends with an incomplete sentence, try to complete it
    for ending in incomplete_endings:
        if story.endswith(ending):
            # Add a simple conclusion
            story += " find the answers they seek and live happily ever after."
            break
    
    # Ensure the story ends with proper punctuation
    if story and not story.endswith(('.', '!', '?')):
        # Check if it's mid-sentence
        last_sentence = story.split('.')[-1].strip()
        if len(last_sentence) > 10:  # If there's a substantial last sentence
            story += "."
        else:
            # If it's clearly cut off, add a conclusion
            story = story.rstrip('.') + " and they all lived happily ever after."
    
    # Clean up any duplicate sentences or repetitive content
    sentences = story.split('.')
    cleaned_sentences = []
    seen_sentences = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence not in seen_sentences and len(sentence) > 5:
            cleaned_sentences.append(sentence)
            seen_sentences.add(sentence)
    
    # Rejoin sentences
    story = '. '.join(cleaned_sentences)
    if story and not story.endswith('.'):
        story += '.'
    
    return story

def load_model(model_key):
    """Load a specific model for story generation"""
    global generator, current_model
    try:
        if model_key in AVAILABLE_MODELS:
            generator = pipeline("text-generation", model=AVAILABLE_MODELS[model_key]["model"])
            current_model = model_key
            return True
    except Exception as e:
        print(f"Error loading model {model_key}: {e}")
        return False
    return False

def generate_story_with_retry(full_prompt, max_length, max_retries=3):
    """Generate a story with retry logic to ensure completion"""
    for attempt in range(max_retries):
        try:
            # Generate the story with improved parameters
            output = generator(
                full_prompt,
                max_length=max_length + len(full_prompt.split()),  # Account for prompt length
                do_sample=True,
                temperature=0.7 + (attempt * 0.1),  # Vary temperature on retries
                top_k=40,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=generator.tokenizer.eos_token_id,
                eos_token_id=generator.tokenizer.eos_token_id,
                no_repeat_ngram_size=2
            )[0]["generated_text"]

            # Extract story content more robustly
            story = output.replace(full_prompt, "").strip()
            
            # Clean up the story and ensure it ends properly
            story = clean_and_complete_story(story)
            
            # Check if the story is complete enough
            if is_story_complete(story):
                return story
                
        except Exception as e:
            print(f"Story generation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return "Sorry, I encountered an issue generating your story. Please try again with a different prompt."
    
    return "Sorry, I couldn't generate a complete story this time. Please try again with a different prompt."

def is_story_complete(story):
    """Check if the story appears to be complete"""
    if not story or len(story.strip()) < 50:
        return False
    
    # Check for common incomplete patterns
    incomplete_patterns = [
        "The old woman then asks the girl if she will",
        "and is eventually caught up in the story line",
        "taken away by the evil witch",
        "However, Jyao has trouble finding out",
        "and is later captured by the Fairy Godmother",
        "and is later captured by",
        "taken away by the",
        "asks the girl if she will"
    ]
    
    story_lower = story.lower()
    for pattern in incomplete_patterns:
        if pattern.lower() in story_lower and story_lower.endswith(pattern.lower()):
            return False
    
    # Check if it ends with proper punctuation
    if not story.rstrip().endswith(('.', '!', '?')):
        return False
    
    # Check minimum length based on story complexity
    if len(story.split()) < 30:  # At least 30 words
        return False
    
    return True

@app.route("/", methods=["GET", "POST"])
def index():
    story = ""
    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        genre = request.form.get("genre", "Fantasy")
        length = request.form.get("length_value", "medium")
        selected_model = request.form.get("model", "original")
        
        # Validate inputs
        if not prompt:
            return render_template("index.html", 
                                 story="Please enter a story prompt!", 
                                 available_models=AVAILABLE_MODELS, 
                                 current_model=current_model)
        
        # Validate genre
        valid_genres = ["Fantasy", "Romance", "Sci-Fi", "Horror", "Mystery"]
        if genre not in valid_genres:
            genre = "Fantasy"
        
        # Validate length
        valid_lengths = ["short", "medium", "long"]
        if length not in valid_lengths:
            length = "medium"
        
        # Validate model - only allow original
        if selected_model not in AVAILABLE_MODELS:
            selected_model = "original"
        
        # Load the selected model if different from current
        if selected_model != current_model:
            if not load_model(selected_model):
                return render_template("index.html", 
                                     story="Error loading AI model. Please try again.", 
                                     available_models=AVAILABLE_MODELS, 
                                     current_model=current_model)
        
        # Map length to token counts (increased for better completion)
        length_map = {
            "short": 400,    # Increased from 200
            "medium": 600,   # Increased from 400
            "long": 1000     # Increased from 800
        }
        max_length = length_map.get(length, 600)
        
        # Create genre-specific prompts
        genre_prompts = {
            "Fantasy": f"Write a fantasy story with magic, mythical creatures, and adventure. Theme: {prompt}",
            "Romance": f"Write a romantic story about love, relationships, and emotions. Theme: {prompt}",
            "Sci-Fi": f"Write a science fiction story with futuristic technology, space, or advanced science. Theme: {prompt}",
            "Horror": f"Write a horror story that creates suspense, fear, and mystery. Theme: {prompt}",
            "Mystery": f"Write a mystery story with puzzles, clues, and investigation. Theme: {prompt}"
        }
        
        full_prompt = f"{genre_prompts.get(genre, genre_prompts['Fantasy'])}\n\nStory:"

        # Log the parameters for debugging
        print(f"Story Generation Parameters:")
        print(f"  Genre: {genre}")
        print(f"  Length: {length} ({max_length} tokens)")
        print(f"  Model: {selected_model}")
        print(f"  Prompt: {prompt[:50]}...")
        
        # Generate the story with improved parameters and retry logic
        story = generate_story_with_retry(full_prompt, max_length)

    return render_template("index.html", story=story, available_models=AVAILABLE_MODELS, current_model=current_model)

@app.route("/debug", methods=["POST"])
def debug_params():
    """Debug route to test form parameters"""
    data = {
        "prompt": request.form.get("prompt", ""),
        "genre": request.form.get("genre", ""),
        "length": request.form.get("length_value", ""),
        "model": request.form.get("model", "original"),
        "all_form_data": dict(request.form)
    }
    return jsonify(data)

@app.route("/download_story", methods=["POST"])
def download_story():
    story_content = request.form.get("story_content", "")
    if not story_content:
        return "No story to download", 400
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    temp_file.write(story_content)
    temp_file.close()
    
    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name="generated_story.txt",
        mimetype="text/plain"
    )

@app.route("/generate_speech", methods=["POST"])
def generate_speech():
    try:
        story_content = request.form.get("story_content", "")
        if not story_content:
            return jsonify({"error": "No story content provided"}), 400
        
        # Clean up the story content for better TTS
        cleaned_story = story_content.strip()
        
        # Create TTS object
        tts = gTTS(text=cleaned_story, lang='en', slow=False)
        
        # Create a temporary audio file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_audio.name)
        temp_audio.close()
        
        return send_file(
            temp_audio.name,
            as_attachment=False,
            mimetype="audio/mpeg"
        )
        
    except Exception as e:
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500

# Cleanup function for temporary files
def cleanup_temp_files():
    """Clean up temporary files older than 1 hour"""
    temp_dir = tempfile.gettempdir()
    current_time = time.time()
    
    for filename in os.listdir(temp_dir):
        if filename.startswith('tmp') and (filename.endswith('.txt') or filename.endswith('.mp3')):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.getmtime(file_path) < current_time - 3600:  # 1 hour
                    os.remove(file_path)
            except OSError:
                pass

# Schedule cleanup every hour
def schedule_cleanup():
    while True:
        time.sleep(3600)  # 1 hour
        cleanup_temp_files()

# Start cleanup thread
cleanup_thread = threading.Thread(target=schedule_cleanup, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    app.run(debug=True)
