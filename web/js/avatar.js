// ========================================
// AI Müze Rehberi - Avatar Module
// ========================================

import { TalkingHead } from "talkinghead";
import { setStatus, showToast } from './utils.js';
import { getRandomGreeting } from './config.js';
import { speakWithAvatar } from './speech.js';

// State
export let head = null;
export let isAvatarReady = false;
export let morphMeshes = [];

// Viseme configuration for lip sync
export const visemeConfig = {
    0: { name: "sil", intensity: 0 },
    1: { name: "aa", intensity: 0.8 },
    2: { name: "aa", intensity: 0.7 },
    3: { name: "O", intensity: 0.7 },
    4: { name: "E", intensity: 0.6 },
    5: { name: "I", intensity: 0.5 },
    6: { name: "I", intensity: 0.5 },
    7: { name: "U", intensity: 0.7 },
    8: { name: "O", intensity: 0.6 },
    9: { name: "aa", intensity: 0.7 },
    10: { name: "O", intensity: 0.6 },
    11: { name: "I", intensity: 0.5 },
    12: { name: "kk", intensity: 0.4 },
    13: { name: "RR", intensity: 0.5 },
    14: { name: "nn", intensity: 0.4 },
    15: { name: "SS", intensity: 0.5 },
    16: { name: "CH", intensity: 0.6 },
    17: { name: "TH", intensity: 0.5 },
    18: { name: "FF", intensity: 0.6 },
    19: { name: "DD", intensity: 0.5 },
    20: { name: "kk", intensity: 0.4 },
    21: { name: "PP", intensity: 0.8 }
};

export const visemeNames = ['sil', 'aa', 'E', 'I', 'O', 'U', 'PP', 'FF', 'TH', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR'];
export let currentVisemeValues = {};
visemeNames.forEach(v => currentVisemeValues[v] = 0);

// Initialize Avatar
export async function initAvatar(qrMode = false, exhibitTitle = '') {
    setStatus('Avatar yükleniyor...');

    try {
        const nodeAvatar = document.getElementById('avatar-container');
        head = new TalkingHead(nodeAvatar, {
            ttsEndpoint: null,
            lipsyncModules: ["en"],
            cameraView: "full",
            cameraRotateEnable: false
        });

        await head.showAvatar({
            url: '/static/avatar.glb',
            body: 'M',
            avatarMood: 'neutral',
            lipsyncLang: 'en'
        }, (ev) => {
            if (ev.lengthComputable) {
                const pct = Math.round((ev.loaded / ev.total) * 100);
                setStatus(`Yükleniyor: ${pct}%`);
            }
        });

        // Get morph meshes for lip sync
        morphMeshes = [];
        if (head?.scene) {
            head.scene.traverse(node => {
                if (node.isMesh && node.morphTargetDictionary && node.morphTargetInfluences) {
                    const visemeKeys = Object.keys(node.morphTargetDictionary).filter(k => k.startsWith('viseme_'));
                    if (visemeKeys.length > 0) {
                        console.log('Found viseme mesh:', node.name, visemeKeys);
                        morphMeshes.push({
                            mesh: node,
                            dict: node.morphTargetDictionary,
                            influences: node.morphTargetInfluences
                        });
                    }
                }
            });
        }

        console.log('Total morph meshes found:', morphMeshes.length);

        isAvatarReady = true;
        setStatus('Hazır');
        showToast('Avatar hazır', 'success');

        // Speak random greeting
        const greeting = getRandomGreeting(qrMode, exhibitTitle);
        addSystemMessage(greeting);
        setTimeout(() => speakWithAvatar(greeting), 500);

    } catch (err) {
        console.error('Avatar load error:', err);
        setStatus('Avatar yüklenemedi');
        showToast('Avatar yüklenemedi', 'error');
    }
}

// Add system message helper
function addSystemMessage(text) {
    const messages = document.getElementById('messages');
    if (messages) {
        const msg = document.createElement('div');
        msg.className = 'message system';
        msg.textContent = text;
        messages.appendChild(msg);
    }

    const panel = document.getElementById('messages-panel');
    if (panel) panel.style.display = 'block';
}

// Configure avatar position based on mode
export function configureAvatarLayout(hasExhibitImage, qrMode) {
    const avatarContainer = document.getElementById('avatar-container');
    const exhibitFrame = document.getElementById('exhibit-frame');
    const modeIndicator = document.getElementById('mode-indicator');
    const exhibitBadge = document.getElementById('exhibit-badge');

    if (!avatarContainer) return;

    if (qrMode) {
        if (hasExhibitImage) {
            if (exhibitFrame) exhibitFrame.style.display = 'block';
            avatarContainer.style.left = '0';
            avatarContainer.style.right = 'auto';
            avatarContainer.style.width = '70%';
            avatarContainer.style.height = '100%';
            avatarContainer.style.transform = 'translateX(-18%) translateY(55%) scale(1.8)';
        } else {
            if (exhibitFrame) exhibitFrame.style.display = 'none';
            avatarContainer.style.left = '50%';
            avatarContainer.style.right = 'auto';
            avatarContainer.style.width = '70%';
            avatarContainer.style.height = '100%';
            avatarContainer.style.transform = 'translateX(-50%) translateY(45%) scale(1.8)';
        }
        if (modeIndicator) modeIndicator.textContent = 'Eser Modu';
        if (exhibitBadge) exhibitBadge.style.display = 'flex';
    } else {
        if (modeIndicator) modeIndicator.textContent = 'Genel Mod';
        if (exhibitBadge) exhibitBadge.style.display = 'none';
        if (exhibitFrame) exhibitFrame.style.display = 'none';
        avatarContainer.style.left = '50%';
        avatarContainer.style.right = 'auto';
        avatarContainer.style.width = '70%';
        avatarContainer.style.height = '100%';
        avatarContainer.style.transform = 'translateX(-50%) translateY(45%) scale(1.8)';
    }
}

// Viseme functions for lip sync
export function setVisemeSmooth(targetViseme, targetIntensity, lerpSpeed = 0.35) {
    visemeNames.forEach(v => {
        const target = (v === targetViseme) ? targetIntensity : 0;
        currentVisemeValues[v] += (target - currentVisemeValues[v]) * lerpSpeed;

        const fullName = 'viseme_' + v;
        morphMeshes.forEach(m => {
            const idx = m.dict[fullName];
            if (idx !== undefined) {
                m.influences[idx] = Math.max(0, currentVisemeValues[v]);
            }
        });
    });
}

export function resetVisemes() {
    visemeNames.forEach(v => currentVisemeValues[v] = 0);
    morphMeshes.forEach(m => {
        Object.keys(m.dict).forEach(key => {
            if (key.startsWith('viseme_')) {
                m.influences[m.dict[key]] = 0;
            }
        });
    });
}
