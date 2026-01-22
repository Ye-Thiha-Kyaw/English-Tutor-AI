# Flask server
import sys
import os

# Add backend and database directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database'))

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from tutor import EnglishTutor

# Initialize database on startup
try:
    from models import init_database
    init_database()
except Exception as e:
    print(f"Database initialization warning: {e}")

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Initialize the tutor
tutor = EnglishTutor()


# Main pages
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


# API endpoints
@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        result = tutor.process_message(user_message)
        return jsonify(result)

    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({
            'message': 'Sorry, there was an error processing your message. Please try again.',
            'corrections': [],
            'feedback': {}
        })


@app.route('/api/mode', methods=['POST'])
def set_mode():
    """Switch between tutor and chat mode"""
    data = request.json
    mode = data.get('mode', 'tutor')

    if mode not in ['tutor', 'chat']:
        return jsonify({'error': 'Invalid mode'}), 400

    tutor.set_mode(mode)
    return jsonify({
        'status': 'ok',
        'mode': mode,
        'message': f'Switched to {mode} mode'
    })


@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """Get comprehensive feedback for chat mode session"""
    try:
        feedback = tutor.get_session_feedback()
        return jsonify(feedback)
    except Exception as e:
        print(f"Error getting feedback: {e}")
        return jsonify({
            'error': 'Could not generate feedback',
            'overall_score': 0,
            'grammar_errors': [],
            'vocabulary_suggestions': [],
            'strengths': [],
            'areas_to_improve': [],
            'tips': [],
            'encouragement': 'Please try again!'
        })


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    tutor.clear_history()
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
