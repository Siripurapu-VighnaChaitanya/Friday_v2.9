import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Post-Processing Imports
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { FXAAShader } from 'three/addons/shaders/FXAAShader.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// ============================================================================
// Global State & Configuration
// ============================================================================
let scene, camera, renderer, controls;
let avatarGroup;
let morphMeshes = [];             // Stores all meshes in the model containing morph targets
let morphTargetNames = [];        // Unique array of morph target names found in the model
const currentMorphInfluences = {}; // Current interpolated values applied to the model
const targetMorphInfluences = {};  // Target values we are interpolating towards
const manualSliderOverrides = new Set(); // Tracks morphs currently controlled manually by sliders

// ============================================================================
// Holographic AI Configuration & State Uniforms
// ============================================================================
const HOLOGRAPHIC_CONFIG = {
  glowIntensity: 0.35, // Reduced ~70% from 1.2
  rimStrength: 0.3,  // Very soft rim
  rimColor: '#00e5ff',
  eyeGlow: 1.2,
  bloomStrength: 0.8,
  bloomRadius: 0.4,
  bloomThreshold: 0.6, // High threshold so face doesn't bloom, only eyes/particles
  particleDensity: 0, // Removed particles
  particleSpeed: 0.3,
  particleColor: '#00d4ff',
  backgroundColor: '#000000' // Black space color
};

const holographicUniforms = {
  uTime: { value: 0 },
  uRimColor: { value: new THREE.Color(HOLOGRAPHIC_CONFIG.rimColor) },
  uRimStrength: { value: HOLOGRAPHIC_CONFIG.rimStrength },
  uGlowIntensity: { value: HOLOGRAPHIC_CONFIG.glowIntensity }
};

// Post-Processing & Particle State
let composer, renderPass, bloomPass, fxaaPass;
let energyParticleSystem = null;
let particlePositions, particleOriginals, particleVelocities, particleLifetimes;
let currentParticleCount = HOLOGRAPHIC_CONFIG.particleDensity;

let fpsFrameCount = 0;
let fpsLastTime = performance.now();
let currentFPS = 60;

// Camera setup defaults
const CAMERA_DEFAULT_POS = new THREE.Vector3(0, 0, 1.2);
const LOOK_AT_TARGET = new THREE.Vector3(0, 0.15, 0);

// Idle animations state
let blinkTimer = Math.random() * 3 + 2; // Time until next blink (in seconds)
let isBlinking = false;
let blinkDuration = 0.18; // 180ms total blink duration
let blinkElapsed = 0;

let eyeLookTimer = Math.random() * 2 + 1;
let targetEyeX = 0; // Negative = Left, Positive = Right
let targetEyeY = 0; // Negative = Down, Positive = Up
let curEyeX = 0;
let curEyeY = 0;

// Emotion Morph Target Presets
const EMOTIONS = {
  neutral: {},
  happy: {
    mouthSmile_L: 0.75,
    mouthSmile_R: 0.75,
    cheekSquint_L: 0.35,
    cheekSquint_R: 0.35,
    eyeSquint_L: 0.2,
    eyeSquint_R: 0.2,
    browOuterUp_L: 0.1,
    browOuterUp_R: 0.1
  },
  sad: {
    mouthFrown_L: 0.65,
    mouthFrown_R: 0.65,
    browDown_L: 0.3,
    browDown_R: 0.3,
    browInnerUp: 0.45,
    mouthShrugLower: 0.4
  },
  surprised: {
    browInnerUp: 0.65,
    eyeWide_L: 0.75,
    eyeWide_R: 0.75,
    jawOpen: 0.38,
    mouthFunnel: 0.2
  },
  angry: {
    browDown_L: 0.8,
    browDown_R: 0.8,
    noseSneer_L: 0.65,
    noseSneer_R: 0.65,
    mouthFrown_L: 0.45,
    mouthFrown_R: 0.45,
    mouthPress_L: 0.3,
    mouthPress_R: 0.3,
    eyeSquint_L: 0.3,
    eyeSquint_R: 0.3
  },
  thinking: {
    browOuterUp_L: 0.6,
    browDown_R: 0.2,
    eyeLookUp_L: 0.3,
    eyeLookUp_R: 0.3,
    eyeLookOut_L: 0.3,
    eyeLookIn_R: 0.3,
    mouthPress_L: 0.2,
    mouthPress_R: 0.2,
    mouthLeft: 0.25
  }
};
let currentEmotion = 'neutral';

// Speech (TTS) Animation State (kept for backward compatibility)
let ttsSpeaking = false;
let ttsSynth = window.speechSynthesis;
let currentUtterance = null;
let ttsVoices = [];

// Audio (Microphone) Capture State (kept for backward compatibility)
let audioCtx = null;
let audioAnalyser = null;
let audioSource = null;
let audioStream = null;
let micEnabled = false;
let micBoost = 2.0;

// ============================================================================
// Friday Backend WebSocket State
// ============================================================================
let fridayState = 'offline'; // offline, idle, listening, thinking, speaking
let fridayWs = null;
let fridayReconnectTimer = null;
let fridayTypingTimer = null;
let fridaySpeakingStartTime = 0;
let fridayEstimatedSpeechDuration = 0;

// Clock to handle frame time differences
const clock = new THREE.Clock();

// DOM elements cached
const loadingOverlay = document.getElementById('loading-overlay');
const loadingStatus = document.getElementById('loading-status');
const progressBar = document.getElementById('progress-bar');
const errorModal = document.getElementById('error-modal');
const errorTitle = document.getElementById('error-title');
const errorMessage = document.getElementById('error-message');
const btnCloseError = document.getElementById('btn-close-error');

// ============================================================================
// Initialization Functions
// ============================================================================

window.addEventListener('DOMContentLoaded', () => {
  initThree();
  setupUIEventListeners();
  loadAvatarModel('../../assets/facecap.bin');
  initFridayWebSocket();
  initEmotionMenu();
  initSessionLog();
});

// Close error modal handler
if (btnCloseError) {
  btnCloseError.addEventListener('click', () => {
    errorModal.classList.remove('active');
  });
}

function showSystemError(title, msg) {
  if (errorModal && errorTitle && errorMessage) {
    errorTitle.textContent = title;
    errorMessage.textContent = msg;
    errorModal.classList.add('active');
  } else {
    alert(`${title}: ${msg}`);
  }
}

/**
 * Initializes Three.js Scene, Camera, Renderer, Lighting, and Controls
 */
