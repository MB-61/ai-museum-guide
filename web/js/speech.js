// ========================================
// AI Müze Rehberi - Speech Module
// ========================================

import { setStatus, showToast } from './utils.js';
import { AZURE_KEY, AZURE_REGION } from './config.js';
import { visemeConfig, setVisemeSmooth, resetVisemes } from './avatar.js';

// State
let audioContext = null;
let currentAudioSource = null;
export let isSpeaking = false;
let lipSyncAnimationId = null;

// Initialize audio context
async function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') await audioContext.resume();
    return audioContext;
}

// Convert PCM data to AudioBuffer
function pcmToAudioBuffer(pcmData, sampleRate) {
    const audioBuffer = audioContext.createBuffer(1, pcmData.length, sampleRate);
    const channelData = audioBuffer.getChannelData(0);
    for (let i = 0; i < pcmData.length; i++) {
        channelData[i] = pcmData[i] / 32768.0;
    }
    return audioBuffer;
}

// Play audio buffer
function playAudioBuffer(audioBuffer) {
    return new Promise(resolve => {
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.onended = () => {
            currentAudioSource = null;
            resolve();
        };
        currentAudioSource = source;
        source.start();
    });
}

// Animate lip sync with viseme data
async function animateLipSync(visemeData, totalDuration) {
    if (visemeData.length === 0) return;

    const startTime = performance.now();
    let currentIdx = 0;

    return new Promise(resolve => {
        function update() {
            if (!isSpeaking) {
                resetVisemes();
                resolve();
                return;
            }

            const elapsed = performance.now() - startTime;

            while (currentIdx < visemeData.length - 1 && visemeData[currentIdx + 1].time <= elapsed) {
                currentIdx++;
            }

            const current = visemeData[currentIdx];
            const config = visemeConfig[current.id] || { name: "sil", intensity: 0 };
            setVisemeSmooth(config.name, config.intensity);

            if (elapsed < totalDuration * 1000 && isSpeaking) {
                lipSyncAnimationId = requestAnimationFrame(update);
            } else {
                let fadeStep = 0;
                function fadeOut() {
                    fadeStep++;
                    setVisemeSmooth("sil", 0, 0.2);
                    if (fadeStep < 10) {
                        requestAnimationFrame(fadeOut);
                    } else {
                        resetVisemes();
                        lipSyncAnimationId = null;
                        resolve();
                    }
                }
                fadeOut();
            }
        }
        lipSyncAnimationId = requestAnimationFrame(update);
    });
}

// Stop speech
export function stopSpeech() {
    if (currentAudioSource) {
        try {
            currentAudioSource.stop();
        } catch (e) { }
        currentAudioSource = null;
    }
    if (lipSyncAnimationId) {
        cancelAnimationFrame(lipSyncAnimationId);
        lipSyncAnimationId = null;
    }
    isSpeaking = false;
    resetVisemes();
    setStatus('Durduruldu');

    document.getElementById('stop-btn').style.display = 'none';
    document.getElementById('stop-placeholder').style.display = 'block';

    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('from-gray-500', 'to-gray-600', 'from-red-500', 'to-red-600');
        micBtn.classList.add('from-primary', 'to-blue-500');
        micBtn.disabled = false;
    }

    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    if (chatInput) {
        chatInput.disabled = false;
        chatInput.placeholder = 'Mesajınızı yazın...';
    }
    if (sendBtn) sendBtn.disabled = false;

    showToast('Konuşma durduruldu', 'info');
}

