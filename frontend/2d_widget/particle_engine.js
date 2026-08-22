const canvas = document.getElementById('particleCanvas');
const ctx = canvas.getContext('2d');

// ==================== AURORA CANVAS ====================
const auroraCanvas = document.getElementById('auroraCanvas');
const auroraCtx = auroraCanvas.getContext('2d');

// ==================== WAVEFORM CANVAS ====================
const waveformCanvas = document.getElementById('waveformCanvas');
const waveformCtx = waveformCanvas.getContext('2d');

// ==================== CONFIG ====================
const NUM_PARTICLES = 1800;
const SPHERE_RADIUS = 120;
const PERSPECTIVE = 800;
const ROTATION_SPEED_Y = 0.003;
const ROTATION_SPEED_X = 0.001;

let width, height, centerX, centerY;
let currentUiState = 'idle';
let rotationY = 0;
let rotationX = 0;
let time = 0;

// Physics targets - smoothly interpolated
let targetRadius = SPHERE_RADIUS;
let currentRadius = SPHERE_RADIUS;

// ==================== AURORA STATE ====================
let auroraHue = 220;
let auroraTargetHue = 220;
let auroraSaturation = 80;
let auroraIntensity = 0.06;
let auroraTargetIntensity = 0.06;

// ==================== MOUSE INTERACTION ====================
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;
let dragVelocityY = 0;
let dragVelocityX = 0;
let manualRotationY = 0;
let manualRotationX = 0;

// ==================== WAVEFORM STATE ====================
let waveAmplitude = 0;
let waveTargetAmplitude = 0;
let wavePhase = 0;

function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    centerX = width / 2;
    centerY = height / 2;

    // Aurora canvas
    auroraCanvas.width = width;
    auroraCanvas.height = height;

    // Waveform canvas
    waveformCanvas.width = width;
    waveformCanvas.height = 80;
}
window.addEventListener('resize', resize);
resize();

// ==================== PARTICLE ====================
class Particle {
    constructor(index, total) {
        // Fibonacci sphere distribution for perfect uniformity
        const golden = Math.PI * (3 - Math.sqrt(5));
        const y = 1 - (index / (total - 1)) * 2;
        const radiusAtY = Math.sqrt(1 - y * y);
        const theta = golden * index;

        // Unit sphere coordinates (home position)
        this.homeX = Math.cos(theta) * radiusAtY;
        this.homeY = y;
        this.homeZ = Math.sin(theta) * radiusAtY;

        // Current position (starts at home)
        this.x = this.homeX * SPHERE_RADIUS;
        this.y = this.homeY * SPHERE_RADIUS;
        this.z = this.homeZ * SPHERE_RADIUS;

        // Velocity
        this.vx = 0;
        this.vy = 0;
        this.vz = 0;

        // Unique offset for staggered animations
        this.offset = Math.random() * Math.PI * 2;
        this.size = 1.2 + Math.random() * 0.8;
    }

    update() {
        // Calculate target position on sphere surface at current radius
        let tx = this.homeX * currentRadius;
        let ty = this.homeY * currentRadius;
        let tz = this.homeZ * currentRadius;

        // Spring force (Hooke's Law) - pulls particle toward target
        const spring = 0.04;
        const damping = 0.88;

        let ax = (tx - this.x) * spring;
        let ay = (ty - this.y) * spring;
        let az = (tz - this.z) * spring;

        this.vx = (this.vx + ax) * damping;
        this.vy = (this.vy + ay) * damping;
        this.vz = (this.vz + az) * damping;

        this.x += this.vx;
        this.y += this.vy;
        this.z += this.vz;
    }

    project() {
        // Apply combined rotation (auto + manual + drag)
        let totalRotY = rotationY + manualRotationY;
        let totalRotX = rotationX + manualRotationX;

        // Apply Y rotation
        let cosY = Math.cos(totalRotY);
        let sinY = Math.sin(totalRotY);
        let x1 = this.x * cosY - this.z * sinY;
        let z1 = this.x * sinY + this.z * cosY;

        // Apply X rotation
        let cosX = Math.cos(totalRotX);
        let sinX = Math.sin(totalRotX);
        let y1 = this.y * cosX - z1 * sinX;
        let z2 = this.y * sinX + z1 * cosX;

        // Perspective projection
        let scale = PERSPECTIVE / (PERSPECTIVE + z2);
        let px = centerX + x1 * scale;
        let py = centerY + y1 * scale;

        return { px, py, scale, z: z2 };
    }
}