function initThree() {
  const container = document.getElementById('canvas-container');
  const canvas = document.getElementById('avatar-canvas');

  // Verify WebGL Support
  const canvasWebGL2 = document.createElement('canvas');
  const glSupport = !!(window.WebGLRenderingContext && (canvasWebGL2.getContext('webgl') || canvasWebGL2.getContext('webgl2')));
  if (!glSupport) {
    document.getElementById('status-webgl').querySelector('.status-indicator').className = 'status-indicator offline';
    showSystemError('WebGL Not Supported', 'Your browser or device does not support WebGL. 3D rendering is disabled.');
    return;
  }

  // Create Scene (Atmospheric Depth)
  scene = new THREE.Scene();
  scene.background = null; // Transparent to allow CSS multi-layered gradient
  scene.fog = new THREE.FogExp2(0x000000, 0.05); // Black space fog

  // Create Camera (Portrait Composition: 30 degree FOV)
  camera = new THREE.PerspectiveCamera(30, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(0, 0, 1.2); // Positioned closely for portrait framing

  // 1. Atmospheric Halo (Large soft cyan glow behind head for depth) - REMOVED for black background
  // const haloCanvas = document.createElement('canvas');
  // haloCanvas.width = 1024;
  // haloCanvas.height = 1024;
  // const haloCtx = haloCanvas.getContext('2d');
  // const haloGradient = haloCtx.createRadialGradient(512, 512, 0, 512, 512, 512);
  // haloGradient.addColorStop(0, 'rgba(0, 180, 255, 0.1)'); // Extremely low opacity center
  // haloGradient.addColorStop(0.4, 'rgba(0, 50, 150, 0.03)'); // Soft fade
  // haloGradient.addColorStop(1, 'rgba(0, 0, 0, 0)'); // Fade to transparent without hard edges
  // haloCtx.fillStyle = haloGradient;
  // haloCtx.fillRect(0, 0, 1024, 1024);

  // const haloTexture = new THREE.CanvasTexture(haloCanvas);
  // const haloMaterial = new THREE.SpriteMaterial({
  //   map: haloTexture,
  //   transparent: true,
  //   blending: THREE.AdditiveBlending,
  //   depthWrite: false
  // });
  // const atmosphericHalo = new THREE.Sprite(haloMaterial);
  // atmosphericHalo.scale.set(4.0, 4.0, 1.0); // 2-3x width of head
  // atmosphericHalo.position.set(0, 0, -0.6); // Pushed back behind the focal plane
  // scene.add(atmosphericHalo);

  // (Verification sphere removed)

  // Create Renderer
  renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance"
  });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;

  // Create Parent Group for Avatar
  avatarGroup = new THREE.Group();
  scene.add(avatarGroup);

  // Setup Cinematic Lighting
  // 1. Soft Key Light
  const keyLight = new THREE.DirectionalLight(0xddffff, 0.5);
  keyLight.position.set(1, 1.5, 2.5);
  camera.add(keyLight);

  // 2. Weak Fill Light
  const fillLight = new THREE.DirectionalLight(0x88bbff, 0.2);
  fillLight.position.set(-1.5, 0.5, 1);
  camera.add(fillLight);

  // 3. Subtle Rim Light
  const rimLight = new THREE.DirectionalLight(0x0088cc, 0.3);
  rimLight.position.set(0, 0.5, -2);
  scene.add(rimLight);

  // Must add camera to scene for its attached lights to work
  scene.add(camera);

  // Setup Post-Processing Composer Pipeline
  composer = new EffectComposer(renderer);
  renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  // Bloom Pass (Soft cyan glow around emissive edges and eyes)
  const bloomVector = new THREE.Vector2(container.clientWidth, container.clientHeight);
  bloomPass = new UnrealBloomPass(bloomVector, HOLOGRAPHIC_CONFIG.bloomStrength, HOLOGRAPHIC_CONFIG.bloomRadius, HOLOGRAPHIC_CONFIG.bloomThreshold);
  composer.addPass(bloomPass);

  // FXAA Pass (Smooth anti-aliased edges)
  fxaaPass = new ShaderPass(FXAAShader);
  const pixelRatio = renderer.getPixelRatio();
  fxaaPass.material.uniforms['resolution'].value.x = 1 / (container.clientWidth * pixelRatio);
  fxaaPass.material.uniforms['resolution'].value.y = 1 / (container.clientHeight * pixelRatio);
  composer.addPass(fxaaPass);

  // Output Pass (Color Space Conversion)
  const outputPass = new OutputPass();
  composer.addPass(outputPass);

  // Orbit Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 0.5;
  controls.maxDistance = 4;
  controls.target.copy(LOOK_AT_TARGET);
  controls.maxPolarAngle = Math.PI / 1.8; // Prevent looking directly from bottom
  controls.minPolarAngle = Math.PI / 3;   // Prevent looking directly from top
  controls.update();

  // Handle Window Resize
  window.addEventListener('resize', onWindowResize);

  // Mouse Tracking for Head and Eyes
  window.addEventListener('mousemove', (e) => {
    // Convert screen coordinates to normalized coordinates (-1 to 1)
    targetEyeX = (e.clientX / window.innerWidth) * 2 - 1;
    targetEyeY = -((e.clientY / window.innerHeight) * 2 - 1);
  });

  // Start Animation Loop
  renderer.setAnimationLoop(animate);
}

function onWindowResize() {
  const container = document.getElementById('canvas-container');
  if (!camera || !renderer) return;
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);

  if (composer) {
    composer.setSize(container.clientWidth, container.clientHeight);
    if (fxaaPass) {
      const pixelRatio = renderer.getPixelRatio();
      fxaaPass.material.uniforms['resolution'].value.x = 1 / (container.clientWidth * pixelRatio);
      fxaaPass.material.uniforms['resolution'].value.y = 1 / (container.clientHeight * pixelRatio);
    }
  }
}

// ============================================================================
// 3D Model Loading & Morph Target Setup
// ============================================================================

/**
 * Loads the GLB Avatar Model
 */
