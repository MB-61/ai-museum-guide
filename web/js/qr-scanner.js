// ========================================
// AI Müze Rehberi - QR Scanner Module
// ========================================

let html5QrCode = null;

// Initialize QR Scanner
export async function initQRScanner(onSuccess) {
    const qrReader = document.getElementById('qr-reader');
    if (!qrReader) return;

    try {
        html5QrCode = new Html5Qrcode("qr-reader");

        const config = {
            fps: 10,
            qrbox: { width: 250, height: 250 },
            aspectRatio: window.innerHeight / window.innerWidth,
            showTorchButtonIfSupported: true,
            showZoomSliderIfSupported: false,
            defaultZoomValueIfSupported: 2,
            formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE]
        };

        await html5QrCode.start(
            { facingMode: "environment" },
            config,
            (decodedText) => {
                console.log('QR found:', decodedText);
                if (onSuccess) {
                    stopQRScanner();
                    onSuccess(decodedText);
                }
            },
            (errorMessage) => {
                // QR kod bulunamadı, normal devam
            }
        );
    } catch (err) {
        console.error('QR Scanner error:', err);
        // Fallback: Show test dropdown
    }
}

// Stop QR Scanner
export function stopQRScanner() {
    if (html5QrCode) {
        html5QrCode.stop().catch(err => {
            console.log('QR stop error:', err);
        });
        html5QrCode = null;
    }
}

// Parse QR code content
export function parseQRCode(content) {
    // Expected format: qr_01, qr_02, etc.
    const match = content.match(/qr_(\d+)/i);
    if (match) {
        return `qr_${match[1].padStart(2, '0')}`;
    }
    return null;
}

// Populate test dropdown
export function populateTestDropdown() {
    const select = document.getElementById('qr-test-select');
    if (!select) return;

    for (let i = 1; i <= 31; i++) {
        const num = i.toString().padStart(2, '0');
        const option = document.createElement('option');
        option.value = `qr_${num}`;
        option.textContent = num;
        option.className = 'bg-background-dark';
        select.appendChild(option);
    }
}

// Make functions globally available
window.stopQRScanner = stopQRScanner;
