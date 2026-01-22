// Voice recognition & TTS for English Tutor AI

class EnglishTutor {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.voiceBtn = document.getElementById('voice-btn');
        this.voiceSelect = document.getElementById('voice-select');

        // Mode elements
        this.tutorModeBtn = document.getElementById('tutor-mode-btn');
        this.chatModeBtn = document.getElementById('chat-mode-btn');
        this.modeDescription = document.getElementById('mode-description');
        this.getFeedbackBtn = document.getElementById('get-feedback-btn');

        // Feedback modal elements
        this.feedbackModal = document.getElementById('feedback-modal');
        this.closeModalBtn = document.getElementById('close-modal');
        this.feedbackBody = document.getElementById('feedback-body');
        this.overallScore = document.getElementById('overall-score');
        this.scoreCircle = document.getElementById('score-circle');

        this.isRecording = false;
        this.isVoiceMode = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.selectedVoice = null;
        this.voices = [];
        this.isSpeaking = false;

        // Silence detection for waiting until user finishes speaking
        this.silenceTimeout = null;
        this.silenceDelay = 1500; // Wait 1.5 seconds of silence before sending
        this.lastTranscript = '';

        // Current mode: 'tutor' or 'chat'
        this.currentMode = 'tutor';
        this.chatMessagesCount = 0;