function loadAvatarModel(url) {
  const loader = new GLTFLoader();

  // Set up KTX2 Loader for texture compression
  const ktx2Loader = new KTX2Loader()
    .setTranscoderPath('https://unpkg.com/three@0.160.0/examples/jsm/libs/basis/')
    .detectSupport(renderer);
  loader.setKTX2Loader(ktx2Loader);

  // Set up Meshopt Decoder for mesh compression
  loader.setMeshoptDecoder(MeshoptDecoder);

  // Primary URL and Fallback URL to guarantee success under any server environment
  const primaryUrl = url || '../../assets/facecap.bin';
  const fallbackUrl = '../../assets/facecap.bin';

  const loadFromUrl = (targetUrl) => {
    fetch(targetUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.arrayBuffer();
      })
      .then(buffer => {
        loader.parse(
          buffer,
          '',
          (gltf) => {
            // Add loaded scene to our group
            avatarGroup.add(gltf.scene);

            // Traversal to find all meshes with Morph Targets
            gltf.scene.traverse((child) => {
              if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;

                // Apply Shaders on top of Original Base Material
                if (child.geometry && child.geometry.attributes.position) {
                  const vertCount = child.geometry.attributes.position.count;

                  if (vertCount > 2000) {
                    // Head Mesh: Deep cyan base, natural facial details, calm and elegant
                    const origMat = Array.isArray(child.material) ? child.material[0] : child.material;
                    const holoSkin = origMat ? origMat.clone() : new THREE.MeshStandardMaterial();

                    // Deep cyan base color, not glowing plastic
                    holoSkin.color = new THREE.Color(0x004466);
                    holoSkin.emissive = new THREE.Color(0x001122);
                    holoSkin.emissiveIntensity = HOLOGRAPHIC_CONFIG.glowIntensity;
                    holoSkin.metalness = 0.1;
                    holoSkin.roughness = 0.6; // Higher roughness, less plastic
                    holoSkin.transparent = false;
                    holoSkin.opacity = 1.0;

                    holoSkin.onBeforeCompile = (shader) => {
                      shader.uniforms.uTime = holographicUniforms.uTime;
                      shader.uniforms.uRimColor = holographicUniforms.uRimColor;
                      shader.uniforms.uRimStrength = holographicUniforms.uRimStrength;

                      shader.fragmentShader = `
                        uniform float uTime;
                        uniform vec3 uRimColor;
                        uniform float uRimStrength;
                        ${shader.fragmentShader}
                      `;

                      shader.fragmentShader = shader.fragmentShader.replace(
                        '#include <emissivemap_fragment>',
                        `
                        #include <emissivemap_fragment>
                        vec3 viewDir = normalize(vViewPosition);
                        vec3 nNormal = normalize(vNormal);
                        float fresnel = pow(1.0 - clamp(dot(nNormal, viewDir), 0.0, 1.0), 3.0);
                        
                        // Very soft additive rim glow at silhouette edges
                        totalEmissiveRadiance += uRimColor * fresnel * uRimStrength;
                        `
                      );
                    };

                    child.material = holoSkin;
                  } else if (vertCount === 530) {
                    // Eye Meshes: Brightest feature, visible sclera, cyan iris, catchlights
                    const origMat = Array.isArray(child.material) ? child.material[0] : child.material;
                    const eyeMat = origMat ? origMat.clone() : new THREE.MeshStandardMaterial();

                    eyeMat.color = new THREE.Color(0xddeeff);
                    eyeMat.emissive = new THREE.Color(0x00ffff);
                    eyeMat.emissiveIntensity = HOLOGRAPHIC_CONFIG.eyeGlow;
                    eyeMat.metalness = 0.2;
                    eyeMat.roughness = 0.1;
                    eyeMat.envMapIntensity = 1.5;
                    child.material = eyeMat;
                  } else {
                    // Teeth / Mouth Interior: dark, nearly invisible
                    const origMat = Array.isArray(child.material) ? child.material[0] : child.material;
                    const teethMat = origMat ? origMat.clone() : new THREE.MeshStandardMaterial();
                    teethMat.color = new THREE.Color(0x000a11);
                    teethMat.emissive = new THREE.Color(0x000000);
                    teethMat.emissiveIntensity = 0.0;
                    child.material = teethMat;
                  }
                }

                // Check if mesh has morph targets
                if (child.morphTargetDictionary && child.morphTargetInfluences) {
                  morphMeshes.push(child);

                  // Add unique morph target names
                  Object.keys(child.morphTargetDictionary).forEach((name) => {
                    if (!morphTargetNames.includes(name)) {
                      morphTargetNames.push(name);
                    }
                  });
                }
              }
            });

            if (morphMeshes.length === 0) {
              showSystemError('No Blendshapes Found', 'The loaded model does not contain any morph targets/blendshapes.');
            } else {
              // Initialize all influence targets to 0
              morphTargetNames.forEach((name) => {
                currentMorphInfluences[name] = 0;
                targetMorphInfluences[name] = 0;
              });

              // Build HTML sliders dynamically
              buildMorphSlidersUI();

              // Find the main head mesh to attach adaptive energy particles
              let headMesh = morphMeshes[0];
              let maxVerts = 0;
              for (const mesh of morphMeshes) {
                if (mesh.geometry && mesh.geometry.attributes.position && mesh.geometry.attributes.position.count > maxVerts) {
                  maxVerts = mesh.geometry.attributes.position.count;
                  headMesh = mesh;
                }
              }

              // Spawn Adaptive Digital Energy Particles
              // (Moved to AFTER centering — see below)
            }

            // Compute bounding box to automatically adjust camera framing nicely
            const box = new THREE.Box3().setFromObject(gltf.scene);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());

            // Center the model exactly at origin
            gltf.scene.position.x = -center.x;
            gltf.scene.position.y = -center.y;
            gltf.scene.position.z = -center.z;

            // Dynamically calculate proper camera distance to fit the model size
            const maxDim = Math.max(size.x, size.y, size.z);
            const fov = camera.fov * (Math.PI / 180);
            let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

            // Add padding so it fits comfortably in the viewport
            cameraZ *= 1.4;

            // Move camera back to the calculated distance, slightly elevated
            camera.position.set(0, size.y * 0.05, cameraZ);

            // Dynamically adjust orbit control limits based on model scale
            controls.minDistance = cameraZ * 0.4;
            controls.maxDistance = cameraZ * 3;
            controls.target.set(0, 0, 0);
            controls.update();

            // NOW create particles AFTER the model is centered at origin
            // Force world matrix update so bounding box is computed correctly
            gltf.scene.updateMatrixWorld(true);
            if (morphMeshes.length > 0) {
              let headMeshForParticles = morphMeshes[0];
              let maxVertsP = 0;
              for (const mesh of morphMeshes) {
                if (mesh.geometry && mesh.geometry.attributes.position && mesh.geometry.attributes.position.count > maxVertsP) {
                  maxVertsP = mesh.geometry.attributes.position.count;
                  headMeshForParticles = mesh;
                }
              }
              createAdaptiveEnergyParticles(headMeshForParticles);
            }

            // Hide loading screen
            fadeOutOverlay();
          },
          (parseError) => {
            console.error('Error parsing GLTF binary buffer:', parseError);
            if (targetUrl !== fallbackUrl) {
              console.log('Attempting fallback to ./facecap.txt...');
              loadFromUrl(fallbackUrl);
            } else {
              showSystemError('Parsing Error', 'Failed to parse 3D face model binary data.');
            }
          }
        );
      })
      .catch(fetchErr => {
        console.warn(`Failed to fetch ${targetUrl}:`, fetchErr);
        if (targetUrl !== fallbackUrl) {
          console.log('Attempting fallback fetch to ./facecap.txt...');
          loadFromUrl(fallbackUrl);
        } else {
          progressBar.style.width = '0%';
          loadingStatus.textContent = 'Loading failed';
          showSystemError('Failed to Load Asset', 'Could not load facecap model file. Please refresh the page.');
        }
      });
  };

  // Start initial fetch
  loadFromUrl(primaryUrl);
}

function fadeOutOverlay() {
  loadingOverlay.style.opacity = 0;
  setTimeout(() => {
    loadingOverlay.style.display = 'none';
  }, 800);
}

// ============================================================================
// UI Generation & Events
// ============================================================================

/**
 * Dynamically builds the sliders in categories inside the left sidebar
 */
function buildMorphSlidersUI() {
  // Sliders UI has been removed in this version to declutter the interface.
  // The avatar now automatically animates based on Friday's state.
  console.log('Morph sliders disabled (auto-lip-sync active).');
}

function resetActiveEmotionButtons() {
  document.querySelectorAll('.btn-emotion').forEach((btn) => {
    btn.classList.remove('active');
  });
  currentEmotion = 'custom';
}