// ==================== INIT PARTICLES ====================
const particles = [];
for (let i = 0; i < NUM_PARTICLES; i++) {
    particles.push(new Particle(i, NUM_PARTICLES));
}

// ==================== EXPLOSION ====================
function disperseParticles() {
    particles.forEach(p => {
        let mag = 8 + Math.random() * 12;
        p.vx += p.homeX * mag;
        p.vy += p.homeY * mag;
        p.vz += p.homeZ * mag;
    });
}

// ==================== RIPPLE / SHOCKWAVE (Feature 4) ====================
function createRipple(mouseX, mouseY) {
    particles.forEach(p => {
        let proj = p.project();
        let dx = proj.px - mouseX;
        let dy = proj.py - mouseY;
        let dist = Math.sqrt(dx * dx + dy * dy);

        // Affect particles within 200px of click
        if (dist < 200) {
            let force = (1 - dist / 200) * 6;
            // Push particles outward from their home (radially)
            p.vx += p.homeX * force;
            p.vy += p.homeY * force;
            p.vz += p.homeZ * force;
        }
    });
}

// ==================== MOUSE EVENT LISTENERS (Feature 4) ====================
canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
    dragVelocityY = 0;
    dragVelocityX = 0;
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    let dx = e.clientX - lastMouseX;
    let dy = e.clientY - lastMouseY;

    dragVelocityY = dx * 0.005;
    dragVelocityX = dy * 0.005;

    manualRotationY += dragVelocityY;
    manualRotationX += dragVelocityX;

    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
});

canvas.addEventListener('mouseup', () => {
    isDragging = false;
});

canvas.addEventListener('mouseleave', () => {
    isDragging = false;
});

canvas.addEventListener('click', (e) => {
    if (Math.abs(dragVelocityY) < 0.001 && Math.abs(dragVelocityX) < 0.001) {
        createRipple(e.clientX, e.clientY);
    }
});

// ==================== AURORA RENDERER (Feature 1) ====================
function renderAurora() {
    auroraCtx.clearRect(0, 0, width, height);

    // Smooth color interpolation
    auroraHue += (auroraTargetHue - auroraHue) * 0.02;
    auroraIntensity += (auroraTargetIntensity - auroraIntensity) * 0.03;

    let t = time * 0.008;

    // Primary glow — centered, large
    let g1 = auroraCtx.createRadialGradient(
        centerX + Math.sin(t) * 50,
        centerY + Math.cos(t * 0.7) * 30,
        0,
        centerX, centerY,
        Math.max(width, height) * 0.6
    );
    g1.addColorStop(0, `hsla(${auroraHue}, ${auroraSaturation}%, 50%, ${auroraIntensity})`);
    g1.addColorStop(0.4, `hsla(${auroraHue + 20}, ${auroraSaturation}%, 40%, ${auroraIntensity * 0.5})`);
    g1.addColorStop(1, 'rgba(5, 5, 5, 0)');
    auroraCtx.fillStyle = g1;
    auroraCtx.fillRect(0, 0, width, height);

    // Secondary glow — offset, drifting
    let g2 = auroraCtx.createRadialGradient(
        centerX + Math.cos(t * 1.3) * 120,
        centerY + Math.sin(t * 0.9) * 80,
        0,
        centerX, centerY,
        Math.max(width, height) * 0.45
    );
    g2.addColorStop(0, `hsla(${auroraHue + 40}, ${auroraSaturation - 10}%, 45%, ${auroraIntensity * 0.6})`);
    g2.addColorStop(0.5, `hsla(${auroraHue + 60}, ${auroraSaturation - 20}%, 35%, ${auroraIntensity * 0.2})`);
    g2.addColorStop(1, 'rgba(5, 5, 5, 0)');
    auroraCtx.fillStyle = g2;
    auroraCtx.fillRect(0, 0, width, height);

    // Tertiary subtle accent
    let g3 = auroraCtx.createRadialGradient(
        centerX + Math.sin(t * 0.5) * 180,
        centerY + Math.cos(t * 1.1) * 100,
        0,
        centerX, centerY,
        Math.max(width, height) * 0.35
    );
    g3.addColorStop(0, `hsla(${auroraHue - 30}, 70%, 55%, ${auroraIntensity * 0.3})`);
    g3.addColorStop(1, 'rgba(5, 5, 5, 0)');
    auroraCtx.fillStyle = g3;
    auroraCtx.fillRect(0, 0, width, height);
}

