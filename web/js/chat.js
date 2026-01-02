// ========================================
// AI Müze Rehberi - Chat Module
// ========================================

import { API_BASE } from './config.js';
import { setStatus, showToast, addMessage } from './utils.js';
import { speakWithAvatar, isSpeaking } from './speech.js';

// State
export let conversationHistory = [];
let qrMode = false;
let currentQrId = null;

// Set chat mode
export function setChatMode(isQrMode, qrId = null) {
    qrMode = isQrMode;
    currentQrId = qrId;
}

// Send message
export async function sendMessage() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, true);
    input.value = '';

    // Close chat input panel after sending
    const chatInputPanel = document.getElementById('chat-input-panel');
    if (chatInputPanel) chatInputPanel.style.display = 'none';

    showMessagesPanel();
    setStatus('Düşünüyor...');

    // Lock chat input while thinking
    input.disabled = true;
    input.placeholder = 'AI düşünüyor...';

    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) sendBtn.disabled = true;

    // Disable mic button while thinking
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('from-primary', 'to-blue-500', 'from-red-500', 'to-red-600');
        micBtn.classList.add('from-gray-500', 'to-gray-600');
        micBtn.disabled = true;
    }

    try {
        const payload = {
            question,
            history: conversationHistory
        };
        if (qrMode && currentQrId) {
            payload.qr_id = currentQrId;
        }

        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        addMessage(data.answer, false);

        conversationHistory.push({ role: 'user', content: question });
        conversationHistory.push({ role: 'assistant', content: data.answer });
        if (conversationHistory.length > 10) {
            conversationHistory = conversationHistory.slice(-10);
        }

        await speakWithAvatar(data.answer);

    } catch (err) {
        console.error('Chat error:', err);
        addMessage('Üzgünüm, bir hata oluştu.', false);
        setStatus('Hata');

        // Re-enable controls
        input.disabled = false;
        input.placeholder = 'Mesajınızı yazın...';
        if (sendBtn) sendBtn.disabled = false;
        if (micBtn) {
            micBtn.classList.remove('from-gray-500', 'to-gray-600');
            micBtn.classList.add('from-primary', 'to-blue-500');
            micBtn.disabled = false;
        }
    }
}

// Handle key press
export function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage();
}

// Ask sample question
export function askSample(question) {
    const input = document.getElementById('chat-input');
    if (input) input.value = question;
    sendMessage();

    const sampleQuestions = document.getElementById('sample-questions');
    if (sampleQuestions) sampleQuestions.style.display = 'none';
}

// Show messages panel
function showMessagesPanel() {
    const panel = document.getElementById('messages-panel');
    const messages = document.getElementById('messages');
    if (panel) panel.style.display = 'block';

    if (!window.messagesPanelOpened && messages) {
        messages.style.display = 'none';
        window.messagesPanelOpened = true;
    }
}

// Toggle messages visibility
export function toggleMessages() {
    const panel = document.getElementById('messages');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
}

// Toggle chat input
export function toggleChatInput() {
    const panel = document.getElementById('chat-input-panel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        if (panel.style.display === 'block') {
            const input = document.getElementById('chat-input');
            if (input) input.focus();
        }
    }
}

// Clear conversation history
export function clearHistory() {
    conversationHistory = [];
}

// Make functions globally available
window.sendMessage = sendMessage;
window.handleKeyPress = handleKeyPress;
window.askSample = askSample;
window.toggleMessages = toggleMessages;
window.toggleChatInput = toggleChatInput;