function setupUIEventListeners() {
  // Emotion buttons click
  document.querySelectorAll('.btn-emotion').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const emotionName = e.currentTarget.getAttribute('data-emotion');
      applyEmotion(emotionName);

      // Update UI buttons active state
      document.querySelectorAll('.btn-emotion').forEach((b) => b.classList.remove('active'));
      e.currentTarget.classList.add('active');
    });
  });
}

/**
 * Resets all morph targets to 0.0
 */
function resetAllMorphTargets() {
  manualSliderOverrides.clear();
  applyEmotion('neutral');
  document.querySelectorAll('.btn-emotion').forEach((btn) => btn.classList.remove('active'));
  const btnNeutral = document.querySelector('[data-emotion="neutral"]');
  if (btnNeutral) btnNeutral.classList.add('active');
}

/**
 * Applies preset emotion values to target morph influences
 */
function applyEmotion(emotionName) {
  if (!EMOTIONS[emotionName]) return;
  currentEmotion = emotionName;
  const emotionValues = EMOTIONS[emotionName];

  // Set all non-overridden targets to 0, or to the preset values
  morphTargetNames.forEach((name) => {
    // If user is controlling a slider manually, don't overwrite it
    if (manualSliderOverrides.has(name)) return;

    if (emotionValues[name] !== undefined) {
      targetMorphInfluences[name] = emotionValues[name];
    } else {
      targetMorphInfluences[name] = 0.0;
    }

    // Update UI slider values
    const range = document.querySelector(`.morph-range[data-morph="${name}"]`);
    if (range) {
      range.value = targetMorphInfluences[name];
      document.getElementById(`val-${name}`).textContent = targetMorphInfluences[name].toFixed(2);
    }
  });
}

// ============================================================================
// Text to Speech Engine (TTS) & Lip-Sync Animation
// ============================================================================
// Removed TTS and Mic functions since Friday Python backend handles the logic

// ============================================================================
// Animation Frame & Main Render Loop
// ============================================================================

