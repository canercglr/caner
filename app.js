// DOM Elements
const imageInput = document.getElementById('imageInput');
const fileName = document.getElementById('fileName');
const pixelSizeSlider = document.getElementById('pixelSize');
const pixelSizeValue = document.getElementById('pixelSizeValue');
const speedSlider = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');
const fpsSlider = document.getElementById('fps');
const fpsValue = document.getElementById('fpsValue');
const bgColorInput = document.getElementById('bgColor');
const mainCanvas = document.getElementById('mainCanvas');
const placeholder = document.getElementById('placeholder');
const previewBtn = document.getElementById('previewBtn');
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const progressContainer = document.getElementById('progress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const downloadSection = document.getElementById('downloadSection');
const videoPreview = document.getElementById('videoPreview');
const downloadBtn = document.getElementById('downloadBtn');

const ctx = mainCanvas.getContext('2d');

// State
let originalImage = null;
let imageData = null;
let pixelIndices = [];
let isAnimating = false;
let isRecording = false;
let mediaRecorder = null;
let recordedChunks = [];
let animationFrameId = null;

// Fisher-Yates shuffle algorithm
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

// Update slider display values
pixelSizeSlider.addEventListener('input', () => {
    pixelSizeValue.textContent = `${pixelSizeSlider.value}px`;
});

speedSlider.addEventListener('input', () => {
    speedValue.textContent = speedSlider.value;
});

fpsSlider.addEventListener('input', () => {
    fpsValue.textContent = fpsSlider.value;
});

// Handle image upload
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    fileName.textContent = file.name;

    const reader = new FileReader();
    reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
            originalImage = img;

            // Set canvas size to image size
            mainCanvas.width = img.width;
            mainCanvas.height = img.height;

            // Draw original image to get pixel data
            ctx.drawImage(img, 0, 0);
            imageData = ctx.getImageData(0, 0, img.width, img.height);

            // Show canvas, hide placeholder
            mainCanvas.style.display = 'block';
            placeholder.style.display = 'none';

            // Clear and show background
            ctx.fillStyle = bgColorInput.value;
            ctx.fillRect(0, 0, mainCanvas.width, mainCanvas.height);

            // Enable buttons
            previewBtn.disabled = false;
            recordBtn.disabled = false;

            // Hide download section
            downloadSection.hidden = true;
        };
        img.src = event.target.result;
    };
    reader.readAsDataURL(file);
});

// Generate pixel indices based on pixel size
function generatePixelIndices() {
    const pixelSize = parseInt(pixelSizeSlider.value);
    const width = mainCanvas.width;
    const height = mainCanvas.height;

    const indices = [];

    for (let y = 0; y < height; y += pixelSize) {
        for (let x = 0; x < width; x += pixelSize) {
            indices.push({ x, y });
        }
    }

    return shuffleArray(indices);
}

// Draw a block of pixels at given position
function drawPixelBlock(x, y, pixelSize) {
    const width = mainCanvas.width;
    const height = mainCanvas.height;

    for (let dy = 0; dy < pixelSize && y + dy < height; dy++) {
        for (let dx = 0; dx < pixelSize && x + dx < width; dx++) {
            const px = x + dx;
            const py = y + dy;
            const idx = (py * width + px) * 4;

            const r = imageData.data[idx];
            const g = imageData.data[idx + 1];
            const b = imageData.data[idx + 2];
            const a = imageData.data[idx + 3];

            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a / 255})`;
            ctx.fillRect(px, py, 1, 1);
        }
    }
}

// Animation function
function animate(recording = false) {
    return new Promise((resolve) => {
        const pixelSize = parseInt(pixelSizeSlider.value);
        const pixelsPerFrame = parseInt(speedSlider.value);
        const fps = parseInt(fpsSlider.value);
        const frameInterval = 1000 / fps;

        pixelIndices = generatePixelIndices();
        const totalPixels = pixelIndices.length;
        let currentIndex = 0;

        // Clear canvas with background color
        ctx.fillStyle = bgColorInput.value;
        ctx.fillRect(0, 0, mainCanvas.width, mainCanvas.height);

        isAnimating = true;
        stopBtn.disabled = false;
        previewBtn.disabled = true;
        recordBtn.disabled = true;

        let lastFrameTime = 0;

        function frame(timestamp) {
            if (!isAnimating) {
                resolve(false);
                return;
            }

            if (timestamp - lastFrameTime >= frameInterval) {
                lastFrameTime = timestamp;

                // Draw pixels for this frame
                const endIndex = Math.min(currentIndex + pixelsPerFrame, totalPixels);

                for (let i = currentIndex; i < endIndex; i++) {
                    const { x, y } = pixelIndices[i];
                    drawPixelBlock(x, y, pixelSize);
                }

                currentIndex = endIndex;

                // Update progress
                const progress = Math.floor((currentIndex / totalPixels) * 100);
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${progress}%`;

                // Check if animation is complete
                if (currentIndex >= totalPixels) {
                    isAnimating = false;
                    stopBtn.disabled = true;
                    previewBtn.disabled = false;
                    recordBtn.disabled = false;
                    resolve(true);
                    return;
                }
            }

            animationFrameId = requestAnimationFrame(frame);
        }

        progressContainer.hidden = false;
        animationFrameId = requestAnimationFrame(frame);
    });
}

// Preview button handler
previewBtn.addEventListener('click', async () => {
    if (!originalImage) return;
    downloadSection.hidden = true;
    await animate(false);
});

// Stop button handler
stopBtn.addEventListener('click', () => {
    isAnimating = false;
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }
    if (isRecording && mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    stopBtn.disabled = true;
    previewBtn.disabled = false;
    recordBtn.disabled = false;
});

// Record button handler
recordBtn.addEventListener('click', async () => {
    if (!originalImage) return;

    downloadSection.hidden = true;
    recordedChunks = [];
    isRecording = true;

    // Set up MediaRecorder
    const stream = mainCanvas.captureStream(parseInt(fpsSlider.value));

    // Try different codecs
    const mimeTypes = [
        'video/webm;codecs=vp9',
        'video/webm;codecs=vp8',
        'video/webm',
        'video/mp4'
    ];

    let selectedMimeType = '';
    for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
            selectedMimeType = mimeType;
            break;
        }
    }

    if (!selectedMimeType) {
        alert('Bu tarayıcı video kaydetmeyi desteklemiyor!');
        isRecording = false;
        return;
    }

    mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedMimeType,
        videoBitsPerSecond: 5000000
    });

    mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
            recordedChunks.push(e.data);
        }
    };

    mediaRecorder.onstop = () => {
        isRecording = false;

        if (recordedChunks.length > 0) {
            const blob = new Blob(recordedChunks, { type: selectedMimeType });
            const url = URL.createObjectURL(blob);

            videoPreview.src = url;
            downloadBtn.href = url;

            // Set appropriate file extension
            const extension = selectedMimeType.includes('mp4') ? 'mp4' : 'webm';
            downloadBtn.download = `pixel-reveal.${extension}`;

            downloadSection.hidden = false;
        }
    };

    mediaRecorder.start(100); // Collect data every 100ms

    const completed = await animate(true);

    // Give a small delay for the final frame to be recorded
    if (completed) {
        setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
        }, 500);
    }
});

// Update background color preview
bgColorInput.addEventListener('input', () => {
    if (originalImage && !isAnimating) {
        ctx.fillStyle = bgColorInput.value;
        ctx.fillRect(0, 0, mainCanvas.width, mainCanvas.height);
    }
});