        this.initEventListeners();
        this.initSpeechRecognition();
        this.initVoices();
    }

    initEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        this.voiceBtn.addEventListener('click', () => this.toggleVoiceMode());

        // Voice selection change
        if (this.voiceSelect) {
            this.voiceSelect.addEventListener('change', (e) => {
                const voiceIndex = parseInt(e.target.value);
                this.selectedVoice = this.voices[voiceIndex] || null;
                this.speak('Hello! This is how I sound.');
            });
        }

        // Mode toggle buttons
        if (this.tutorModeBtn) {
            this.tutorModeBtn.addEventListener('click', () => this.switchMode('tutor'));
        }
        if (this.chatModeBtn) {
            this.chatModeBtn.addEventListener('click', () => this.switchMode('chat'));
        }

        // Get feedback button
        if (this.getFeedbackBtn) {
            this.getFeedbackBtn.addEventListener('click', () => this.getFeedback());
        }

        // Close modal
        if (this.closeModalBtn) {
            this.closeModalBtn.addEventListener('click', () => this.closeModal());
        }
        if (this.feedbackModal) {
            this.feedbackModal.addEventListener('click', (e) => {
                if (e.target === this.feedbackModal) this.closeModal();
            });
        }
    }

    async switchMode(mode) {
        if (mode === this.currentMode) return;

        if (this.currentMode === 'chat' && this.chatMessagesCount > 0) {
            const shouldGetFeedback = confirm('You have messages in chat mode. Would you like to get feedback before switching?');
            if (shouldGetFeedback) {
                await this.getFeedback();
            }
        }

        try {
            const response = await fetch('/api/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });

            const data = await response.json();

            if (data.status === 'ok') {
                this.currentMode = mode;
                this.chatMessagesCount = 0;
                this.updateModeUI();
                this.clearChat();
                this.showWelcomeMessage();
            }
        } catch (error) {
            console.error('Error switching mode:', error);
        }
    }

    updateModeUI() {
        const feedbackBtn = document.getElementById('get-feedback-btn');

        if (this.currentMode === 'tutor') {
            this.tutorModeBtn.classList.add('active');
            this.chatModeBtn.classList.remove('active');
            this.modeDescription.textContent = 'Practice your English with instant corrections';
            if (feedbackBtn) {
                feedbackBtn.setAttribute('data-visible', 'false');
            }
        } else {
            this.chatModeBtn.classList.add('active');
            this.tutorModeBtn.classList.remove('active');
            this.modeDescription.textContent = 'Chat naturally, get feedback when you\'re done';
            if (feedbackBtn) {
                feedbackBtn.setAttribute('data-visible', 'true');
            }
        }
    }

    showWelcomeMessage() {
        const welcomeMessages = {
            tutor: "Hello! I'm your English tutor. Feel free to practice speaking or writing with me. I'll help you improve your grammar and vocabulary with instant corrections. What would you like to talk about today?",
            chat: "Hey there! I'm here to chat with you like a friend. Just talk naturally about anything - hobbies, movies, your day, whatever you want! When you're done, click 'Get Feedback' to see how you did. So, what's on your mind?"
        };

        this.addMessage(welcomeMessages[this.currentMode], 'assistant');
    }

    clearChat() {
        this.chatContainer.innerHTML = '';
    }

    async getFeedback() {
        if (this.chatMessagesCount === 0) {
            alert('No messages to analyze. Start chatting first!');
            return;
        }

        this.feedbackModal.style.display = 'flex';
        this.feedbackBody.innerHTML = '<div class="feedback-loading"><div class="loading"><span></span><span></span><span></span></div><p>Analyzing your conversation...</p></div>';
        this.overallScore.textContent = '...';

        try {
            const response = await fetch('/api/feedback');
            const feedback = await response.json();

            this.displayFeedback(feedback);
        } catch (error) {
            console.error('Error getting feedback:', error);
            this.feedbackBody.innerHTML = '<p class="error">Could not load feedback. Please try again.</p>';
        }
    }

    displayFeedback(feedback) {
        let score = feedback.overall_score || 0;

        // Convert score to 100 scale if it's on a 10 scale
        if (score <= 10 && score > 0) {
            score = score * 10;
        }

        this.overallScore.textContent = Math.round(score);

        if (score >= 80) {
            this.scoreCircle.className = 'score-circle excellent';
        } else if (score >= 60) {
            this.scoreCircle.className = 'score-circle good';
        } else if (score >= 40) {
            this.scoreCircle.className = 'score-circle average';
        } else {
            this.scoreCircle.className = 'score-circle needs-work';
        }

        let html = '';

        if (feedback.encouragement) {
            html += `<div class="feedback-encouragement">${feedback.encouragement}</div>`;
        }

        if (feedback.strengths && feedback.strengths.length > 0) {
            html += `
                <div class="feedback-section strengths">
                    <h3>What You Did Well</h3>
                    <ul>${feedback.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
                </div>
            `;
        }

        if (feedback.grammar_errors && feedback.grammar_errors.length > 0) {
            html += `
                <div class="feedback-section errors">
                    <h3>Grammar Corrections</h3>
                    <div class="error-list">
                        ${feedback.grammar_errors.map(err => `
                            <div class="error-item">
                                <div class="error-original">"${err.original}"</div>
                                <div class="error-arrow">→</div>
                                <div class="error-corrected">"${err.corrected}"</div>
                                <div class="error-explanation">${err.explanation}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (feedback.vocabulary_suggestions && feedback.vocabulary_suggestions.length > 0) {
            html += `
                <div class="feedback-section vocabulary">
                    <h3>Vocabulary Suggestions</h3>
                    <div class="vocab-list">
                        ${feedback.vocabulary_suggestions.map(vocab => `
                            <div class="vocab-item">
                                <div class="vocab-original">Instead of: "${vocab.original}"</div>
                                <div class="vocab-alternatives">Try: ${vocab.better_alternatives.join(', ')}</div>
                                ${vocab.context ? `<div class="vocab-context">${vocab.context}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (feedback.areas_to_improve && feedback.areas_to_improve.length > 0) {
            html += `
                <div class="feedback-section improve">
                    <h3>Areas to Improve</h3>
                    <ul>${feedback.areas_to_improve.map(a => `<li>${a}</li>`).join('')}</ul>
                </div>
            `;
        }

        if (feedback.tips && feedback.tips.length > 0) {
            html += `
                <div class="feedback-section tips">
                    <h3>Tips for Next Time</h3>
                    <ul>${feedback.tips.map(t => `<li>${t}</li>`).join('')}</ul>
                </div>
            `;
        }

        html += `<div class="feedback-footer">Based on ${feedback.total_messages || this.chatMessagesCount} messages</div>`;

        this.feedbackBody.innerHTML = html;
    }

    closeModal() {
        this.feedbackModal.style.display = 'none';
    }

    initVoices() {
        const loadVoices = () => {
            this.voices = this.synthesis.getVoices();

            const englishVoices = this.voices.filter(voice =>
                voice.lang.startsWith('en')
            );

            if (this.voiceSelect && englishVoices.length > 0) {
                this.voiceSelect.innerHTML = '';

                const sortedVoices = englishVoices.sort((a, b) => {
                    const aScore = this.getVoiceQualityScore(a);
                    const bScore = this.getVoiceQualityScore(b);
                    return bScore - aScore;
                });

                sortedVoices.forEach((voice, index) => {
                    const option = document.createElement('option');
                    const originalIndex = this.voices.indexOf(voice);
                    option.value = originalIndex;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    if (this.getVoiceQualityScore(voice) > 0) {
                        option.textContent += ' ★';
                    }
                    this.voiceSelect.appendChild(option);
                });

                if (sortedVoices.length > 0) {
                    this.selectedVoice = sortedVoices[0];
                    this.voiceSelect.value = this.voices.indexOf(sortedVoices[0]);
                }
            }
        };

        if (this.synthesis.onvoiceschanged !== undefined) {
            this.synthesis.onvoiceschanged = loadVoices;
        }
        loadVoices();
    }

    getVoiceQualityScore(voice) {
        let score = 0;
        const name = voice.name.toLowerCase();

        if (name.includes('natural')) score += 3;
        if (name.includes('neural')) score += 3;
        if (name.includes('premium')) score += 2;
        if (name.includes('enhanced')) score += 2;
        if (name.includes('wavenet')) score += 2;
        if (name.includes('studio')) score += 2;
        if (name.includes('online')) score += 1;
        if (name.includes('google')) score += 1;
        if (name.includes('microsoft')) score += 1;

        if (voice.lang === 'en-US' || voice.lang === 'en-GB') score += 1;

        return score;
    }

    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;  // Keep listening
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';

            this.recognition.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                // Update the display
                const currentText = this.lastTranscript + finalTranscript + interimTranscript;
                this.messageInput.value = currentText;
                this.updateLiveTranscription(currentText);

                // If we got final results, add to lastTranscript
                if (finalTranscript) {
                    this.lastTranscript += finalTranscript;
                }

                // Reset silence timer - wait for user to finish speaking
                this.resetSilenceTimer();
            };

            this.recognition.onend = () => {
                this.isRecording = false;
                // Don't auto-restart here - let speakAndWait handle restart after AI finishes
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isRecording = false;

                if (event.error === 'no-speech' && this.isVoiceMode) {
                    this.startListening();
                } else if (event.error !== 'aborted' && event.error !== 'not-allowed') {
                    // Try to restart on recoverable errors
                    if (this.isVoiceMode) {
                        setTimeout(() => this.startListening(), 500);
                    }
                }
            };
        } else {
            this.voiceBtn.style.display = 'none';
            console.warn('Speech recognition not supported');
        }
    }

    resetSilenceTimer() {
        // Clear existing timer
        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
        }

        // Set new timer - when silence is detected for 1.5 seconds, send the message
        this.silenceTimeout = setTimeout(() => {
            if (this.isVoiceMode && this.messageInput.value.trim()) {
                this.finishSpeaking();
            }
        }, this.silenceDelay);
    }

    finishSpeaking() {
        // User finished speaking - send the message
        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
            this.silenceTimeout = null;
        }

        const message = this.messageInput.value.trim();
        if (message && this.isVoiceMode) {
            // Stop recognition temporarily
            if (this.recognition) {
                this.recognition.stop();
            }

            this.removeLiveTranscription();
            this.lastTranscript = '';
            this.sendMessage(true);
        }
    }

    // Interrupt AI when user starts speaking
    interruptAI() {
        if (this.isSpeaking) {
            this.synthesis.cancel();
            this.isSpeaking = false;
            this.removeStatusMessage();
        }
    }

    toggleVoiceMode() {
        if (this.isVoiceMode) {
            this.stopVoiceMode();
        } else {
            this.startVoiceMode();
        }
    }

    startVoiceMode() {
        this.isVoiceMode = true;
        this.lastTranscript = '';
        this.voiceBtn.classList.add('recording');
        this.voiceBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
            </svg>
        `;
        this.showStatusMessage('Listening... (speak naturally, I\'ll wait for you to finish)');
        this.startListening();
    }

    stopVoiceMode() {
        this.isVoiceMode = false;
        this.isRecording = false;
        this.lastTranscript = '';

        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
            this.silenceTimeout = null;
        }

        this.voiceBtn.classList.remove('recording');
        this.voiceBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
        `;

        if (this.recognition) {
            this.recognition.stop();
        }
        this.synthesis.cancel();
        this.isSpeaking = false;
        this.removeStatusMessage();
        this.removeLiveTranscription();
    }

    startListening() {
        if (!this.isVoiceMode || this.isSpeaking || this.isRecording) return;

        try {
            // Interrupt AI if speaking
            this.interruptAI();

            this.recognition.start();
            this.isRecording = true;
            this.showStatusMessage('Listening... (speak naturally)');
        } catch (e) {
            console.log('Recognition already running or error:', e);
            // If already running, that's okay
            if (e.name === 'InvalidStateError') {
                this.isRecording = true;
            }
        }
    }

    showStatusMessage(text) {
        this.removeStatusMessage();
        const statusDiv = document.createElement('div');
        statusDiv.id = 'voice-status';
        statusDiv.className = 'voice-status';
        statusDiv.innerHTML = `
            <div class="status-indicator">
                <span class="pulse-dot"></span>
                <span>${text}</span>
            </div>
        `;
        this.chatContainer.appendChild(statusDiv);
        this.scrollToBottom();
    }

    removeStatusMessage() {
        const status = document.getElementById('voice-status');
        if (status) status.remove();
    }

    updateLiveTranscription(text) {
        let liveDiv = document.getElementById('live-transcription');
        if (!liveDiv) {
            liveDiv = document.createElement('div');
            liveDiv.id = 'live-transcription';
            liveDiv.className = 'message user live-transcription';
            this.chatContainer.appendChild(liveDiv);
        }
        liveDiv.innerHTML = `<div class="message-bubble">${text}<span class="typing-cursor">|</span></div>`;
        this.scrollToBottom();
    }

    removeLiveTranscription() {
        const live = document.getElementById('live-transcription');
        if (live) live.remove();
    }

    async sendMessage(fromVoice = false) {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.messageInput.value = '';

        this.showLoading();

        if (fromVoice) {
            this.showStatusMessage('Thinking...');
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            this.hideLoading();

            this.addMessage(data.message, 'assistant', data.corrections);

            if (data.mode === 'chat' && data.messages_count) {
                this.chatMessagesCount = data.messages_count;
            }

            if (data.feedback && data.mode === 'tutor') {
                this.showFeedback(data.feedback);
            }

            // Speak the response
            if (fromVoice && this.isVoiceMode) {
                this.showStatusMessage('Speaking...');
                await this.speakAndWait(data.message);

                // After speaking, wait a moment then start listening again
                if (this.isVoiceMode) {
                    this.showStatusMessage('Listening... (speak naturally)');
                    // Extra delay to ensure mic doesn't pick up residual audio
                    setTimeout(() => {
                        if (this.isVoiceMode && !this.isSpeaking) {
                            this.startListening();
                        }
                    }, 300);
                }
            } else if (!this.isVoiceMode) {
                // Only auto-speak in non-voice mode (manual text input)
                this.speak(data.message);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideLoading();
            this.addMessage('Sorry, there was an error. Please try again.', 'assistant');

            if (this.isVoiceMode) {
                this.startListening();
            }
        }
    }

    addMessage(text, sender, corrections = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        let displayText = this.formatMessage(text);

        if (corrections && corrections.length > 0 && this.currentMode === 'tutor') {
            corrections.forEach(correction => {
                displayText = displayText.replace(
                    correction.original,
                    `<span class="correction">${correction.original}</span> → <span class="correction-text">${correction.corrected}</span>`
                );
            });
        }

        messageDiv.innerHTML = `<div class="message-bubble">${displayText}</div>`;
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(text) {
        // Split text into lines
        const lines = text.split('\n');
        let result = [];
        let inList = false;
        let listType = null; // 'ol' or 'ul'
        let listItems = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            // Check for numbered list (1. or 1) format)
            const numberedMatch = line.match(/^(\d+)[.\)]\s+(.+)$/);
            // Check for bullet list (* or - format)
            const bulletMatch = line.match(/^[\*\-•]\s+(.+)$/);

            if (numberedMatch) {
                if (!inList || listType !== 'ol') {
                    // Close previous list if different type
                    if (inList && listItems.length > 0) {
                        result.push(`<${listType}>${listItems.join('')}</${listType}>`);
                        listItems = [];
                    }
                    inList = true;
                    listType = 'ol';
                }
                listItems.push(`<li>${numberedMatch[2]}</li>`);
            } else if (bulletMatch) {
                if (!inList || listType !== 'ul') {
                    // Close previous list if different type
                    if (inList && listItems.length > 0) {
                        result.push(`<${listType}>${listItems.join('')}</${listType}>`);
                        listItems = [];
                    }
                    inList = true;
                    listType = 'ul';
                }
                listItems.push(`<li>${bulletMatch[1]}</li>`);
            } else {
                // Not a list item - close any open list
                if (inList && listItems.length > 0) {
                    result.push(`<${listType}>${listItems.join('')}</${listType}>`);
                    listItems = [];
                    inList = false;
                    listType = null;
                }

                // Add non-empty lines as paragraphs or line breaks
                if (line) {
                    result.push(line);
                } else if (result.length > 0) {
                    // Empty line creates a break between paragraphs
                    result.push('<br>');
                }
            }
        }

        // Close any remaining list
        if (inList && listItems.length > 0) {
            result.push(`<${listType}>${listItems.join('')}</${listType}>`);
        }

        return result.join('<br>');
    }

    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        this.chatContainer.appendChild(loadingDiv);
        this.scrollToBottom();
    }

    hideLoading() {
        const loading = document.getElementById('loading-indicator');
        if (loading) loading.remove();
    }

    speak(text) {
        if (this.synthesis) {
            this.synthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);

            if (this.selectedVoice) {
                utterance.voice = this.selectedVoice;
            }

            utterance.lang = 'en-US';
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;

            this.synthesis.speak(utterance);
        }
    }

    speakAndWait(text) {
        return new Promise((resolve) => {
            if (!this.synthesis) {
                resolve();
                return;
            }

            // Stop any ongoing recognition to prevent picking up AI voice
            if (this.recognition && this.isRecording) {
                this.recognition.stop();
                this.isRecording = false;
            }

            this.synthesis.cancel();
            this.isSpeaking = true;

            const utterance = new SpeechSynthesisUtterance(text);

            if (this.selectedVoice) {
                utterance.voice = this.selectedVoice;
            }

            utterance.lang = 'en-US';
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;

            utterance.onend = () => {
                this.isSpeaking = false;
                // Add delay before resolving to let audio fully stop
                setTimeout(() => {
                    resolve();
                }, 500);
            };

            utterance.onerror = () => {
                this.isSpeaking = false;
                setTimeout(() => {
                    resolve();
                }, 300);
            };

            this.synthesis.speak(utterance);
        });
    }

    showFeedback(feedback) {
        const existingFeedback = document.querySelector('.feedback-section-inline');
        if (existingFeedback) existingFeedback.remove();

        if (feedback.tips && feedback.tips.length > 0) {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-section-inline';
            feedbackDiv.innerHTML = `
                <h4>Tips for Improvement</h4>
                <ul>
                    ${feedback.tips.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            `;
            this.chatContainer.appendChild(feedbackDiv);
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
}

// Sidebar Navigation Toggle
class SidebarNav {
    constructor() {
        this.hamburgerBtn = document.getElementById('hamburger-btn');
        this.sidebar = document.getElementById('sidebar');
        this.overlay = document.getElementById('sidebar-overlay');

        if (this.hamburgerBtn && this.sidebar) {
            this.initEventListeners();
        }
    }

    initEventListeners() {
        // Toggle sidebar on hamburger click
        this.hamburgerBtn.addEventListener('click', () => this.toggleSidebar());

        // Close sidebar when clicking overlay
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.closeSidebar());
        }

        // Close sidebar on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.sidebar.classList.contains('open')) {
                this.closeSidebar();
            }
        });
    }

    toggleSidebar() {
        this.hamburgerBtn.classList.toggle('active');
        this.sidebar.classList.toggle('open');
        if (this.overlay) {
            this.overlay.classList.toggle('visible');
        }
    }

    closeSidebar() {
        this.hamburgerBtn.classList.remove('active');
        this.sidebar.classList.remove('open');
        if (this.overlay) {
            this.overlay.classList.remove('visible');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tutor = new EnglishTutor();
    window.sidebarNav = new SidebarNav();
});