function animate(time) {
  const delta = clock.getDelta();
  const elapsedTime = clock.getElapsedTime();

  // Update Holographic Time Uniform
  holographicUniforms.uTime.value = elapsedTime;

  // FPS Monitoring & Adaptive Particle Density Scaling
  fpsFrameCount++;
  const now = performance.now();
  if (now - fpsLastTime >= 1000) {
    currentFPS = (fpsFrameCount * 1000) / (now - fpsLastTime);
    fpsFrameCount = 0;
    fpsLastTime = now;

    // Auto-scale particle count down if FPS drops below 45
    if (currentFPS < 45 && currentParticleCount > 800 && energyParticleSystem) {
      currentParticleCount = Math.max(800, Math.floor(currentParticleCount * 0.85));
      energyParticleSystem.geometry.setDrawRange(0, currentParticleCount);
    }
  }

  // 1. Natural Idle swayed motion + Mouse Tracking
  if (avatarGroup) {
    // Gentle breathing vertical movement
    avatarGroup.position.y = Math.sin(elapsedTime * 1.5) * 0.004;

    // Head tracks mouse with slight idle sway layered on top
    const headSwayX = Math.sin(elapsedTime * 1.2) * 0.012;
    const headSwayY = Math.cos(elapsedTime * 0.7) * 0.008;

    // Limit head rotation so it doesn't break its neck
    const maxHeadTurn = 0.6; // radians
    const maxHeadTilt = 0.35; // radians

    // Smoothly apply rotation based on the smoothed eye tracking variables (curEyeX, curEyeY)
    avatarGroup.rotation.y = (curEyeX * maxHeadTurn) + headSwayY;
    avatarGroup.rotation.x = (-curEyeY * maxHeadTilt) + headSwayX;
  }

  // 2. Natural Auto-Blink Logic
  handleIdleBlink(delta);

  // 3. Natural Eye movement (saccades)
  handleEyeMovement(delta);

  // 4. Voice Lip-Sync Driving (Friday Backend State or fallback TTS/Mic)
  if (fridayState === 'speaking') {
    processFridayLipSync(elapsedTime);
  } else if (micEnabled && audioAnalyser) {
    processMicLipSync();
  } else if (ttsSpeaking) {
    processTTSLipSync(elapsedTime);
  } else if (fridayState !== 'speaking') {
    // Ensure mouth closes when not speaking
    if (!manualSliderOverrides.has('jawOpen')) {
      targetMorphInfluences['jawOpen'] = currentEmotion === 'surprised' ? 0.38 : 0;
      targetMorphInfluences['mouthFunnel'] = currentEmotion === 'surprised' ? 0.2 : 0;
      targetMorphInfluences['mouthPucker'] = 0;
      targetMorphInfluences['mouthSmile_L'] = 0;
      targetMorphInfluences['mouthSmile_R'] = 0;
      targetMorphInfluences['mouthStretch_L'] = 0;
      targetMorphInfluences['mouthStretch_R'] = 0;
      targetMorphInfluences['mouthShrugUpper'] = 0;
      targetMorphInfluences['mouthLowerDown_L'] = 0;
      targetMorphInfluences['mouthLowerDown_R'] = 0;
    }
  }

  // 5. Interpolate (lerp) Morph influences smoothly toward targets
  interpolateMorphTargets();

  // 6. State-Reactive Lighting & Holographic Emission Pulsing
  let targetGlow = HOLOGRAPHIC_CONFIG.glowIntensity;
  let targetRim = HOLOGRAPHIC_CONFIG.rimStrength;

  if (fridayState === 'listening') {
    // LISTENING state: subtle green pulse
    const pulse = Math.sin(elapsedTime * 6.0) * 0.15 + 0.15;
    targetGlow += pulse;
    targetRim += pulse * 0.5;
  } else if (fridayState === 'thinking' || currentEmotion === 'thinking') {
    // THINKING state: slow energy wave
    const wave = Math.sin(elapsedTime * 2.5) * 0.25 + 0.25;
    targetGlow += wave;
    targetRim += wave * 0.8;
  } else if (fridayState === 'speaking' || ttsSpeaking) {
    // SPEAKING state: brighter emission
    const speakPulse = Math.cos(elapsedTime * 10.0) * 0.2 + 0.25;
    targetGlow += speakPulse;
  }

  holographicUniforms.uGlowIntensity.value += (targetGlow - holographicUniforms.uGlowIntensity.value) * 0.1;
  holographicUniforms.uRimStrength.value += (targetRim - holographicUniforms.uRimStrength.value) * 0.1;

  // 7. Animate Adaptive Energy Particles
  if (energyParticleSystem && energyParticleSystem.geometry) {
    const pos = energyParticleSystem.geometry.attributes.position.array;
    const initPos = energyParticleSystem.geometry.attributes.initialPosition ? energyParticleSystem.geometry.attributes.initialPosition.array : null;
    const vel = energyParticleSystem.geometry.attributes.velocity ? energyParticleSystem.geometry.attributes.velocity.array : null;
    const life = energyParticleSystem.geometry.attributes.lifetime ? energyParticleSystem.geometry.attributes.lifetime.array : null;

    if (pos && vel && life && initPos) {
      const speedMult = HOLOGRAPHIC_CONFIG.particleSpeed;
      for (let i = 0; i < currentParticleCount; i++) {
        life[i] -= delta * speedMult;
        if (life[i] <= 0) {
          pos[i * 3] = initPos[i * 3];
          pos[i * 3 + 1] = initPos[i * 3 + 1];
          pos[i * 3 + 2] = initPos[i * 3 + 2];
          life[i] = Math.random() * 2.0;
        } else {
          pos[i * 3] += vel[i * 3] * speedMult;
          pos[i * 3 + 1] += vel[i * 3 + 1] * speedMult;
          pos[i * 3 + 2] += vel[i * 3 + 2] * speedMult;
        }
      }
      energyParticleSystem.geometry.attributes.position.needsUpdate = true;
    }
  }

  // 8. Update controls & render scene via EffectComposer
  if (controls) controls.update();
  if (composer) {
    composer.render();
  } else if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

/**
 * Randomized natural blinking behavior
 */
function handleIdleBlink(delta) {
  if (manualSliderOverrides.has('eyeBlink_L') || manualSliderOverrides.has('eyeBlink_R')) return;

  if (isBlinking) {
    blinkElapsed += delta;
    const progress = blinkElapsed / blinkDuration;

    if (progress >= 1.0) {
      isBlinking = false;
      targetMorphInfluences['eyeBlink_L'] = 0;
      targetMorphInfluences['eyeBlink_R'] = 0;
      blinkTimer = Math.random() * 4 + 2; // Random wait: 2-6 seconds
    } else {
      // Sine curve for eye closing and opening back up rapidly
      const blinkInfluence = Math.sin(progress * Math.PI);
      targetMorphInfluences['eyeBlink_L'] = blinkInfluence;
      targetMorphInfluences['eyeBlink_R'] = blinkInfluence;
    }
  } else {
    blinkTimer -= delta;
    if (blinkTimer <= 0) {
      isBlinking = true;
      blinkElapsed = 0;
    }
  }
}

/**
 * Smoothly interpolates eye morphs to follow the target coordinates (Mouse Tracking)
 */
function handleEyeMovement(delta) {

  // Smoothly slide current look values towards targets
  curEyeX += (targetEyeX - curEyeX) * 0.15;
  curEyeY += (targetEyeY - curEyeY) * 0.15;

  // Map to ARKit morphs
  // Note: ARKit Left/Right is from the Avatar's perspective

  // Left Eye (On OUR right side of the screen)
  targetMorphInfluences['eyeLookOut_L'] = curEyeX > 0 ? curEyeX : 0; // Mouse Right -> Looks Out (Towards our right)
  targetMorphInfluences['eyeLookIn_L'] = curEyeX < 0 ? -curEyeX : 0; // Mouse Left -> Looks In (Towards our left)
  targetMorphInfluences['eyeLookUp_L'] = curEyeY > 0 ? curEyeY : 0;
  targetMorphInfluences['eyeLookDown_L'] = curEyeY < 0 ? -curEyeY : 0;

  // Right Eye (On OUR left side of the screen)
  targetMorphInfluences['eyeLookIn_R'] = curEyeX > 0 ? curEyeX : 0; // Mouse Right -> Looks In (Towards our right)
  targetMorphInfluences['eyeLookOut_R'] = curEyeX < 0 ? -curEyeX : 0; // Mouse Left -> Looks Out (Towards our left)
  targetMorphInfluences['eyeLookUp_R'] = curEyeY > 0 ? curEyeY : 0;
  targetMorphInfluences['eyeLookDown_R'] = curEyeY < 0 ? -curEyeY : 0;
}

/**
 * Procedural TTS conversation lip sync (jaw bounce)
 */
function processTTSLipSync(time) {
  // Check if manually modified
  if (manualSliderOverrides.has('jawOpen')) return;

  // Combine low-frequency mouth open waves with high frequency jitter to simulate phoneme changes
  const baseWave = Math.sin(time * 15) * Math.cos(time * 8);
  const talkValue = Math.max(0, (baseWave + 0.8) * 0.4);

  targetMorphInfluences['jawOpen'] = talkValue;

  // Vary mouth shape during speech
  targetMorphInfluences['mouthFunnel'] = Math.max(0, Math.sin(time * 9) * 0.15);
  targetMorphInfluences['mouthPucker'] = Math.max(0, Math.cos(time * 11) * 0.12);
}

/**
 * Audio analysis to extract amplitude volume and drive the jaw morph target
 */
function processMicLipSync() {
  if (!audioAnalyser || manualSliderOverrides.has('jawOpen')) return;

  const dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
  audioAnalyser.getByteTimeDomainData(dataArray);

  // Compute Root Mean Square (RMS) volume
  let sum = 0;
  for (let i = 0; i < dataArray.length; i++) {
    const val = (dataArray[i] - 128) / 128.0; // Normalize between -1.0 and 1.0
    sum += val * val;
  }
  const rms = Math.sqrt(sum / dataArray.length);

  // Apply sensitivity boost
  const volume = Math.min(1.0, rms * micBoost);

  // Update visualizer bar width
  document.getElementById('mic-visualizer').style.width = (volume * 100) + '%';

  // Open the jaw proportional to the captured volume
  // Low volume threshold (noise gate)
  if (volume > 0.05) {
    targetMorphInfluences['jawOpen'] = volume * 0.85;
    // Subtle mouth shaping based on loudness
    targetMorphInfluences['mouthFunnel'] = volume * 0.25;
    targetMorphInfluences['mouthPucker'] = volume * 0.15;
  } else {
    // Close mouth smoothly
    targetMorphInfluences['jawOpen'] = currentEmotion === 'surprised' ? 0.38 : 0;
    targetMorphInfluences['mouthFunnel'] = currentEmotion === 'surprised' ? 0.2 : 0;
    targetMorphInfluences['mouthPucker'] = 0;
  }
}

/**
 * Linearly interpolates the mesh morph influences towards the target values
 */
function interpolateMorphTargets() {
  const lerpFactor = 0.18; // Speed of expression transitions (18% per frame)

  morphTargetNames.forEach((name) => {
    // Interpolate current influence value
    currentMorphInfluences[name] += (targetMorphInfluences[name] - currentMorphInfluences[name]) * lerpFactor;

    // Apply value to all meshes containing this target
    morphMeshes.forEach((mesh) => {
      const index = mesh.morphTargetDictionary[name];
      if (index !== undefined) {
        mesh.morphTargetInfluences[index] = currentMorphInfluences[name];
      }
    });

    // Update UI text displays (Only if the slider is not currently being hovered/dragged manually)
    if (!manualSliderOverrides.has(name)) {
      const valDisplay = document.getElementById(`val-${name}`);
      const range = document.querySelector(`.morph-range[data-morph="${name}"]`);
      if (valDisplay && range) {
        valDisplay.textContent = currentMorphInfluences[name].toFixed(2);
        range.value = currentMorphInfluences[name];
      }
    }
  });
}

// ============================================================================
// Adaptive Energy Particle System & Spatial Exclusion Zone
// ============================================================================

function createAdaptiveEnergyParticles(headMesh) {
  const count = HOLOGRAPHIC_CONFIG.particleDensity;
  console.log('[PARTICLES] Creating', count, 'particles around headMesh:', headMesh.name);
  const geometry = new THREE.BufferGeometry();

  particlePositions = new Float32Array(count * 3);
  particleOriginals = new Float32Array(count * 3);
  particleVelocities = new Float32Array(count * 3);
  particleLifetimes = new Float32Array(count);
  const colors = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const opacities = new Float32Array(count);

  // Multi-shade blue/cyan palette — ALL shades must be visible against dark bg
  const colorPalette = [
    new THREE.Color(0x0055aa),  // Dark blue (visible)
    new THREE.Color(0x0066bb),  // Medium-dark blue
    new THREE.Color(0x0077cc),  // Medium blue
    new THREE.Color(0x0088dd),  // Bright blue
    new THREE.Color(0x0099ee),  // Cyan-blue
    new THREE.Color(0x00aaff),  // Soft cyan
    new THREE.Color(0x00ccff),  // Bright cyan
    new THREE.Color(0x00eeff),  // Electric cyan
    new THREE.Color(0x99ffff),  // Near-white highlight
  ];

  // Get head bounding box in world space
  const headBox = new THREE.Box3().setFromObject(headMesh);
  const headCenter = headBox.getCenter(new THREE.Vector3());
  const headSize = headBox.getSize(new THREE.Vector3());
  const headRadius = Math.max(headSize.x, headSize.y, headSize.z) * 0.5;

  // The particle cloud extends to ~3x the head radius
  const maxCloudRadius = headRadius * 3.0;

  console.log('[PARTICLES] headCenter:', headCenter, 'headRadius:', headRadius, 'maxCloudRadius:', maxCloudRadius);

  let validCount = 0;
  let attempts = 0;
  const maxAttempts = count * 15;

  while (validCount < count && attempts < maxAttempts) {
    attempts++;

    // === DISTRIBUTION: Organic, Cinematic Falloff ===
    // Use a power curve to heavily cluster particles near the head silhouette
    const u = Math.pow(Math.random(), 3.0); // Extreme clustering near 0
    
    // Base radius ranges from 0.8x to 3.5x headRadius, densely packed near 0.8
    let r = headRadius * (0.8 + u * 2.7);

    // Spherical angles
    const theta = Math.random() * 2 * Math.PI;
    const phi = Math.acos(2 * Math.random() - 1);

    // Organic wisps/clustering (subtle noise based on angle)
    const wisp = Math.sin(phi * 4.0) * Math.cos(theta * 5.0); // range -1 to 1
    r += headRadius * wisp * 0.3 * (0.3 + u); // Wisps become more noticeable slightly further out

    // Shape the cloud to follow the tall head silhouette (Ellipsoid instead of Sphere)
    const shapeScaleX = 0.85; // Slightly narrower
    const shapeScaleY = 1.25; // Taller
    const shapeScaleZ = 0.80; // Slightly flatter depth

    const x = headCenter.x + r * Math.sin(phi) * Math.cos(theta) * shapeScaleX;
    const y = headCenter.y + r * Math.sin(phi) * Math.sin(theta) * shapeScaleY;
    const z = headCenter.z + r * Math.cos(phi) * shapeScaleZ;

    // === 3D FACE EXCLUSION: Keep the face completely clean ===
    const relX = x - headCenter.x;
    const relY = y - headCenter.y;
    const relZ = z - headCenter.z;
    const distFromCenter = Math.sqrt(relX * relX + relY * relY + relZ * relZ);

    // Create a bullet-shaped exclusion ellipsoid.
    // It tightly wraps the head's width/height, but extends massively towards the camera (+Z).
    // This prevents ANY particles from floating in the air between the face and the camera,
    // ensuring the face remains a clean silhouette embedded in the cloud.
    const rx = headSize.x * 0.7;  // 70% of bounding box width (covers face)
    const ry = headSize.y * 0.6;  // 60% of bounding box height (covers chin to forehead)
    const rzFront = headSize.z * 3.0; // Extends far out in front of the face
    const rzBack = headSize.z * 0.4;  // Allows particles immediately behind the head

    const normX = relX / rx;
    const normY = (relY + headSize.y * 0.1) / ry; // Shift exclusion slightly down to cover chin
    const normZ = relZ > 0 ? (relZ / rzFront) : (relZ / rzBack);

    if (normX * normX + normY * normY + normZ * normZ < 1.0) {
      continue; // Inside the exclusion zone, skip!
    }

    const idx = validCount * 3;
    particlePositions[idx] = x;
    particlePositions[idx + 1] = y;
    particlePositions[idx + 2] = z;

    particleOriginals[idx] = x;
    particleOriginals[idx + 1] = y;
    particleOriginals[idx + 2] = z;

    // Very slow, organic floating drift
    particleVelocities[idx] = (Math.random() - 0.5) * 0.0003;
    particleVelocities[idx + 1] = (Math.random() - 0.5) * 0.0003;
    particleVelocities[idx + 2] = (Math.random() - 0.5) * 0.0003;

    particleLifetimes[validCount] = Math.random() * 4.0 + 2.0;

    // === COLOR: Cinematic Gradient ===
    // Use the actual distance to determine falloff
    const normalizedDist = Math.max(0, Math.min(1.0, (distFromCenter - headRadius * 0.8) / (maxCloudRadius - headRadius * 0.8)));
    
    let colorIndex;
    if (normalizedDist < 0.15) {
      // ZONE A: Inner halo - extremely bright cyan and white
      colorIndex = 6 + Math.floor(Math.random() * 3); // 6-8: Bright Cyan, Electric, White
    } else if (normalizedDist < 0.35) {
      // ZONE B: Surrounding head - dense cyan/electric blue
      colorIndex = 4 + Math.floor(Math.random() * 3); // 4-6: Soft Cyan, Bright Cyan
    } else if (normalizedDist < 0.65) {
      // ZONE C: Outer atmosphere - medium blue/cyan
      colorIndex = 2 + Math.floor(Math.random() * 2); // 2-3: Medium Blue, Bright Blue
    } else {
      // ZONE D: Far edges - sparse dark blue
      colorIndex = Math.floor(Math.random() * 2);     // 0-1: Dark Blue, Medium-dark
    }
    colorIndex = Math.min(colorIndex, colorPalette.length - 1);
    const pColor = colorPalette[colorIndex];
    colors[idx] = pColor.r;
    colors[idx + 1] = pColor.g;
    colors[idx + 2] = pColor.b;

    // === SIZE: Organic Cinematic Variation ===
    const baseSizeNear = 0.025 + Math.random() * 0.025; // Soft large glow near head
    const baseSizeFar = 0.004 + Math.random() * 0.008;  // Tiny scattered specs far away
    // Ease-out curve so size stays relatively large in mid-zone before shrinking
    const sizeLerp = Math.pow(normalizedDist, 1.5);
    sizes[validCount] = baseSizeNear * (1.0 - sizeLerp) + baseSizeFar * sizeLerp;

    // === OPACITY: Smooth Atmospheric Fade ===
    const opacityNear = 0.85 + Math.random() * 0.15; // Very visible near head
    const opacityFar = 0.05 + Math.random() * 0.1;   // Very subtle at edges
    const opacityLerp = Math.pow(normalizedDist, 1.2);
    opacities[validCount] = opacityNear * (1.0 - opacityLerp) + opacityFar * opacityLerp;

    validCount++;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
  geometry.setAttribute('initialPosition', new THREE.BufferAttribute(particleOriginals, 3));
  geometry.setAttribute('velocity', new THREE.BufferAttribute(particleVelocities, 3));
  geometry.setAttribute('lifetime', new THREE.BufferAttribute(particleLifetimes, 1));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

  // Soft circular particle sprite (radial gradient dot)
  const spriteCanvas = document.createElement('canvas');
  spriteCanvas.width = 32;
  spriteCanvas.height = 32;
  const ctx = spriteCanvas.getContext('2d');
  const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
  gradient.addColorStop(0.15, 'rgba(255, 255, 255, 0.8)');
  gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.3)');
  gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 32, 32);
  const particleTexture = new THREE.CanvasTexture(spriteCanvas);

  const pMaterial = new THREE.PointsMaterial({
    map: particleTexture,
    size: 0.035,  // Global size multiplier
    transparent: true,
    opacity: 0.95,
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    depthTest: true,
    sizeAttenuation: true,
    fog: false  // Don't let fog hide particles
  });

  energyParticleSystem = new THREE.Points(geometry, pMaterial);
  scene.add(energyParticleSystem);

  // === ADD SOFT CYAN ATMOSPHERIC GLOW ===
  // Creates the volumetric light/mist effect behind and around the face
  // Keep alpha very low so it doesn't overpower tone mapping and turn the face black!
  // REMOVED for black background
  /*
  const glowCanvas = document.createElement('canvas');
  glowCanvas.width = 128;
  glowCanvas.height = 128;
  const gCtx = glowCanvas.getContext('2d');
  const gGradient = gCtx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gGradient.addColorStop(0, 'rgba(0, 180, 255, 0.08)'); // Extremely subtle center
  gGradient.addColorStop(0.4, 'rgba(0, 120, 255, 0.03)'); // Soft fade
  gGradient.addColorStop(1, 'rgba(0, 50, 150, 0)');
  gCtx.fillStyle = gGradient;
  gCtx.fillRect(0, 0, 128, 128);

  const glowTexture = new THREE.CanvasTexture(glowCanvas);
  const glowMaterial = new THREE.SpriteMaterial({
    map: glowTexture,
    color: 0xffffff,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    depthTest: true // Still occluded by the face if directly behind it
  });

  const atmosphericGlow = new THREE.Sprite(glowMaterial);
  // Scale it massively to cover the space behind the head
  atmosphericGlow.scale.set(headRadius * 8, headRadius * 8, 1);
  // Position it slightly behind the head center so it acts as a backdrop glow
  atmosphericGlow.position.set(headCenter.x, headCenter.y, headCenter.z - headRadius * 0.5);
  scene.add(atmosphericGlow);
  */
}