// ==================== WAVEFORM RENDERER (Feature 3) ====================
function renderWaveform() {
    const w = waveformCanvas.width;
    const h = waveformCanvas.height;
    waveformCtx.clearRect(0, 0, w, h);

    // Smooth amplitude interpolation
    waveAmplitude += (waveTargetAmplitude - waveAmplitude) * 0.08;
    wavePhase += 0.04;

    const midY = h / 2;
    const segments = 120;
    const segWidth = w / segments;

    // Get state-dependent color
    let waveHue;
    if (currentUiState === 'idle' || currentUiState === 'thinking') {
        waveHue = auroraHue; // Blue/Cyan
    } else {
        waveHue = 150; // Green
    }

    // Draw multiple wave layers for depth
    for (let layer = 0; layer < 3; layer++) {
        let layerAlpha = (0.3 - layer * 0.08);
        let layerAmp = waveAmplitude * (1 - layer * 0.25);
        let layerPhaseOffset = layer * 0.8;

        waveformCtx.beginPath();
        waveformCtx.moveTo(0, midY);

        for (let i = 0; i <= segments; i++) {
            let x = i * segWidth;
            let normalX = i / segments;

            // Envelope: fade edges to zero
            let envelope = Math.sin(normalX * Math.PI);

            // Composite wave
            let y = midY +
                Math.sin(normalX * Math.PI * 4 + wavePhase + layerPhaseOffset) * layerAmp * envelope * 0.6 +
                Math.sin(normalX * Math.PI * 7 + wavePhase * 1.3 + layerPhaseOffset) * layerAmp * envelope * 0.3 +
                Math.sin(normalX * Math.PI * 2 + wavePhase * 0.5 + layerPhaseOffset) * layerAmp * envelope * 0.4;

            if (i === 0) {
                waveformCtx.moveTo(x, y);
            } else {
                waveformCtx.lineTo(x, y);
            }
        }

        waveformCtx.strokeStyle = `hsla(${waveHue + layer * 15}, 80%, 60%, ${layerAlpha})`;
        waveformCtx.lineWidth = 2 - layer * 0.5;
        waveformCtx.stroke();
    }

    // Center glow line (always visible, very subtle)
    waveformCtx.beginPath();
    waveformCtx.moveTo(0, midY);
    waveformCtx.lineTo(w, midY);
    waveformCtx.strokeStyle = `hsla(${waveHue}, 60%, 50%, 0.05)`;
    waveformCtx.lineWidth = 1;
    waveformCtx.stroke();
}

