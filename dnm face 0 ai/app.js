import { TalkingHead } from "talkinghead";

// ========================================
// Global Variables
// ========================================
let head = null;
let faceMesh = null;
let teethMesh = null;
let isSpeaking = false;
let animationInterval = null;
let currentViseme = 'sil';

// DOM Elements
const avatarElement = document.getElementById('avatar');
const loadingElement = document.getElementById('loading');
const loadingText = document.getElementById('loading-text');
const statusElement = document.getElementById('status');

const textInput = document.getElementById('text-input');
const speakBtn = document.getElementById('speak-btn');
const stopBtn = document.getElementById('stop-btn');

const voiceSelect = document.getElementById('voice-select');
const rateSlider = document.getElementById('rate-slider');
const rateValue = document.getElementById('rate-value');
const pitchSlider = document.getElementById('pitch-slider');
const pitchValue = document.getElementById('pitch-value');
const volumeSlider = document.getElementById('volume-slider');
const volumeValue = document.getElementById('volume-value');

const moodButtons = document.querySelectorAll('.mood-btn');
const phraseButtons = document.querySelectorAll('.phrase-btn');
const cameraButtons = document.querySelectorAll('.camera-btn');

// ========================================
// Viseme Names (Oculus format)
// ========================================
const VISEME_NAMES = ['sil', 'PP', 'FF', 'TH', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR', 'aa', 'E', 'I', 'O', 'U'];

// Turkish character to viseme mapping
const CHAR_TO_VISEME = {
    // Vowels
    'a': 'aa', 'e': 'E', 'ı': 'I', 'i': 'I',
    'o': 'O', 'ö': 'O', 'u': 'U', 'ü': 'U',
    // Consonants
    'b': 'PP', 'p': 'PP', 'm': 'PP',
    'f': 'FF', 'v': 'FF',
    'd': 'DD', 't': 'DD', 'n': 'nn', 'l': 'nn',
    's': 'SS', 'z': 'SS', 'c': 'SS',
    'ş': 'CH', 'ç': 'CH', 'j': 'CH',
    'k': 'kk', 'g': 'kk', 'ğ': 'kk',
    'r': 'RR', 'y': 'I', 'h': 'sil',
    // Punctuation
    ' ': 'sil', '.': 'sil', ',': 'sil', '!': 'sil', '?': 'sil', '\n': 'sil'
};

// ========================================
// Initialize TalkingHead
// ========================================
async function initTalkingHead() {
    try {
        loadingText.textContent = "Avatar yükleniyor...";

        head = new TalkingHead(avatarElement, {
            cameraView: "upper",
            cameraRotateEnable: true,
            cameraZoomEnable: true,
            cameraPanEnable: true,
            modelPixelRatio: 1.5,
            lightAmbientIntensity: 2.5,
            lightDirectIntensity: 25
        });

        await head.showAvatar({
            url: './avatar.glb',
            body: 'M',
            avatarMood: 'neutral',
            lipsyncLang: 'en'
        }, (ev) => {
            if (ev.lengthComputable) {
                const percent = Math.min(100, Math.round(ev.loaded / ev.total * 100));
                loadingText.textContent = `Avatar yükleniyor... ${percent}%`;
            }
        });

        loadingElement.classList.add('hidden');
        console.log("✅ Avatar başarıyla yüklendi!");

        // Find face and teeth meshes
        findMeshes();

        loadVoices();

    } catch (error) {
        console.error("❌ Avatar yüklenirken hata:", error);
        loadingText.textContent = `Hata: ${error.message}`;
    }
}

// ========================================
// Find Face and Teeth Meshes
// ========================================
function findMeshes() {
    if (!head || !head.scene) {
        console.error("❌ Scene bulunamadı");
        return;
    }

    head.scene.traverse((child) => {
        if (child.isMesh && child.morphTargetDictionary) {
            if (child.name === 'Wolf3D_Head') {
                faceMesh = child;
                console.log("✅ Yüz mesh'i bulundu:", child.name);
                console.log("   Morph targets:", Object.keys(child.morphTargetDictionary).filter(k => k.includes('viseme')));
            }
            if (child.name === 'Wolf3D_Teeth') {
                teethMesh = child;
                console.log("✅ Diş mesh'i bulundu:", child.name);
            }
        }
    });

    if (!faceMesh) {
        console.warn("⚠️ Wolf3D_Head bulunamadı, alternatif arıyorum...");
        head.scene.traverse((child) => {
            if (child.isMesh && child.morphTargetDictionary && !faceMesh) {
                const hasVisemes = Object.keys(child.morphTargetDictionary).some(k => k.includes('viseme'));
                if (hasVisemes) {
                    faceMesh = child;
                    console.log("✅ Alternatif yüz mesh'i bulundu:", child.name);
                }
            }
        });
    }
}

// ========================================
// Set Viseme on Mesh
// ========================================
function setViseme(visemeName, intensity = 0.8) {
    if (!faceMesh) return;

    const dict = faceMesh.morphTargetDictionary;
    const influences = faceMesh.morphTargetInfluences;

    // Reset all visemes first
    VISEME_NAMES.forEach(name => {
        const key = `viseme_${name}`;
        if (dict[key] !== undefined) {
            influences[dict[key]] = 0;
        }
    });

    // Set target viseme
    const targetKey = `viseme_${visemeName}`;
    if (dict[targetKey] !== undefined) {
        influences[dict[targetKey]] = intensity;
    }

    // Also apply to teeth if exists
    if (teethMesh && teethMesh.morphTargetDictionary && teethMesh.morphTargetInfluences) {
        const teethDict = teethMesh.morphTargetDictionary;
        const teethInf = teethMesh.morphTargetInfluences;

        VISEME_NAMES.forEach(name => {
            const key = `viseme_${name}`;
            if (teethDict[key] !== undefined) {
                teethInf[teethDict[key]] = 0;
            }
        });

        if (teethDict[targetKey] !== undefined) {
            teethInf[teethDict[targetKey]] = intensity;
        }
    }

    currentViseme = visemeName;
}

// ========================================
// Smooth Viseme Transition
// ========================================
let smoothInterval = null;
let targetIntensity = 0;
let currentIntensity = 0;

function smoothSetViseme(visemeName, intensity = 0.8, duration = 50) {
    setViseme(visemeName, intensity);
}

// ========================================
// Load Voices
// ========================================
function loadVoices() {
    const synth = window.speechSynthesis;

    function populateVoices() {
        const voices = synth.getVoices();
        voiceSelect.innerHTML = '';

        const turkishVoices = voices.filter(v => v.lang.startsWith('tr'));
        const englishVoices = voices.filter(v => v.lang.startsWith('en')).slice(0, 5);

        if (turkishVoices.length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = '🇹🇷 Türkçe';
            turkishVoices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.name;
                option.textContent = voice.name;
                optgroup.appendChild(option);
            });
            voiceSelect.appendChild(optgroup);
        }

        if (englishVoices.length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = '🇬🇧 English';
            englishVoices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.name;
                option.textContent = voice.name;
                optgroup.appendChild(option);
            });
            voiceSelect.appendChild(optgroup);
        }

        console.log(`✅ ${voices.length} ses yüklendi (${turkishVoices.length} Türkçe)`);
    }

    if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = populateVoices;
    }
    populateVoices();
}

