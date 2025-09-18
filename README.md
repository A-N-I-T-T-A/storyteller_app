# Storyteller AI - Original Generator

A Flask web application that generates creative stories using the specialized **Original Story Generator** model.

## 🚀 Features

- **Original Story Generator**: Uses `pranavpsv/gpt2-genre-story-generator` model
- **Multiple Genres**: Fantasy, Romance, Sci-Fi, Horror, Mystery
- **Adjustable Length**: Short, Medium, Long stories
- **Text-to-Speech**: Convert generated stories to audio
- **Download Stories**: Save stories as text files
- **Beautiful UI**: Modern, responsive design

## 🛠️ Technology Stack

- **Backend**: Flask, Transformers, PyTorch
- **AI Model**: Original Story Generator (pranavpsv/gpt2-genre-story-generator)
- **TTS**: Google Text-to-Speech (gTTS)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap

## 📋 Prerequisites

- Python 3.8+
- 2GB+ RAM recommended
- Internet connection (for model download)

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://localhost:5000` to use the application.

## 🌐 Usage

1. Select a genre (Fantasy, Romance, Sci-Fi, Horror, Mystery)
2. Choose story length (Short, Medium, Long)
3. Enter your story prompt
4. Click "Generate Story"
5. Download or convert to speech

## 📊 API Endpoints

- `GET /` - Main interface
- `POST /` - Generate story
- `POST /download_story` - Download story as text file
- `POST /generate_speech` - Convert story to audio
- `POST /debug` - Debug form parameters

## 🚀 Deployment

For production deployment on Render:

1. Upload to GitHub
2. Connect to Render
3. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Python Version**: 3.11

## 📁 Project Structure

```
storyteller_app/
├── app.py                 # Main Flask application
├── requirements.txt       # Dependencies
├── README.md             # This file
└── templates/
    └── index.html        # Main interface
```

---
**Built with ❤️ for creative storytelling**