// ============================================================================
// Friday AI Backend WebSocket Integration
// ============================================================================

/**
 * Connects to the Friday Python backend WebSocket server.
 * Listens for state changes (idle, listening, thinking, speaking)
 * and drives the 3D avatar accordingly.
 */
function initFridayWebSocket() {
  const WS_URL = 'ws://localhost:8765';

  function connect() {
    // Clear any pending reconnect
    if (fridayReconnectTimer) {
      clearTimeout(fridayReconnectTimer);
      fridayReconnectTimer = null;
    }

    try {
      fridayWs = new WebSocket(WS_URL);
    } catch (e) {
      console.warn('[Friday WS] Failed to create WebSocket:', e);
      scheduleReconnect();
      return;
    }

    fridayWs.onopen = () => {
      console.log('[Friday WS] Connected to backend');
      updateFridayUI('idle', 'Connected. Awaiting wake word...');
      // Update backend status indicator
      const statusBackend = document.getElementById('status-backend');
      if (statusBackend) {
        statusBackend.querySelector('.status-indicator').className = 'status-indicator success';
      }
    };

    fridayWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const newState = data.state;
        const msgText = data.text;

        handleFridayStateChange(newState, msgText);
      } catch (e) {
        console.warn('[Friday WS] Failed to parse message:', e);
      }
    };

    fridayWs.onclose = () => {
      console.log('[Friday WS] Connection closed');
      updateFridayUI('offline', 'Backend disconnected. Reconnecting...');
      const statusBackend = document.getElementById('status-backend');
      if (statusBackend) {
        statusBackend.querySelector('.status-indicator').className = 'status-indicator offline';
      }
      scheduleReconnect();
    };

    fridayWs.onerror = (err) => {
      console.warn('[Friday WS] Connection error');
      // onclose will fire after this, which handles reconnect
    };
  }

  function scheduleReconnect() {
    if (!fridayReconnectTimer) {
      fridayReconnectTimer = setTimeout(() => {
        console.log('[Friday WS] Attempting reconnect...');
        connect();
      }, 2000);
    }
  }

  connect();
}

