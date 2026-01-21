# English Tutor AI

An AI-powered English language tutor with voice recognition and text-to-speech capabilities.

## Features

- Real-time grammar checking and corrections
- Voice input with speech recognition
- Text-to-speech for AI responses
- Progress tracking and vocabulary building
- Adaptive difficulty based on user level

## Project Structure

```
english-tutor-ai/
├── backend/
│   ├── __init__.py
│   ├── app.py           # Flask server
│   ├── graph.py         # LangGraph workflow
│   ├── nodes.py         # Graph nodes (functions)
│   ├── state.py         # State definition
│   ├── prompts.py       # AI prompts
│   └── config.py        # Configuration
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js   # Voice recognition & TTS
│   └── templates/
│       └── index.html   # Main UI
├── database/
│   └── init_db.py       # Database setup
├── requirements.txt
├── .env                 # API keys (not committed)
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env` and add your API keys:
   ```bash
   cp .env.example .env
   ```
5. Initialize the database:
   ```bash
   python database/init_db.py
   ```
6. Run the application:
   ```bash
   python backend/app.py
   ```
7. Open http://localhost:5000 in your browser

## Usage

- Type a message or click the microphone button to speak
- The AI will respond and correct any grammar mistakes
- View tips and feedback for improvement
- Track your progress over time

## Technologies

- **Backend**: Flask, LangGraph, LangChain
- **Frontend**: HTML, CSS, JavaScript
- **AI**: OpenAI GPT-4 / Anthropic Claude
- **Database**: SQLite
- **Voice**: Web Speech API