// ==================== RADIAL HUD RENDERER ====================
function drawRadialHuds() {
    ctx.save();
    
    // Dynamic styling based on auroraHue and waveAmplitude
    const hue = auroraHue;
    
    // 1. Inner Glow Ring (Solid, slightly pulsating)
    const r1 = currentRadius * 1.1 + Math.sin(time * 0.05) * 3;
    ctx.strokeStyle = `hsla(${hue}, 85%, 65%, 0.18)`;
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 10;
    ctx.shadowColor = `hsla(${hue}, 85%, 65%, 0.3)`;
    ctx.beginPath();
    ctx.arc(centerX, centerY, r1, 0, Math.PI * 2);
    ctx.stroke();
    
    // Reset shadow for other lines to keep them sharp
    ctx.shadowBlur = 0;
    
    // 2. Middle Rotating Dashed Ring
    const r2 = currentRadius * 1.3 + waveAmplitude * 0.4;
    ctx.strokeStyle = `hsla(${hue}, 90%, 70%, 0.25)`;
    ctx.lineWidth = 1;
    ctx.setLineDash([8, 15]);
    ctx.lineDashOffset = -time * 0.15;
    ctx.beginPath();
    ctx.arc(centerX, centerY, r2, 0, Math.PI * 2);
    ctx.stroke();
    
    // 3. Fine Tick-Mark HUD Ring (Thin and dense)
    const r3 = currentRadius * 1.5 + waveAmplitude * 0.6;
    ctx.strokeStyle = `hsla(${hue + 15}, 80%, 60%, 0.15)`;
    ctx.lineWidth = 0.8;
    ctx.setLineDash([2, 8]);
    ctx.lineDashOffset = time * 0.08;
    ctx.beginPath();
    ctx.arc(centerX, centerY, r3, 0, Math.PI * 2);
    ctx.stroke();
    
    // 4. Outer Rotating Arcs (Thicker bracket segments)
    const r4 = currentRadius * 1.45 + waveAmplitude * 0.5;
    ctx.strokeStyle = `hsla(${hue}, 95%, 75%, 0.35)`;
    ctx.lineWidth = 3;
    ctx.setLineDash([]); // clear dash
    
    // We draw two opposite arcs that rotate
    const angleOffset = time * 0.01;
    const arcLength = Math.PI / 3; // 60 degrees
    
    // Arc 1
    ctx.beginPath();
    ctx.arc(centerX, centerY, r4, angleOffset, angleOffset + arcLength);
    ctx.stroke();
    
    // Arc 2
    ctx.beginPath();
    ctx.arc(centerX, centerY, r4, angleOffset + Math.PI, angleOffset + Math.PI + arcLength);
    ctx.stroke();

    // 5. Crosshair ticks inside
    ctx.strokeStyle = `hsla(${hue}, 80%, 70%, 0.12)`;
    ctx.lineWidth = 1;
    
    const crossHairSize = 8;
    // Top
    ctx.beginPath();
    ctx.moveTo(centerX, centerY - currentRadius * 0.95);
    ctx.lineTo(centerX, centerY - currentRadius * 0.95 + crossHairSize);
    ctx.stroke();
    // Bottom
    ctx.beginPath();
    ctx.moveTo(centerX, centerY + currentRadius * 0.95);
    ctx.lineTo(centerX, centerY + currentRadius * 0.95 - crossHairSize);
    ctx.stroke();
    // Left
    ctx.beginPath();
    ctx.moveTo(centerX - currentRadius * 0.95, centerY);
    ctx.lineTo(centerX - currentRadius * 0.95 + crossHairSize, centerY);
    ctx.stroke();
    // Right
    ctx.beginPath();
    ctx.moveTo(centerX + currentRadius * 0.95, centerY);
    ctx.lineTo(centerX + currentRadius * 0.95 - crossHairSize, centerY);
    ctx.stroke();

    // ==================== 6. CIRCULAR CORE BATTERY & SIGNAL METERS ====================
    const gaugeRadius = currentRadius * 1.65 + waveAmplitude * 0.2;
    ctx.lineWidth = 1.5;

    // Left Gauge - SYS PWR (System Power)
    // Background arc
    ctx.strokeStyle = `hsla(${hue}, 80%, 50%, 0.08)`;
    ctx.beginPath();
    ctx.arc(centerX, centerY, gaugeRadius, 0.75 * Math.PI, 1.25 * Math.PI);
    ctx.stroke();

    // Active progress (fluctuates slightly)
    const pwrVal = 0.88 + Math.sin(time * 0.02) * 0.03 + Math.random() * 0.005;
    ctx.strokeStyle = `hsla(${hue}, 85%, 65%, 0.35)`;
    ctx.beginPath();
    ctx.arc(centerX, centerY, gaugeRadius, 1.25 * Math.PI - (0.5 * Math.PI * pwrVal), 1.25 * Math.PI);
    ctx.stroke();

    // Outer notched ring dots
    ctx.strokeStyle = `hsla(${hue}, 85%, 65%, 0.25)`;
    ctx.lineWidth = 2.5;
    ctx.setLineDash([1.5, 6.5]);
    ctx.beginPath();
    ctx.arc(centerX, centerY, gaugeRadius + 4, 0.75 * Math.PI, 1.25 * Math.PI);
    ctx.stroke();
    ctx.setLineDash([]); // reset line dash

    // Labels
    ctx.font = '8px Orbitron, monospace';
    ctx.fillStyle = `hsla(${hue}, 80%, 75%, 0.4)`;
    ctx.textAlign = 'right';
    ctx.fillText('SYS PWR', centerX - gaugeRadius - 10, centerY + 2);
    ctx.fillText(`${Math.round(pwrVal * 100)}%`, centerX - gaugeRadius - 10, centerY + 12);

    // Right Gauge - SIG INT (Signal Integrity)
    ctx.lineWidth = 1.5;
    // Background arc
    ctx.strokeStyle = `hsla(${hue}, 80%, 50%, 0.08)`;
    ctx.beginPath();
    ctx.arc(centerX, centerY, gaugeRadius, -0.25 * Math.PI, 0.25 * Math.PI);
    ctx.stroke();

    // Active progress (signal strength changes with state)
    let sigVal = 0.92 + Math.sin(time * 0.03) * 0.04;
    let sigLabel = 'SECURE';
    if (currentUiState === 'thinking') {
        sigVal = 0.75 + Math.sin(time * 0.12) * 0.15; // fluctuates more when processing
        sigLabel = 'PROC';
    } else if (currentUiState === 'listening') {
        sigVal = 0.96 + Math.sin(time * 0.06) * 0.03;
        sigLabel = 'LISTEN';
    } else if (currentUiState === 'speaking') {
        sigVal = 0.94 + Math.sin(time * 0.08) * 0.04;
        sigLabel = 'SPEAK';
    }
    ctx.strokeStyle = `hsla(${hue}, 85%, 65%, 0.35)`;
    ctx.beginPath();
    ctx.arc(centerX, centerY, gaugeRadius, -0.25 * Math.PI, -0.25 * Math.PI + (0.5 * Math.PI * sigVal));
    ctx.stroke();

    // Outer notched ring dots
    ctx.strokeStyle = `hsla(${hue}, 85%, 65%, 0.25)`;
    ctx.lineWidth = 2.5;
    ctx.setLineDash([1.5, 6.5]);
    ctx.beginPath();
    ctx.arc(centerX, centerY, gaugeRadius + 4, -0.25 * Math.PI, 0.25 * Math.PI);
    ctx.stroke();
    ctx.setLineDash([]); // reset line dash

    // Labels
    ctx.textAlign = 'left';
    ctx.fillText('SIG INT', centerX + gaugeRadius + 10, centerY + 2);
    ctx.fillText(sigLabel, centerX + gaugeRadius + 10, centerY + 12);
    
    ctx.restore();
}