// ============================================================================
// Session Log — Hacker Terminal Feed
// ============================================================================

/**
 * Appends a new entry to the session log terminal.
 * @param {'user'|'friday'} who - Speaker identifier
 * @param {string} text - The message text
 */
function addSessionLog(who, text) {
  const terminal = document.getElementById('session-log-terminal');
  if (!terminal) return;

  const now = new Date();
  const timestamp = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const entry = document.createElement('div');
  entry.className = `session-log-entry ${who === 'user' ? 'user-entry' : 'friday-entry'}`;

  const whoLabel = who === 'user' ? 'YOU' : 'FRIDAY';
  entry.innerHTML = `
    <span class="session-entry-who">${whoLabel} <span style="opacity:0.4;font-weight:400;">[${timestamp}]</span></span>
    <span class="session-entry-text">${text}</span>
  `;

  terminal.appendChild(entry);
  // Auto-scroll to bottom
  terminal.scrollTop = terminal.scrollHeight;
}

// ============================================================================
// Hamburger Emotion Menu Toggle
// ============================================================================

function initEmotionMenu() {
  const toggle = document.getElementById('emotion-menu-toggle');
  const panel = document.getElementById('emotions-panel');
  const chevron = document.getElementById('emotion-chevron');

  if (!toggle || !panel) return;

  toggle.addEventListener('click', () => {
    const isOpen = panel.classList.toggle('open');
    toggle.classList.toggle('open', isOpen);
    if (chevron) chevron.classList.toggle('open', isOpen);
  });
}

// Clear session log button
function initSessionLog() {
  const clearBtn = document.getElementById('session-clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      const terminal = document.getElementById('session-log-terminal');
      if (terminal) {
        terminal.innerHTML = `
          <div class="session-log-boot">
            <span class="log-prefix">&gt;</span>
            <span class="log-boot-text">LOG CLEARED — AWAITING INTERACTION...</span>
          </div>`;
      }
    });
  }
}