// ========================================
// Speak with Lip Sync
// ========================================
async function speak(text) {
    if (!head || isSpeaking) return;
    if (!faceMesh) {
        findMeshes();
        if (!faceMesh) {
            console.error("❌ Yüz mesh'i bulunamadı!");
            return;
        }
    }

    const synth = window.speechSynthesis;
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    // Set voice
    const voices = synth.getVoices();
    const selectedVoice = voices.find(v => v.name === voiceSelect.value);
    if (selectedVoice) {
        utterance.voice = selectedVoice;
        utterance.lang = selectedVoice.lang;
    } else {
        utterance.lang = 'tr-TR';
    }

    utterance.rate = parseFloat(rateSlider.value);
    utterance.pitch = parseFloat(pitchSlider.value);
    utterance.volume = parseFloat(volumeSlider.value);

    // Prepare characters for lip sync
    const chars = text.toLowerCase().split('');
    let charIndex = 0;
    const charDuration = 70 / utterance.rate; // milliseconds per character

    isSpeaking = true;
    speakBtn.disabled = true;
    stopBtn.disabled = false;

    utterance.onstart = () => {
        console.log("🎤 Konuşma başladı - Lip sync aktif");

        animationInterval = setInterval(() => {
            if (!isSpeaking) return;

            if (charIndex < chars.length) {
                const char = chars[charIndex];
                const viseme = CHAR_TO_VISEME[char] || 'sil';

                // Random intensity for more natural look
                const intensity = viseme === 'sil' ? 0.1 : 0.6 + Math.random() * 0.3;
                setViseme(viseme, intensity);

                // Log which character and viseme is being used
                console.log(`👄 Harf: "${char}" → Viseme: ${viseme} (yoğunluk: ${intensity.toFixed(2)})`);

                charIndex++;
            } else {
                // End of text, close mouth
                setViseme('sil', 0);
            }
        }, charDuration);
    };

    utterance.onend = () => {
        console.log("🎤 Konuşma bitti");
        finishSpeaking();
    };

    utterance.onerror = (event) => {
        console.error("❌ Konuşma hatası:", event.error);
        finishSpeaking();
    };

    synth.speak(utterance);
}

