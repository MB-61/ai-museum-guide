// ========================================
// AI Müze Rehberi - Configuration
// ========================================

export const API_BASE = window.location.origin + '/api/v1';
export let AZURE_KEY = '';
export let AZURE_REGION = 'westeurope';

// QR Mappings for test dropdown
export const QR_EXHIBITS = {
    "qr_01": "Türk Maarif Cemiyeti Tüzüğü",
    "qr_02": "Atatürk Fotoğrafı",
    "qr_03": "Kuruluş Diploması",
    "qr_04": "Bando Kıyafeti",
    "qr_05": "Spor Kupası",
    "qr_06": "İlk Zil",
    "qr_07": "Mimari Maket",
    "qr_08": "Eğitim Sırası",
    "qr_09": "Nota Defteri",
    "qr_10": "Daktilo Makinesi"
};

// Greeting phrases loaded from files
export let QR_GREETINGS = [];
export let GENERAL_GREETINGS = [];

// Load Azure config from server
export async function loadAzureConfig() {
    try {
        const response = await fetch(`${API_BASE}/voice/azure-config`);
        if (response.ok) {
            const config = await response.json();
            AZURE_KEY = config.key || '';
            AZURE_REGION = config.region || 'westeurope';
        }
    } catch (err) {
        console.warn('Could not load Azure config:', err);
    }
}

// Load greetings from txt files
export async function loadGreetings() {
    try {
        const qrResponse = await fetch('/static/data/qrli_greeting.txt');
        if (qrResponse.ok) {
            const text = await qrResponse.text();
            QR_GREETINGS = text.split('\n').filter(line => line.trim());
        }
    } catch (e) {
        console.warn('Could not load QR greetings:', e);
    }

    try {
        const genResponse = await fetch('/static/data/qrsiz_greeting.txt');
        if (genResponse.ok) {
            const text = await genResponse.text();
            GENERAL_GREETINGS = text.split('\n').filter(line => line.trim());
        }
    } catch (e) {
        console.warn('Could not load general greetings:', e);
    }

    // Fallback if files not loaded
    if (QR_GREETINGS.length === 0) {
        QR_GREETINGS = ["Merhaba! {exhibit} hakkında bilgi almak için hazırım."];
    }
    if (GENERAL_GREETINGS.length === 0) {
        GENERAL_GREETINGS = ["Merhaba! Size nasıl yardımcı olabilirim?"];
    }
}

// Get random greeting
export function getRandomGreeting(isQrMode, exhibitTitle = '') {
    if (isQrMode && exhibitTitle && QR_GREETINGS.length > 0) {
        const greeting = QR_GREETINGS[Math.floor(Math.random() * QR_GREETINGS.length)];
        return greeting.replace('{exhibit}', exhibitTitle);
    } else if (GENERAL_GREETINGS.length > 0) {
        return GENERAL_GREETINGS[Math.floor(Math.random() * GENERAL_GREETINGS.length)];
    }
    return "Merhaba! Size nasıl yardımcı olabilirim?";
}

// Update Azure config (called from other modules)
export function setAzureConfig(key, region) {
    AZURE_KEY = key;
    AZURE_REGION = region;
}