/**
 * Handles a state change from the Friday backend.
 */
function handleFridayStateChange(newState, msgText) {
  const previousState = fridayState;
  fridayState = newState;

  // State-specific UI and avatar behavior
  switch (newState) {
    case 'idle':
      updateFridayUI('idle', 'Awaiting command.');
      // Hide speech overlay after a delay
      setTimeout(() => {
        if (fridayState === 'idle') {
          hideFridaySpeechOverlay();
        }
      }, 3000);
      break;

    case 'listening':
      updateFridayUI('listening', 'Listening...');
      break;

    case 'thinking':
      updateFridayUI('thinking', 'Processing...');
      // Log user query when we move to thinking (msgText carries the user query)
      if (msgText) {
        addSessionLog('user', msgText);
      }
      break;

    case 'speaking':
      updateFridayUI('speaking', 'Speaking...');
      fridaySpeakingStartTime = performance.now() / 1000;
      if (msgText) {
        showFridaySpeechOverlay(msgText);
        // Estimate how long the audio will play: ~0.06s per character + 0.3s padding
        fridayEstimatedSpeechDuration = (msgText.length * 0.06) + 0.3;
        // Log Friday's spoken response to the session terminal
        addSessionLog('friday', msgText);
      } else {
        fridayEstimatedSpeechDuration = 2.0; // fallback if no text
      }
      break;
  }
}

/**
 * Updates the Friday Status card in the sidebar.
 */
function updateFridayUI(state, subText) {
  const stateIcon = document.getElementById('friday-state-icon');
  const stateLabel = document.getElementById('friday-state-label');
  const stateSub = document.getElementById('friday-state-sub');

  if (stateIcon) {
    stateIcon.className = 'friday-state-icon state-' + state;
  }
  if (stateLabel) {
    stateLabel.textContent = state.toUpperCase();
  }
  if (stateSub && subText) {
    stateSub.textContent = subText;
  }
}

// ============================================================================
// Friday Speech Overlay (Typewriter Text Display)
// ============================================================================

/**
 * Shows Friday's spoken text with a typewriter animation.
 */
function showFridaySpeechOverlay(text) {
  const overlay = document.getElementById('friday-speech-overlay');
  const textEl = document.getElementById('friday-speech-text');
  if (!overlay || !textEl) return;

  // Cancel any ongoing typing
  if (fridayTypingTimer) clearTimeout(fridayTypingTimer);

  // Show the overlay
  overlay.classList.remove('hidden');
  textEl.textContent = '';
  textEl.classList.add('typing');

  let i = 0;
  function typeChar() {
    if (i < text.length) {
      textEl.textContent += text.charAt(i);
      // Auto-scroll
      textEl.scrollTop = textEl.scrollHeight;
      i++;
      fridayTypingTimer = setTimeout(typeChar, 22);
    } else {
      // Done typing
      textEl.classList.remove('typing');
    }
  }
  typeChar();
}

/**
 * Hides the speech overlay with a smooth fade-out.
 */
function hideFridaySpeechOverlay() {
  const overlay = document.getElementById('friday-speech-overlay');
  if (overlay) {
    overlay.classList.add('hidden');
  }
  if (fridayTypingTimer) {
    clearTimeout(fridayTypingTimer);
    fridayTypingTimer = null;
  }
}

// ============================================================================
// Friday State-Driven Procedural Lip-Sync
// ============================================================================

/**
 * Procedural mouth animation driven by the Friday backend's "speaking" state.
 * Uses layered sine waves at different frequencies to create natural-looking
 * mouth movement without needing actual audio data.
 */
function processFridayLipSync(elapsedTime) {
  if (manualSliderOverrides.has('jawOpen')) return;

  // Time since speaking started
  const speakTime = performance.now() / 1000 - fridaySpeakingStartTime;

  // Calculate fader to slowly stop mouth movement if we exceed the estimated audio duration.
  // This handles the fact that the backend keeps state in "speaking" 1.2s after audio finishes.
  let fader = 1.0;
  if (speakTime > fridayEstimatedSpeechDuration) {
    fader = Math.max(0, 1.0 - (speakTime - fridayEstimatedSpeechDuration) * 3.0); // Fade out quickly
  }

  // If fader is basically 0, force close the mouth
  if (fader <= 0.01) {
    targetMorphInfluences['jawOpen'] = 0;
    targetMorphInfluences['mouthFunnel'] = 0;
    targetMorphInfluences['mouthPucker'] = 0;
    targetMorphInfluences['mouthSmile_L'] = 0;
    targetMorphInfluences['mouthSmile_R'] = 0;
    targetMorphInfluences['mouthStretch_L'] = 0;
    targetMorphInfluences['mouthStretch_R'] = 0;
    targetMorphInfluences['mouthShrugUpper'] = 0;
    targetMorphInfluences['mouthLowerDown_L'] = 0;
    targetMorphInfluences['mouthLowerDown_R'] = 0;
    return;
  }

  // Layer 1: Primary jaw open/close rhythm (syllable-level)
  const jaw1 = Math.sin(speakTime * 12.0) * 0.3;
  const jaw2 = Math.sin(speakTime * 7.5 + 0.7) * 0.2;
  const jaw3 = Math.cos(speakTime * 18.0) * 0.1;

  // Combine and clamp to 0-0.6 range (natural jaw range)
  const jawValue = Math.max(0, Math.min(0.6, (jaw1 + jaw2 + jaw3 + 0.25)));

  targetMorphInfluences['jawOpen'] = jawValue * fader;

  // Layer 2: Mouth shape variation (simulates different phonemes)
  // These vary at different rates to create organic-looking speech
  const funnel = Math.max(0, Math.sin(speakTime * 9.0 + 1.2) * 0.2);
  const pucker = Math.max(0, Math.cos(speakTime * 11.0 + 0.5) * 0.15);
  const smileL = Math.max(0, Math.sin(speakTime * 5.0 + 2.0) * 0.12);
  const smileR = Math.max(0, Math.sin(speakTime * 5.0 + 2.0) * 0.12);
  const stretch = Math.max(0, Math.cos(speakTime * 8.0 + 3.0) * 0.1);
  const shrugUpper = Math.max(0, Math.sin(speakTime * 6.5) * 0.08);

  targetMorphInfluences['mouthFunnel'] = funnel * fader;
  targetMorphInfluences['mouthPucker'] = pucker * fader;
  targetMorphInfluences['mouthSmile_L'] = smileL * fader;
  targetMorphInfluences['mouthSmile_R'] = smileR * fader;
  targetMorphInfluences['mouthStretch_L'] = stretch * fader;
  targetMorphInfluences['mouthStretch_R'] = stretch * fader;
  targetMorphInfluences['mouthShrugUpper'] = shrugUpper * fader;

  // Layer 3: Subtle tongue and lower lip movement
  targetMorphInfluences['mouthLowerDown_L'] = jawValue * 0.3 * fader;
  targetMorphInfluences['mouthLowerDown_R'] = jawValue * 0.3 * fader;
}