// ========================================
// Finish Speaking
// ========================================
function finishSpeaking() {
    isSpeaking = false;

    if (animationInterval) {
        clearInterval(animationInterval);
        animationInterval = null;
    }

    // Close mouth smoothly
    setViseme('sil', 0);

    speakBtn.disabled = false;
    stopBtn.disabled = true;
}

// ========================================
// Stop Speaking
// ========================================
function stopSpeaking() {
    window.speechSynthesis.cancel();
    finishSpeaking();
}

// ========================================
// Set Mood
// ========================================
function setMood(mood) {
    if (head && head.setMood) {
        head.setMood(mood);
        console.log(`😊 Ruh hali: ${mood}`);
    }

    moodButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mood === mood);
    });
}

// ========================================
// Set Camera View
// ========================================
function setCameraView(view) {
    if (head && head.setView) {
        head.setView(view);
        console.log(`📷 Kamera: ${view}`);
    }

    cameraButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
}

// ========================================
// Event Listeners
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    if (!('speechSynthesis' in window)) {
        statusElement.textContent = "❌ Web Speech API desteklenmiyor!";
        statusElement.classList.remove('connected');
        statusElement.classList.add('error');
        speakBtn.disabled = true;
        return;
    }

    initTalkingHead();

    speakBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (text) speak(text);
    });

    stopBtn.addEventListener('click', stopSpeaking);

    rateSlider.addEventListener('input', (e) => rateValue.textContent = e.target.value);
    pitchSlider.addEventListener('input', (e) => pitchValue.textContent = e.target.value);
    volumeSlider.addEventListener('input', (e) => volumeValue.textContent = e.target.value);

    moodButtons.forEach(btn => btn.addEventListener('click', () => setMood(btn.dataset.mood)));
    phraseButtons.forEach(btn => btn.addEventListener('click', () => {
        textInput.value = btn.dataset.text;
        speak(btn.dataset.text);
    }));
    cameraButtons.forEach(btn => btn.addEventListener('click', () => setCameraView(btn.dataset.view)));

    document.querySelector('.mood-btn[data-mood="neutral"]').classList.add('active');

    document.addEventListener("visibilitychange", () => {
        if (head) {
            document.visibilityState === "visible" ? head.start() : head.stop();
        }
    });

    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const text = textInput.value.trim();
            if (text && !isSpeaking) speak(text);
        }
    });
});

// Debug exports
window.talkingHead = {
    head: () => head,
    faceMesh: () => faceMesh,
    speak,
    setMood,
    stopSpeaking,
    setViseme,
    testMouth: () => {
        // Test function - open mouth
        setViseme('aa', 1.0);
        setTimeout(() => setViseme('sil', 0), 1000);
    }
};