// Main speak function with Azure TTS
export async function speakWithAvatar(text) {
    if (!AZURE_KEY || AZURE_KEY === 'YOUR_AZURE_SPEECH_KEY_HERE') {
        showToast('Azure API anahtarı gerekli', 'error');
        setStatus('API anahtarı eksik');
        return;
    }

    setStatus('Konuşuyor...');
    isSpeaking = true;

    document.getElementById('stop-btn').style.display = 'flex';
    document.getElementById('stop-placeholder').style.display = 'none';

    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('from-primary', 'to-blue-500', 'from-red-500', 'to-red-600');
        micBtn.classList.add('from-gray-500', 'to-gray-600');
    }

    document.getElementById('mic-pulse-1')?.classList.add('opacity-0');
    document.getElementById('mic-pulse-2')?.classList.add('opacity-0');

    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    if (chatInput) {
        chatInput.disabled = true;
        chatInput.placeholder = 'AI konuşuyor...';
    }
    if (sendBtn) sendBtn.disabled = true;

    await initAudioContext();

    const voiceName = 'tr-TR-AhmetNeural';
    const ssml = `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="tr-TR">
        <voice name="${voiceName}">
            <mstts:viseme type="redlips_front"/>
            ${text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}
        </voice>
    </speak>`;

    const config = SpeechSDK.SpeechConfig.fromSubscription(AZURE_KEY, AZURE_REGION);
    config.speechSynthesisOutputFormat = SpeechSDK.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm;

    const synth = new SpeechSDK.SpeechSynthesizer(config, null);
    const visemeData = [];

    synth.visemeReceived = (s, e) => {
        visemeData.push({ id: e.visemeId, time: e.audioOffset / 10000 });
    };

    return new Promise((resolve, reject) => {
        synth.speakSsmlAsync(ssml,
            async result => {
                if (result.reason === SpeechSDK.ResultReason.SynthesizingAudioCompleted) {
                    const pcmData = new Int16Array(result.audioData);
                    const audioBuffer = pcmToAudioBuffer(pcmData, 24000);

                    await Promise.all([
                        playAudioBuffer(audioBuffer),
                        animateLipSync(visemeData, audioBuffer.duration)
                    ]);

                    isSpeaking = false;
                    document.getElementById('stop-btn').style.display = 'none';
                    document.getElementById('stop-placeholder').style.display = 'block';
                    setStatus('Hazır');

                    if (micBtn) {
                        micBtn.classList.remove('from-gray-500', 'to-gray-600', 'from-red-500', 'to-red-600');
                        micBtn.classList.add('from-primary', 'to-blue-500');
                        micBtn.disabled = false;
                    }

                    if (chatInput) {
                        chatInput.disabled = false;
                        chatInput.placeholder = 'Mesajınızı yazın...';
                    }
                    if (sendBtn) sendBtn.disabled = false;

                    resolve();
                } else {
                    isSpeaking = false;
                    document.getElementById('stop-btn').style.display = 'none';
                    setStatus('TTS hatası');
                    reject(result.errorDetails);
                }
                synth.close();
            },
            error => {
                isSpeaking = false;
                document.getElementById('stop-btn').style.display = 'none';
                setStatus('Bağlantı hatası');
                synth.close();
                reject(error);
            }
        );
    });
}

// Speech Recognition
let recognition = null;
let isListening = false;
let silenceTimer = null;
const SILENCE_TIMEOUT = 7000;

export function initSpeechRecognition(onResult) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) micBtn.style.display = 'none';
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'tr-TR';

    let finalTranscript = '';

    recognition.onresult = (event) => {
        if (silenceTimer) {
            clearTimeout(silenceTimer);
            silenceTimer = null;
        }

        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
                finalTranscript += result[0].transcript;
            } else {
                interimTranscript += result[0].transcript;
            }
        }

        setStatus(interimTranscript || finalTranscript || 'Dinliyor...');

        if (finalTranscript) {
            silenceTimer = setTimeout(() => {
                if (finalTranscript.trim() && onResult) {
                    onResult(finalTranscript.trim());
                    finalTranscript = '';
                }
                stopListening();
            }, 1500);
        }
    };

    recognition.onend = () => {
        if (isListening) {
            if (finalTranscript.trim() && onResult) {
                onResult(finalTranscript.trim());
            }
        }
        stopListening();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopListening();
        if (event.error !== 'no-speech') {
            showToast('Ses tanıma hatası', 'error');
        }
    };
}

export function startListening() {
    if (!recognition || isListening || isSpeaking) return;

    isListening = true;
    setStatus('Dinliyor...');

    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('from-primary', 'to-blue-500', 'from-gray-500', 'to-gray-600');
        micBtn.classList.add('from-red-500', 'to-red-600');
    }

    document.getElementById('mic-pulse-1')?.classList.remove('opacity-0');
    document.getElementById('mic-pulse-2')?.classList.remove('opacity-0');

    try {
        recognition.start();
    } catch (e) {
        console.log('Recognition already started');
    }
}

export function stopListening() {
    if (!recognition) return;

    isListening = false;

    if (silenceTimer) {
        clearTimeout(silenceTimer);
        silenceTimer = null;
    }

    try {
        recognition.stop();
    } catch (e) { }

    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('from-red-500', 'to-red-600', 'from-gray-500', 'to-gray-600');
        micBtn.classList.add('from-primary', 'to-blue-500');
    }

    document.getElementById('mic-pulse-1')?.classList.add('opacity-0');
    document.getElementById('mic-pulse-2')?.classList.add('opacity-0');

    if (!isSpeaking) {
        setStatus('Hazır');
    }
}

// Make functions globally available
window.stopSpeech = stopSpeech;