// ==================== HOLOGRAM SCANNER RENDERER ====================
function renderLaserScanner() {
    ctx.save();
    
    const hue = auroraHue;
    const maxScanHeight = currentRadius * 1.35;
    
    // Laser position sweeps up and down
    const scanPeriod = time * 0.015;
    const scanY = centerY + Math.sin(scanPeriod) * maxScanHeight;
    const scanWidth = currentRadius * 1.5;
    
    // Draw horizontal grid lines that light up when scanned
    const gridLinesCount = 7;
    ctx.lineWidth = 0.8;
    for (let i = 0; i < gridLinesCount; i++) {
        const fraction = (i / (gridLinesCount - 1)) * 2 - 1; // range -1 to 1
        const lineY = centerY + fraction * maxScanHeight;
        
        // Calculate distance to laser scanner
        const dist = Math.abs(lineY - scanY);
        let alpha = 0.03; // baseline faint grid
        if (dist < 40) {
            // Light up near the laser scanner
            alpha = 0.03 + (1 - dist / 40) * 0.15;
        }
        
        ctx.strokeStyle = `hsla(${hue}, 80%, 70%, ${alpha})`;
        ctx.beginPath();
        // Spans across the active width at lineY
        const span = Math.sqrt(Math.max(0, maxScanHeight * maxScanHeight - (lineY - centerY) * (lineY - centerY))) * 1.1;
        ctx.moveTo(centerX - span, lineY);
        ctx.lineTo(centerX + span, lineY);
        ctx.stroke();
    }
    
    // Draw the active laser scanner line itself
    const laserGradient = ctx.createLinearGradient(centerX - scanWidth, scanY, centerX + scanWidth, scanY);
    laserGradient.addColorStop(0, `hsla(${hue}, 90%, 60%, 0)`);
    laserGradient.addColorStop(0.2, `hsla(${hue}, 90%, 65%, 0.3)`);
    laserGradient.addColorStop(0.5, `rgba(255, 255, 255, 0.95)`); // white hot core
    laserGradient.addColorStop(0.8, `hsla(${hue}, 90%, 65%, 0.3)`);
    laserGradient.addColorStop(1, `hsla(${hue}, 90%, 60%, 0)`);
    
    // Glowing laser beam blur
    ctx.shadowBlur = 12;
    ctx.shadowColor = `hsla(${hue}, 90%, 65%, 0.8)`;
    
    // Draw main laser beam line
    ctx.strokeStyle = laserGradient;
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(centerX - scanWidth, scanY);
    ctx.lineTo(centerX + scanWidth, scanY);
    ctx.stroke();
    
    // Reset shadow
    ctx.shadowBlur = 0;
    
    // Draw vertical flare at the endpoints of the laser beam (little tick marks)
    ctx.strokeStyle = `hsla(${hue}, 90%, 70%, 0.6)`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(centerX - scanWidth, scanY - 4);
    ctx.lineTo(centerX - scanWidth, scanY + 4);
    ctx.moveTo(centerX + scanWidth, scanY - 4);
    ctx.lineTo(centerX + scanWidth, scanY + 4);
    ctx.stroke();
    
    ctx.restore();
}

// ==================== RENDER LOOP ====================
let lastState = 'idle';

function render() {
    time++;

    // ---- State-driven physics ----
    if (currentUiState === 'idle') {
        targetRadius = SPHERE_RADIUS * 1.25;
        auroraTargetHue = 220;       // Deep indigo-blue
        auroraTargetIntensity = 0.06;
        waveTargetAmplitude = 2;     // Nearly flat
    } else if (currentUiState === 'listening') {
        targetRadius = SPHERE_RADIUS;
        auroraTargetHue = 150;       // Vibrant green
        auroraTargetIntensity = 0.1;
        waveTargetAmplitude = 8;     // Subtle movement
    } else if (currentUiState === 'thinking') {
        targetRadius = SPHERE_RADIUS * 0.8;
        auroraTargetHue = 185;       // Electric cyan
        auroraTargetIntensity = 0.14;
        waveTargetAmplitude = 4;     // Gentle pulse
    } else if (currentUiState === 'speaking') {
        targetRadius = SPHERE_RADIUS * 1.55;
        auroraTargetHue = 160;       // Teal-green
        auroraTargetIntensity = 0.12;
        waveTargetAmplitude = 25;    // Full active waves
    }

    // Trigger explosion only on state TRANSITION to speaking
    if (currentUiState === 'speaking' && lastState !== 'speaking') {
        disperseParticles();
    }
    lastState = currentUiState;

    // Smooth radius interpolation
    currentRadius += (targetRadius - currentRadius) * 0.06;

    // Rotate the sphere (auto rotation + drag inertia)
    if (!isDragging) {
        rotationY += ROTATION_SPEED_Y;
        rotationX += ROTATION_SPEED_X;

        // Decay drag velocity smoothly
        dragVelocityY *= 0.96;
        dragVelocityX *= 0.96;
        manualRotationY += dragVelocityY;
        manualRotationX += dragVelocityX;
    }

    // Update particles
    particles.forEach(p => p.update());

    // Project and sort by depth
    let projected = particles.map(p => {
        let proj = p.project();
        return { p, ...proj };
    });
    projected.sort((a, b) => a.z - b.z);

    // ---- Render Aurora Background ----
    renderAurora();

    // ---- Draw Particles ----
    // Clear with subtle trail
    ctx.fillStyle = 'rgba(5, 5, 5, 0.2)';
    ctx.fillRect(0, 0, width, height);

    // Draw glow behind sphere
    let glowHue = (currentUiState === 'listening' || currentUiState === 'speaking') ? 150 : 200;
    let glowSize = currentRadius * 1.5;
    let gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, glowSize);
    gradient.addColorStop(0, `hsla(${glowHue}, 80%, 50%, 0.06)`);
    gradient.addColorStop(1, 'rgba(5, 5, 5, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    // ---- Draw Radial Sci-Fi HUD Rings ----
    drawRadialHuds();

    // Draw each particle
    projected.forEach(pt => {
        let hue;
        if (currentUiState === 'idle' || currentUiState === 'thinking') {
            hue = 200 + (pt.z / (SPHERE_RADIUS * 3)) * 20;
        } else {
            hue = 140 + (pt.z / (SPHERE_RADIUS * 3)) * 20;
        }

        let alpha = 0.3 + pt.scale * 0.7;
        let size = pt.p.size * pt.scale;

        // Glow layer
        ctx.fillStyle = `hsla(${hue}, 80%, 60%, ${alpha * 0.3})`;
        ctx.beginPath();
        ctx.arc(pt.px, pt.py, size * 2.5, 0, Math.PI * 2);
        ctx.fill();

        // Core dot
        ctx.fillStyle = `hsla(${hue}, 90%, 70%, ${alpha})`;
        ctx.beginPath();
        ctx.arc(pt.px, pt.py, size, 0, Math.PI * 2);
        ctx.fill();
    });

    // ---- Render Hologram Laser Scanner ----
    renderLaserScanner();

    // ---- Render Waveform ----
    renderWaveform();

    requestAnimationFrame(render);
}

requestAnimationFrame(render);

// ==================== STATE INTERFACE ====================
window.setUiState = function(state) {
    currentUiState = state;
}
