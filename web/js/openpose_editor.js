import { app } from "../../../../scripts/app.js";

/* ---------- constants (matching original OpenPoseEditor) ---------- */

const CONNECT = [[0,1],[1,2],[2,3],[3,4],[1,5],[5,6],[6,7],[1,8],[8,9],[9,10],[1,11],[11,12],[12,13],[14,0],[14,16],[15,0],[15,17]];

const COLORS = [
  [0,0,255],[255,0,0],[255,170,0],[255,255,0],[255,85,0],[170,255,0],[85,255,0],[0,255,0],
  [0,255,85],[0,255,170],[0,255,255],[0,170,255],[0,85,255],[85,0,255],[170,0,255],[255,0,255],[255,0,170],[255,0,85]
];

/* ---------- IK constants ---------- */

// 骨骼链定义（用于 IK 解算）
const BONE_CHAINS = {
  rightArm: [2, 3, 4],
  leftArm: [5, 6, 7],
  rightLeg: [8, 9, 10],
  leftLeg: [11, 12, 13],
};

// 末端关节（IK 末端效应器）
const END_EFFECTORS = new Set([4, 7, 10, 13]);

// 中间关节
const MID_JOINTS = new Set([3, 6, 9, 12]);

// 脖子是全局根
const NECK_IDX = 1;

// 骨骼父子关系
const PARENT_MAP = {
  0: 1, 1: null, 2: 1, 3: 2, 4: 3, 5: 1, 6: 5, 7: 6,
  8: 1, 9: 8, 10: 9, 11: 1, 12: 11, 13: 12,
  14: 0, 15: 0, 16: 14, 17: 15
};

// 关节名称
const JOINT_NAMES = {
  0: '鼻子', 1: '脖子', 2: '右肩', 3: '右肘', 4: '右腕',
  5: '左肩', 6: '左肘', 7: '左腕', 8: '右髋', 9: '右膝',
  10: '右踝', 11: '左髋', 12: '左膝', 13: '左踝',
  14: '右眼', 15: '左眼', 16: '右耳', 17: '左耳'
};

/* convert original 2D keypoints (512×512, y-down) to 3D (y-up) normalized to ~±0.5 */
function kp2dto3d(x2d, y2d) {
  const s = 1 / 470;
  return [(x2d - 256) * s, -(y2d - 256) * s, 0];
}

const _D = [
  [241,77],[241,120],[191,118],[177,183],[163,252],[298,118],[317,182],[332,245],
  [225,241],[213,359],[215,454],[270,240],[282,360],[286,456],[232,59],[253,60],[225,70],[260,72]
];
const DEF_PTS = _D.map(p => kp2dto3d(p[0], p[1]));

/* ---------- Three.js & OrbitControls lazy loader ---------- */

function loadThree(cb) {
  if (typeof THREE !== 'undefined') { 
    if (typeof THREE.OrbitControls !== 'undefined') {
      cb(); 
      return;
    }
    // Load OrbitControls if Three.js is available but OrbitControls is not
    const oc = document.createElement('script');
    oc.src = '/CJ-Nodes/js/OrbitControls.js';
    oc.onload = cb;
    oc.onerror = () => {
      console.warn('[PoseEditor] Failed to load OrbitControls, using basic controls');
      cb();
    };
    document.head.appendChild(oc);
    return;
  }
  const s = document.createElement('script');
  s.src = '/CJ-Nodes/js/three.min.js';
  s.onload = () => {
    const oc = document.createElement('script');
    oc.src = '/CJ-Nodes/js/OrbitControls.js';
    oc.onload = cb;
    oc.onerror = () => {
      console.warn('[PoseEditor] Failed to load OrbitControls, using basic controls');
      cb();
    };
    document.head.appendChild(oc);
  };
  s.onerror = () => console.error('[PoseEditor] Failed to load three.js');
  document.head.appendChild(s);
}

/* ---------- three scene ---------- */

function buildScene(container) {
  const w = 300;
  const h = 300;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a1a);

  const camera = new THREE.PerspectiveCamera(40, 1, 0.01, 20);
  camera.position.set(0, 0.3, 1.8);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  /* lights */
  scene.add(new THREE.AmbientLight(0x888888, 1.0));
  const dl = new THREE.DirectionalLight(0xffffff, 1.8); dl.position.set(1, 3, 1); scene.add(dl);
  const bl = new THREE.DirectionalLight(0x4488ff, 0.6); bl.position.set(-1, 0, -1); scene.add(bl);

  /* ground grid */
  const grid = new THREE.GridHelper(2.5, 12, 0x555555, 0x333333);
  grid.position.y = -0.55;
  scene.add(grid);

  /* shared geometry - smaller joints for adult proportion */
  const bodyJointGeo = new THREE.SphereGeometry(0.035, 10, 10);
  const headJointGeo = new THREE.SphereGeometry(0.02, 8, 8);

  let state = {
    scene, camera, renderer, bodyJointGeo, headJointGeo,
    people: [], nextId: 0,
    selPerson: null, selJoint: null, isDragging: false, draggingAll: false,
    hitPt: new THREE.Vector3(), dragOff: new THREE.Vector3(),
    dragAllStart: [], dragAllCamPlane: new THREE.Plane(),
    orbitActive: false, panMode: false,
    orbitStartX: 0, orbitStartY: 0, orbitStartTheta: 0, orbitStartPhi: 0,
    camTheta: 0, camPhi: 0.15, camDist: 1.8,
    camTarget: new THREE.Vector3(0, 0, 0),
    viewLocked: false, needsUpdate: false,
    previewEl: null, onUpdate: null,
    controls: null, useOrbitControls: false,
    boneLengths: {},
    showBoneLengths: true,
    boneLengthLabels: [],
    ikIterations: 10
  };

  // Try to use OrbitControls if available
  if (typeof THREE.OrbitControls !== 'undefined') {
    try {
      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.screenSpacePanning = true;
      controls.minDistance = 0.3;
      controls.maxDistance = 5;
      controls.maxPolarAngle = Math.PI;
      // Start with target at origin, will be updated when people are added
      controls.target.set(0, 0, 0);
      
      // Update camera info display when controls change
      controls.addEventListener('change', () => {
        updatePreview(state);
      });
      
      state.controls = controls;
      state.useOrbitControls = true;
      console.log('[PoseEditor] Using OrbitControls');
    } catch (e) {
      console.warn('[PoseEditor] Failed to initialize OrbitControls:', e);
    }
  }

  if (!state.useOrbitControls) {
    updateCam(state);
  }

  const ro = new ResizeObserver(() => {
    const r = container.getBoundingClientRect();
    if (r.width > 10 && r.height > 10) {
      camera.aspect = r.width / r.height;
      camera.updateProjectionMatrix();
      renderer.setSize(r.width, r.height);
    }
  });
  ro.observe(container);
  state.ro = ro;

  setupInput(state, container, () => {
    if (state.needsUpdate) { state.needsUpdate = false; sendUpdate(state); }
  });

  (function anim() {
    requestAnimationFrame(anim);
    if (state.controls && state.useOrbitControls) {
      state.controls.update();
    }
    renderer.render(scene, camera);
  })();

  return state;
}

function updateCam(st, target) {
  const x = st.camDist * Math.sin(st.camTheta) * Math.cos(st.camPhi);
  const y = st.camDist * Math.sin(st.camPhi);
  const z = st.camDist * Math.cos(st.camTheta) * Math.cos(st.camPhi);
  if (!target) target = { x: 0, y: 0, z: 0 };
  st.camera.position.set(target.x + x, target.y + y, target.z + z);
  st.camera.lookAt(target.x, target.y, target.z);
}

/* ---------- joints / bones ---------- */

// Head joint indices: 0 (nose), 14 (right eye), 15 (left eye), 16 (right ear), 17 (left ear)
const HEAD_INDICES = new Set([0, 14, 15, 16, 17]);

function createJoint(st, pos, colorIdx) {
  const c = COLORS[colorIdx] || [255,255,255];
  const mat = new THREE.MeshStandardMaterial({
    color: (c[0]<<16)|(c[1]<<8)|c[2],
    emissive: (c[0]<<16)|(c[1]<<8)|c[2],
    emissiveIntensity: 0.15,
    roughness: 0.3
  });
  const geo = HEAD_INDICES.has(colorIdx) ? st.headJointGeo : st.bodyJointGeo;
  const m = new THREE.Mesh(geo, mat);
  m.position.copy(pos);
  m.userData.isJoint = true;
  m.userData.jointIdx = colorIdx;
  m.raycast = THREE.Mesh.prototype.raycast;
  st.scene.add(m);

  // 为脖子关节添加方向圆锥体
  if (colorIdx === 1) {
    const coneGeo = new THREE.ConeGeometry(0.025, 0.08, 8);
    const coneMat = new THREE.MeshStandardMaterial({
      color: 0xff4444,
      emissive: 0xff4444,
      emissiveIntensity: 0.3,
      roughness: 0.4
    });
    const cone = new THREE.Mesh(coneGeo, coneMat);
    cone.rotation.x = Math.PI / 2;
    cone.position.set(0, 0, 0.06);
    m.add(cone);
    st.neckDirectionCone = cone;
  }

  return m;
}

function createBone(st, posA, posB, colorIdx) {
  const dir = new THREE.Vector3().subVectors(posB, posA);
  const len = dir.length();
  if (len < 0.001) return null;
  dir.normalize();

  const c = COLORS[colorIdx] || [255,255,255];
  const mat = new THREE.MeshStandardMaterial({
    color: (c[0]<<16)|(c[1]<<8)|c[2],
    transparent: true, opacity: 0.6, roughness: 0.5
  });

  /* cylinder along Y, shift so bottom at origin - thinner bones for adult proportion */
  const geo = new THREE.CylinderGeometry(0.012, 0.012, len, 6);
  geo.translate(0, len / 2, 0);

  const m = new THREE.Mesh(geo, mat);
  m.position.copy(posA);

  const up = new THREE.Vector3(0, 1, 0);
  m.quaternion.setFromUnitVectors(up, dir);

  st.scene.add(m);
  return m;
}

/* ---------- person management ---------- */

function addPerson(st, kp4d) {
  if (st.people.length) [...st.people].forEach(p => removePerson(st, p));
  st.nextId = 0;
  const pid = st.nextId++;
  const data = kp4d || getDefaultKp4d();
  const joints = [];
  const meshes = [];

  for (let i = 0; i < 18; i++) {
    const x = data[i*4], y = data[i*4+1], z = data[i*4+2]||0, conf = data[i*4+3]||1;
    if (!conf) { joints.push(null); continue; }
    const pos = new THREE.Vector3(x, y, z);
    const mesh = createJoint(st, pos, i);
    meshes.push(mesh);
    joints.push({ idx: i, mesh, pos });
  }

  CONNECT.forEach(pair => {
    const a = joints[pair[0]], b = joints[pair[1]];
    if (!a || !b) return;
    const bone = createBone(st, a.mesh.position, b.mesh.position, pair[0]);
    if (bone) meshes.push(bone);
  });

  const person = { id: pid, joints: joints.filter(j => j), meshes };
  st.people.push(person);
  st.boneLengths = calcBoneLengths(st, person);
  createBoneLengthLabels(st, person);
  return person;
}

function rebuildBones(st, person) {
  const keep = [];
  person.meshes.forEach(m => {
    if (m.userData.isJoint) keep.push(m);
    else { st.scene.remove(m); m.geometry.dispose(); m.material.dispose(); }
  });
  person.meshes = keep;

  const map = {};
  person.joints.forEach(j => { map[j.idx] = j; });

  CONNECT.forEach(pair => {
    const a = map[pair[0]], b = map[pair[1]];
    if (!a || !b) return;
    const bone = createBone(st, a.mesh.position, b.mesh.position, pair[0]);
    if (bone) person.meshes.push(bone);
  });

  updateBoneLengthLabels(st, person);
  updateDirectionCone(st, person);
}

function updateDirectionCone(st, person) {
  const neck = person.joints.find(j => j.idx === 1);
  const nose = person.joints.find(j => j.idx === 0);
  if (!neck || !nose || !st.neckDirectionCone) return;

  const neckPos = neck.mesh.position;
  const nosePos = nose.mesh.position;
  
  const dir = new THREE.Vector3().subVectors(nosePos, neckPos).normalize();
  
  st.neckDirectionCone.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 0, 1),
    dir
  );
}

function removePerson(st, person) {
  person.meshes.forEach(m => { st.scene.remove(m); m.geometry.dispose(); m.material.dispose(); });
  const i = st.people.indexOf(person);
  if (i >= 0) st.people.splice(i, 1);
}

function clearAll(st) {
  [...st.people].forEach(p => removePerson(st, p));
  st.nextId = 0; st.selJoint = null; st.selPerson = null;
}

function getDefaultKp4d() {
  const out = [];
  DEF_PTS.forEach(p => out.push(p[0], p[1], p[2], 1.0));
  return out;
}

/* ---------- IK system ---------- */

function calcBoneLengths(st, person) {
  const lengths = {};
  for (const [chainName, chain] of Object.entries(BONE_CHAINS)) {
    for (let i = 0; i < chain.length - 1; i++) {
      const a = person.joints.find(j => j.idx === chain[i]);
      const b = person.joints.find(j => j.idx === chain[i + 1]);
      if (a && b) {
        const key = `${chain[i]}_${chain[i+1]}`;
        lengths[key] = a.mesh.position.distanceTo(b.mesh.position);
      }
    }
  }
  const lHip = person.joints.find(j => j.idx === 11);
  const rHip = person.joints.find(j => j.idx === 8);
  if (lHip && rHip) {
    lengths['hip_width'] = lHip.mesh.position.distanceTo(rHip.mesh.position);
  }
  return lengths;
}

function fabrikSolve(person, targetIdx, targetPos, boneLengths) {
  let chain = null;
  for (const [name, indices] of Object.entries(BONE_CHAINS)) {
    if (indices.includes(targetIdx)) {
      chain = indices;
      break;
    }
  }
  if (!chain) return;

  const joints = chain.map(idx => person.joints.find(j => j.idx === idx)).filter(Boolean);
  if (joints.length < 2) return;

  const lengths = [];
  for (let i = 0; i < joints.length - 1; i++) {
    const key = `${chain[i]}_${chain[i+1]}`;
    lengths.push(boneLengths[key] || joints[i].mesh.position.distanceTo(joints[i+1].mesh.position));
  }

  const positions = joints.map(j => j.mesh.position.clone());
  const rootPos = positions[0].clone();

  for (let iter = 0; iter < 10; iter++) {
    positions[positions.length - 1].copy(targetPos);
    for (let i = positions.length - 2; i >= 0; i--) {
      const dir = new THREE.Vector3().subVectors(positions[i], positions[i + 1]).normalize();
      positions[i].copy(positions[i + 1]).add(dir.multiplyScalar(lengths[i]));
    }
    positions[0].copy(rootPos);
    for (let i = 1; i < positions.length; i++) {
      const dir = new THREE.Vector3().subVectors(positions[i], positions[i - 1]).normalize();
      positions[i].copy(positions[i - 1]).add(dir.multiplyScalar(lengths[i - 1]));
    }
  }

  for (let i = 1; i < joints.length; i++) {
    joints[i].mesh.position.copy(positions[i]);
  }
}

function maintainHipWidth(person, boneLengths) {
  const lHip = person.joints.find(j => j.idx === 11);
  const rHip = person.joints.find(j => j.idx === 8);
  if (!lHip || !rHip) return;

  const targetDist = boneLengths['hip_width'] || 0.2;
  const currentDist = lHip.mesh.position.distanceTo(rHip.mesh.position);

  if (Math.abs(currentDist - targetDist) > 0.001) {
    const center = new THREE.Vector3().addVectors(lHip.mesh.position, rHip.mesh.position).multiplyScalar(0.5);
    const dir = new THREE.Vector3().subVectors(rHip.mesh.position, lHip.mesh.position).normalize();
    rHip.mesh.position.copy(center).add(dir.multiplyScalar(targetDist / 2));
    lHip.mesh.position.copy(center).sub(dir.multiplyScalar(targetDist / 2));
  }
}

function applyIKConstraint(st, person, draggedIdx, newPos) {
  const neck = person.joints.find(j => j.idx === NECK_IDX);
  if (!neck) return;

  if (draggedIdx === NECK_IDX) {
    const delta = new THREE.Vector3().subVectors(newPos, neck.mesh.position);
    person.joints.forEach(j => j.mesh.position.add(delta));
  } else if (END_EFFECTORS.has(draggedIdx)) {
    fabrikSolve(person, draggedIdx, newPos, st.boneLengths);
  } else if (MID_JOINTS.has(draggedIdx)) {
    const parent = person.joints.find(j => j.idx === PARENT_MAP[draggedIdx]);
    let childIdx = null;
    for (const [name, chain] of Object.entries(BONE_CHAINS)) {
      const idx = chain.indexOf(draggedIdx);
      if (idx >= 0 && idx < chain.length - 1) {
        childIdx = chain[idx + 1];
        break;
      }
    }
    const child = childIdx !== null ? person.joints.find(j => j.idx === childIdx) : null;

    if (parent) {
      const parentKey = `${PARENT_MAP[draggedIdx]}_${draggedIdx}`;
      const dist = st.boneLengths[parentKey] || parent.mesh.position.distanceTo(newPos);
      const dir = new THREE.Vector3().subVectors(newPos, parent.mesh.position).normalize();
      newPos.copy(parent.mesh.position).add(dir.multiplyScalar(dist));
    }

    person.joints.find(j => j.idx === draggedIdx).mesh.position.copy(newPos);

    if (child) {
      const childKey = `${draggedIdx}_${child.idx}`;
      const dist = st.boneLengths[childKey] || newPos.distanceTo(child.mesh.position);
      const dir = new THREE.Vector3().subVectors(child.mesh.position, newPos).normalize();
      child.mesh.position.copy(newPos).add(dir.multiplyScalar(dist));
    }
  } else {
    person.joints.find(j => j.idx === draggedIdx).mesh.position.copy(newPos);
  }

  maintainHipWidth(person, st.boneLengths);
}

/* ---------- bone length visualization ---------- */

function createBoneLengthLabels(st, person) {
  clearBoneLengthLabels(st);
  if (!st.showBoneLengths) return;

  for (const [chainName, chain] of Object.entries(BONE_CHAINS)) {
    for (let i = 0; i < chain.length - 1; i++) {
      const a = person.joints.find(j => j.idx === chain[i]);
      const b = person.joints.find(j => j.idx === chain[i + 1]);
      if (a && b) {
        const midPos = new THREE.Vector3().addVectors(a.mesh.position, b.mesh.position).multiplyScalar(0.5);
        const key = `${chain[i]}_${chain[i+1]}`;
        const len = st.boneLengths[key] || a.mesh.position.distanceTo(b.mesh.position);
        const label = createTextLabel(st, `${JOINT_NAMES[chain[i]]}-${JOINT_NAMES[chain[i+1]]}: ${len.toFixed(2)}`, midPos, key);
        label.userData.jointA = chain[i];
        label.userData.jointB = chain[i + 1];
        st.boneLengthLabels.push(label);
      }
    }
  }

  const lHip = person.joints.find(j => j.idx === 11);
  const rHip = person.joints.find(j => j.idx === 8);
  if (lHip && rHip) {
    const midPos = new THREE.Vector3().addVectors(lHip.mesh.position, rHip.mesh.position).multiplyScalar(0.5);
    const len = st.boneLengths['hip_width'] || lHip.mesh.position.distanceTo(rHip.mesh.position);
    const label = createTextLabel(st, `腰宽: ${len.toFixed(2)}`, midPos, 'hip_width');
    label.userData.jointA = 11;
    label.userData.jointB = 8;
    st.boneLengthLabels.push(label);
  }
}

function clearBoneLengthLabels(st) {
  st.boneLengthLabels.forEach(label => {
    st.scene.remove(label);
    if (label.material) label.material.dispose();
    if (label.material.map) label.material.map.dispose();
  });
  st.boneLengthLabels = [];
}

function updateBoneLengthLabels(st, person) {
  if (!st.showBoneLengths) return;

  st.boneLengthLabels.forEach(label => {
    const a = person.joints.find(j => j.idx === label.userData.jointA);
    const b = person.joints.find(j => j.idx === label.userData.jointB);
    if (a && b) {
      label.position.lerpVectors(a.mesh.position, b.mesh.position, 0.5);
      const len = a.mesh.position.distanceTo(b.mesh.position);
      const nameA = JOINT_NAMES[label.userData.jointA] || '';
      const nameB = JOINT_NAMES[label.userData.jointB] || '';
      const prefix = label.userData.key === 'hip_width' ? '腰宽' : `${nameA}-${nameB}`;
      updateTextLabel(label, `${prefix}: ${len.toFixed(2)}`);
    }
  });
}

function createTextLabel(st, text, position, key) {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
  ctx.roundRect(0, 0, 256, 64, 4);
  ctx.fill();
  ctx.fillStyle = '#00ff88';
  ctx.font = 'bold 20px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 32);

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, depthTest: false });
  const sprite = new THREE.Sprite(material);
  sprite.position.copy(position);
  sprite.scale.set(0.15, 0.04, 1);
  sprite.userData.key = key;
  sprite.userData.canvas = canvas;
  sprite.userData.texture = texture;
  st.scene.add(sprite);
  return sprite;
}

function updateTextLabel(sprite, text) {
  const canvas = sprite.userData.canvas;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 256, 64);
  ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
  ctx.roundRect(0, 0, 256, 64, 4);
  ctx.fill();
  ctx.fillStyle = '#00ff88';
  ctx.font = 'bold 20px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 32);
  sprite.userData.texture.needsUpdate = true;
}

/* ---------- pose commands ---------- */

function getPeopleBounds(st) {
  const box = new THREE.Box3();
  st.people.forEach(p => {
    p.joints.forEach(j => {
      box.expandByPoint(j.mesh.position);
    });
  });
  return box;
}

function centerCameraOnPeople(st) {
  if (st.people.length === 0) return;
  
  const box = getPeopleBounds(st);
  const center = new THREE.Vector3();
  box.getCenter(center);
  
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.y, size.z);
  
  // Calculate appropriate camera distance
  const fov = st.camera.fov * (Math.PI / 180);
  let distance = (maxDim / 2) / Math.tan(fov / 2) * 1.5;
  distance = Math.max(0.5, Math.min(3, distance));
  
  if (st.controls && st.useOrbitControls) {
    // Set orbit target to model center - rotation will be around the model
    st.controls.target.copy(center);
    // Position camera at an angle to see the full pose
    st.camera.position.set(
      center.x,
      center.y + distance * 0.3,
      center.z + distance
    );
    st.controls.update();
  } else {
    st.camTarget.copy(center);
    st.camDist = distance;
    updateCam(st, st.camTarget);
  }
}

function resetPoseState(st) {
  clearAll(st);
  addPerson(st);
  
  // Center camera on the new person
  centerCameraOnPeople(st);
  
  updatePreview(st);
  st.needsUpdate = true;
}

function flipPoseState(st) {
  st.people.forEach(p => {
    p.joints.forEach(j => { j.mesh.position.x = -j.mesh.position.x; });
    rebuildBones(st, p);
  });
  updatePreview(st); st.needsUpdate = true;
}

function rotatePoseState(st, deg) {
  const rad = deg * Math.PI / 180;
  const cos = Math.cos(rad), sin = Math.sin(rad);
  st.people.forEach(p => {
    p.joints.forEach(j => {
      const x = j.mesh.position.x, z = j.mesh.position.z || 0;
      j.mesh.position.x = x * cos - z * sin;
      j.mesh.position.z = x * sin + z * cos;
    });
    rebuildBones(st, p);
  });
  updatePreview(st); st.needsUpdate = true;
}

/* ---------- posture text analysis (enhanced with 3D vector analysis) ---------- */

function analyzePerson(joints) {
  const p = {};
  joints.forEach(j => { p[j.idx] = j.mesh.position; });
  const parts = [];

  const vecLen = (v) => Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
  const vecNorm = (v) => {
    const len = vecLen(v);
    return len > 0 ? { x: v.x / len, y: v.y / len, z: v.z / len } : { x: 0, y: 1, z: 0 };
  };
  const getCenter = (p1, p2) => p1 && p2 ? {
    x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2, z: (p1.z + p2.z) / 2
  } : null;
  const calcAngle = (v1, v2) => {
    const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
    const l1 = vecLen(v1), l2 = vecLen(v2);
    if (l1 === 0 || l2 === 0) return 0;
    return Math.acos(Math.min(1, Math.max(-1, dot / (l1 * l2)))) * 180 / Math.PI;
  };

  // ========== 1. 基本姿势（站立/坐姿/蹲姿/躺姿）==========
  const shoulderCenter = getCenter(p[2], p[5]);
  const hipCenter = getCenter(p[8], p[11]);
  
  if (shoulderCenter && hipCenter && p[1]) {
    const spineVector = {
      x: p[1].x - hipCenter.x, y: p[1].y - hipCenter.y, z: p[1].z - hipCenter.z
    };
    const spineLen = vecLen(spineVector);
    
    if (spineLen > 0) {
      const spineDir = vecNorm(spineVector);
      const verticalAngle = Math.acos(Math.abs(spineDir.y)) * 180 / Math.PI;
      
      const avgAnkleY = ((p[10] ? p[10].y : 0) + (p[13] ? p[13].y : 0)) / 2;
      const hipHeight = hipCenter.y - avgAnkleY;
      const bodyHeight = spineLen;
      
      if (verticalAngle < 45) {
        if (spineDir.z < -0.6) {
          parts.push("身体大幅后仰");
        } else if (spineDir.z > 0.6) {
          parts.push(hipHeight < bodyHeight * 0.3 ? "坐姿身体前倾" : "站立身体前倾");
        } else if (spineDir.z < -0.3) {
          parts.push("身体微微后仰");
        } else if (spineDir.z > 0.3) {
          parts.push("身体微微前倾");
        } else {
          if (hipHeight < bodyHeight * 0.3) {
            const avgKneeY = ((p[9] ? p[9].y : 0) + (p[12] ? p[12].y : 0)) / 2;
            if (avgKneeY > hipCenter.y + 0.05) {
              if (p[10] && p[13] && p[9] && p[12]) {
                const legsCrossed = (p[10].x > p[12].x && p[13].x < p[9].x) ||
                                   (p[13].x > p[9].x && p[10].x < p[12].x);
                parts.push(legsCrossed ? "盘腿坐姿" : "跪坐姿势");
              } else {
                parts.push("坐姿");
              }
            } else {
              parts.push("坐姿");
            }
          } else if (hipHeight < bodyHeight * 0.6) {
            parts.push("蹲姿");
          } else {
            parts.push("标准站立");
          }
        }
      } else if (verticalAngle > 75) {
        const shoulderHipDiff = shoulderCenter.y - hipCenter.y;
        if (shoulderHipDiff > 0.2) parts.push("仰卧姿势");
        else if (shoulderHipDiff < -0.2) parts.push("俯卧姿势");
        else parts.push("侧卧姿势");
      } else {
        if (spineDir.z < -0.5) parts.push("身体大幅度后仰倾斜");
        else if (spineDir.z > 0.5) parts.push("身体大幅度前倾倾斜");
        else if (spineDir.z < -0.2) parts.push("身体后仰倾斜");
        else if (spineDir.z > 0.2) parts.push("身体前倾倾斜");
        else parts.push("身体倾斜姿态");
      }
    }
  }

  // ========== 2. 手臂动作（详细分析）==========
  const analyzeArm = (shoulder, elbow, wrist, side) => {
    if (!shoulder || !elbow || !wrist) return;
    
    const upperArmRel = { x: elbow.x - shoulder.x, y: elbow.y - shoulder.y, z: elbow.z - shoulder.z };
    const forearmRel = { x: wrist.x - elbow.x, y: wrist.y - elbow.y, z: wrist.z - elbow.z };
    const wristRel = { x: wrist.x - shoulder.x, y: wrist.y - shoulder.y, z: wrist.z - shoulder.z };
    const wristLen = vecLen(wristRel);
    
    if (wristLen > 0) {
      const wristDir = vecNorm(wristRel);
      
      if (wristDir.y > 0.6) parts.push(`${side}手高举过头顶`);
      else if (wristDir.y > 0.3) parts.push(`${side}手举起`);
      else if (wristDir.y < -0.6) parts.push(`${side}手自然下垂`);
      else if (wristDir.y < -0.3) parts.push(`${side}手放下`);
      
      if (wristDir.z > 0.3) parts.push(`${side}手向前伸展`);
      else if (wristDir.z > 0.1) parts.push(`${side}手在身体前面`);
      else if (wristDir.z < -0.3) parts.push(`${side}手向后伸展`);
      else if (wristDir.z < -0.1) parts.push(`${side}手在身体后面`);
      
      if (Math.abs(wristDir.x) > 0.3) parts.push(`${side}手向外侧伸展`);
    }
    
    const upperArmLen = vecLen(upperArmRel);
    const forearmLen = vecLen(forearmRel);
    if (upperArmLen > 0 && forearmLen > 0) {
      const elbowAngle = calcAngle(vecNorm(upperArmRel), vecNorm(forearmRel));
      if (elbowAngle < 45) parts.push(`${side}手臂弯曲`);
      else if (elbowAngle > 135) parts.push(`${side}手臂伸直`);
    }
  };
  
  analyzeArm(p[2], p[3], p[4], "右");
  analyzeArm(p[5], p[6], p[7], "左");

  // ========== 3. 腿部动作（详细分析）==========
  const analyzeLeg = (hip, knee, ankle, side) => {
    if (!hip || !knee || !ankle) return;
    
    const kneeLocal = { x: knee.x - hip.x, y: knee.y - hip.y, z: knee.z - hip.z };
    const ankleLocal = { x: ankle.x - knee.x, y: ankle.y - knee.y, z: ankle.z - knee.z };
    
    const kneeLen = vecLen(kneeLocal);
    if (kneeLen > 0) {
      const kneeDir = vecNorm(kneeLocal);
      if (kneeDir.z > 0.7) parts.push(`${side}腿膝盖大幅抬起`);
      else if (kneeDir.z > 0.4) parts.push(`${side}腿膝盖抬起`);
      else if (kneeDir.z > 0.2) parts.push(`${side}腿膝盖微微抬起`);
      
      if (kneeDir.y < -0.3) parts.push(`${side}腿弯曲`);
      else if (kneeDir.y > 0.3) parts.push(`${side}腿伸直`);
    }
    
    const footLen = Math.sqrt(ankleLocal.y * ankleLocal.y + ankleLocal.z * ankleLocal.z);
    if (footLen > 0) {
      const footDirY = ankleLocal.y / footLen;
      const footDirZ = ankleLocal.z / footLen;
      if (footDirY > 0.7) parts.push(`${side}脚大幅抬起`);
      else if (footDirY > 0.4) parts.push(`${side}脚抬起`);
      if (footDirZ > 0.3) parts.push(`${side}脚向前伸`);
      else if (footDirZ < -0.3) parts.push(`${side}脚向后伸`);
    }
  };
  
  analyzeLeg(p[8], p[9], p[10], "右");
  analyzeLeg(p[11], p[12], p[13], "左");

  // ========== 4. 双腿分开程度 ==========
  if (p[9] && p[12] && p[8] && p[11]) {
    const leftKneeRel = { x: p[9].x - p[8].x, y: p[9].y - p[8].y, z: p[9].z - p[8].z };
    const rightKneeRel = { x: p[12].x - p[11].x, y: p[12].y - p[11].y, z: p[12].z - p[11].z };
    const kneeDistanceX = Math.abs(leftKneeRel.x - rightKneeRel.x);
    
    if (kneeDistanceX > 0.25) parts.push("双腿大幅分开站立");
    else if (kneeDistanceX > 0.17) parts.push("双腿分开站立");
    else if (kneeDistanceX > 0.08) parts.push("双腿微微分开");
    else if (kneeDistanceX < 0.03) parts.push("双腿并拢站立");
  }

  // ========== 5. 头部方向和倾斜 ==========
  if (p[0] && p[1]) {
    const headTilt = Math.abs(p[0].x - p[1].x);
    if (headTilt > 0.06) parts.push(p[0].x > p[1].x ? "头部向右倾斜" : "头部向左倾斜");
    else if (headTilt > 0.03) parts.push(p[0].x > p[1].x ? "头部微微右偏" : "头部微微左偏");
    
    const headZ = p[0].z - p[1].z;
    if (headZ > 0.03) parts.push("头部向前伸");
    else if (headZ < -0.03) parts.push("头部向后仰");
  }

  // ========== 6. 重心分布 ==========
  if (p[10] && p[13] && p[8] && p[11]) {
    const leftWeight = p[10].x - p[8].x;
    const rightWeight = p[13].x - p[11].x;
    if (Math.abs(leftWeight - rightWeight) > 0.1) {
      parts.push(leftWeight > rightWeight ? "重心偏向左侧" : "重心偏向右侧");
    }
  }

  return parts.length ? parts.join("，") : "标准站立姿势";
}

function updatePreview(st) {
  let el = st.previewEl;
  if (!el && st.node) el = st.node.querySelector('.cj-pose-preview');
  if (!el) return;
  if (!st.people.length) { el.textContent = "未检测到人物"; return; }
  const txt = analyzePerson(st.people[0].joints);
  if (el.textContent !== txt) el.textContent = txt;
  
  // Update camera prompt display (show description instead of angles)
  const angles = calcCameraAngles(st);
  const cameraPrompt = generateCameraPrompt(angles.horizontal, angles.vertical, angles.zoom);
  const camEl = document.getElementById('cj-camera-prompt');
  if (camEl) camEl.textContent = cameraPrompt;
  
  // Sync data to backend so output matches frontend display
  if (st.onUpdate) st.onUpdate(serializeState(st));
}

/* ---------- serialization ---------- */

function serializeState(st) {
  const all = [];
  st.people.forEach(p => {
    const kp = new Array(72).fill(0);
    p.joints.forEach(j => {
      const pos = j.mesh.position;
      kp[j.idx * 4] = pos.x;
      kp[j.idx * 4 + 1] = pos.y;
      kp[j.idx * 4 + 2] = pos.z || 0;
      kp[j.idx * 4 + 3] = 1;
    });
    all.push({ pose_keypoints_3d: kp });
  });
  
  // Include posture description from frontend analysis
  const postureDesc = st.people.length > 0 ? analyzePerson(st.people[0].joints) : "";
  
  // Get camera info and angles
  const cam = st.camera;
  const cameraInfo = {
    position: { x: cam.position.x, y: cam.position.y, z: cam.position.z },
    target: { x: st.controls?.target?.x || 0, y: st.controls?.target?.y || 0, z: st.controls?.target?.z || 0 }
  };
  
  const angles = calcCameraAngles(st);
  const cameraPrompt = generateCameraPrompt(angles.horizontal, angles.vertical, angles.zoom);
  
  return JSON.stringify({ 
    width: 1024, 
    height: 1024, 
    people: all,
    posture_description: postureDesc,
    camera: cameraInfo,
    camera_angles: angles,
    camera_prompt: cameraPrompt
  });
}

function sendUpdate(st) {
  if (st.onUpdate) st.onUpdate(serializeState(st));
}

/* ---------- camera angle calculation ---------- */

function calcCameraAngles(st) {
  const cam = st.camera;
  const target = st.controls?.target || new THREE.Vector3(0, 0, 0);
  
  // 计算相机相对于目标的向量
  const dx = cam.position.x - target.x;
  const dy = cam.position.y - target.y;
  const dz = cam.position.z - target.z;
  
  // 计算相机距离（zoom）
  const zoom = Math.sqrt(dx * dx + dy * dy + dz * dz);
  
  // 计算水平角度 (0-360, 正面dz方向为0°, 顺时针增加)
  // atan2(x, z) 给出从z轴正方向逆时针到向量的角度
  let h_angle = Math.atan2(dx, dz) * (180 / Math.PI);
  h_angle = ((h_angle % 360) + 360) % 360; // 转换为0-360
  
  // 计算垂直角度 (-90到90, 0为水平, 正值为仰视)
  const distXZ = Math.sqrt(dx * dx + dz * dz);
  let v_angle = Math.atan2(dy, distXZ) * (180 / Math.PI);
  
  return {
    horizontal: Math.round(h_angle),
    vertical: Math.round(v_angle),
    zoom: Math.round(zoom * 10) / 10
  };
}

function generateCameraPrompt(h_angle, v_angle, zoom) {
  // 水平方向 - 使用更精细的分类
  const h = ((h_angle % 360) + 360) % 360;
  let h_direction;
  if (h < 15 || h >= 345) h_direction = "front view";
  else if (h < 45) h_direction = "front-right quarter view";
  else if (h < 75) h_direction = "right-front view";
  else if (h < 105) h_direction = "right side view";
  else if (h < 135) h_direction = "right-back view";
  else if (h < 165) h_direction = "back-right quarter view";
  else if (h < 195) h_direction = "back view";
  else if (h < 225) h_direction = "back-left quarter view";
  else if (h < 255) h_direction = "left-back view";
  else if (h < 285) h_direction = "left side view";
  else if (h < 315) h_direction = "left-front view";
  else h_direction = "front-left quarter view";
  
  // 垂直方向 - 使用更精细的分类
  let v_direction;
  if (v_angle < -30) v_direction = "extreme low angle";
  else if (v_angle < -15) v_direction = "low angle";
  else if (v_angle < -5) v_direction = "slightly low angle";
  else if (v_angle < 5) v_direction = "eye level";
  else if (v_angle < 15) v_direction = "slightly high angle";
  else if (v_angle < 30) v_direction = "high angle";
  else if (v_angle < 60) v_direction = "elevated angle";
  else if (v_angle < 80) v_direction = "bird's eye view";
  else v_direction = "top-down view";
  
  // 远近 - 使用更精细的分类
  let distance;
  if (zoom < 1) distance = "extreme close-up";
  else if (zoom < 2) distance = "close-up";
  else if (zoom < 3) distance = "medium close-up";
  else if (zoom < 5) distance = "medium shot";
  else if (zoom < 7) distance = "medium-wide shot";
  else if (zoom < 9) distance = "wide shot";
  else distance = "extreme wide shot";
  
  return `${h_direction}, ${v_direction}, ${distance}`;
}

/* ---------- input ---------- */

function setupInput(st, container, onDragEnd) {
  const el = st.renderer.domElement;
  const ray = new THREE.Raycaster();
  const mp = new THREE.Vector2();

  function getHits(ev) {
    const rect = el.getBoundingClientRect();
    mp.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    mp.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    ray.setFromCamera(mp, st.camera);
    const meshes = [];
    st.people.forEach(p => p.joints.forEach(j => meshes.push(j.mesh)));
    return ray.intersectObjects(meshes);
  }

  // Use pointerdown for better compatibility
  el.addEventListener('pointerdown', (ev) => {
    if (ev.button === 0) {
      const hits = getHits(ev);
      if (hits.length > 0) {
        ev.preventDefault();
        ev.stopPropagation();
        
        // Disable OrbitControls while dragging a joint
        if (st.controls && st.useOrbitControls) {
          st.controls.enabled = false;
        }
        
        const mesh = hits[0].object;
        for (const p of st.people) {
          for (const j of p.joints) {
            if (j.mesh === mesh) {
              st.selPerson = p;
              st.selJoint = { person: p, joint: j, mesh };
              st.isDragging = true;

              if (ev.shiftKey) {
                /* Shift+drag: translate entire person */
                st.draggingAll = true;
                st.dragAllStart = [];
                p.joints.forEach(jj => st.dragAllStart.push(jj.mesh.position.clone()));
                const cd = new THREE.Vector3().subVectors(st.camera.position, mesh.position).normalize();
                st.dragAllCamPlane.setFromNormalAndCoplanarPoint(cd, mesh.position);
                ray.ray.intersectPlane(st.dragAllCamPlane, st.hitPt);
                if (st.hitPt) st.dragOff.copy(st.hitPt);
              } else {
                /* normal drag: move single joint */
                st.draggingAll = false;
                const cd = new THREE.Vector3().subVectors(st.camera.position, mesh.position).normalize();
                const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(cd, mesh.position);
                ray.ray.intersectPlane(plane, st.hitPt);
                if (st.hitPt) st.dragOff.copy(mesh.position).sub(st.hitPt);
                mesh.material.emissiveIntensity = 0.8;
              }
              return;
            }
          }
        }
      }
    }
    /* OrbitControls handles orbit when clicking on empty space */
  }, { capture: true });

  el.addEventListener('pointermove', (ev) => {
    if (st.isDragging && st.selJoint) {
      ev.preventDefault();
      
      const rect = el.getBoundingClientRect();
      mp.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
      mp.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
      ray.setFromCamera(mp, st.camera);

      if (st.draggingAll) {
        if (ray.ray.intersectPlane(st.dragAllCamPlane, st.hitPt)) {
          const delta = new THREE.Vector3().subVectors(st.hitPt, st.dragOff);
          st.selPerson.joints.forEach((jj, i) => { jj.mesh.position.copy(st.dragAllStart[i]).add(delta); });
          rebuildBones(st, st.selPerson);
        }
      } else {
        const camDir = new THREE.Vector3().subVectors(st.camera.position, st.selJoint.mesh.position).normalize();
        const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(camDir, st.selJoint.mesh.position);
        if (ray.ray.intersectPlane(plane, st.hitPt)) {
          const newPos = st.hitPt.clone().add(st.dragOff);
          applyIKConstraint(st, st.selPerson, st.selJoint.joint.idx, newPos);
          rebuildBones(st, st.selPerson);
          updateBoneLengthLabels(st, st.selPerson);
        }
      }
      updatePreview(st);
      return;
    }

    // Update cursor style for hover feedback
    const hits = getHits(ev);
    if (hits.length > 0) {
      el.style.cursor = ev.shiftKey ? 'move' : 'grab';
      // Highlight hovered joint
      const hoveredMesh = hits[0].object;
      if (st.hoveredMesh && st.hoveredMesh !== hoveredMesh && st.hoveredMesh.material) {
        st.hoveredMesh.material.emissiveIntensity = 0.15;
      }
      if (hoveredMesh.material) {
        hoveredMesh.material.emissiveIntensity = 0.5;
        st.hoveredMesh = hoveredMesh;
      }
    } else {
      el.style.cursor = 'default';
      // Reset highlight
      if (st.hoveredMesh && st.hoveredMesh.material) {
        st.hoveredMesh.material.emissiveIntensity = 0.15;
        st.hoveredMesh = null;
      }
    }
  });

  // Use global pointerup to catch mouse release even outside the canvas
  window.addEventListener('pointerup', () => {
    if (st.isDragging && st.selJoint) {
      if (!st.draggingAll && st.selJoint.mesh.material) {
        st.selJoint.mesh.material.emissiveIntensity = 0.15;
      }
      
      st.selJoint = null; st.isDragging = false; st.draggingAll = false;
      
      // Re-enable OrbitControls after dragging
      if (st.controls && st.useOrbitControls) {
        st.controls.enabled = true;
      }
      
      // Always sync data after drag ends
      updatePreview(st);
      if (st.onUpdate) st.onUpdate(serializeState(st));
    }
  });

  el.addEventListener('contextmenu', (ev) => ev.preventDefault());

  /* also catch wheel on the wrapper to prevent LiteGraph zoom */
  container.addEventListener('wheel', (ev) => {
    if (ev.target === el || el.contains(ev.target)) {
      ev.stopPropagation();
    }
  }, { passive: true });
}

/* ---------- UI ---------- */

function buildUI(node) {
  // Find the pose_data widget and hide it
  let pdW = node.widgets?.find(w => w.name === "pose_data");
  if (pdW) { 
    pdW.hidden = true; 
    pdW.computeSize = () => [0, -4]; 
  }
  
  const wrap = document.createElement("div");
  wrap.style.cssText = "display:flex;flex-direction:column;gap:2px;width:100%;height:100%;overflow:hidden;";

  const cvWrap = document.createElement("div");
  cvWrap.style.cssText = "position:relative;width:100%;aspect-ratio:1/1;overflow:hidden;background:#1a1a1a;border:1px solid #333;border-radius:4px;touch-action:none;max-height:400px;";
  
  // Style canvas to fill container
  const style = document.createElement("style");
  style.textContent = `.cj-canvas-wrap canvas { width: 100% !important; height: 100% !important; display: block; }`;
  document.head.appendChild(style);
  cvWrap.classList.add("cj-canvas-wrap");

  const preview = document.createElement("div");
  preview.className = "cj-pose-preview";
  preview.style.cssText = "background:#0d0d0d;color:#fff;border:1px solid #555;border-radius:3px;padding:3px 6px;font-size:10px;font-family:monospace;line-height:1.6;min-height:20px;overflow:hidden;";
  preview.innerText = "加载中...";

  // Camera prompt display (show description instead of angles)
  const cameraInfo = document.createElement("div");
  cameraInfo.className = "cj-camera-info";
  cameraInfo.style.cssText = "background:#0a0a0f;color:#E93D82;border:1px solid rgba(233,61,130,0.3);border-radius:3px;padding:3px 6px;font-size:10px;font-family:monospace;line-height:1.4;";
  cameraInfo.innerHTML = '<span id="cj-camera-prompt">front view, eye level, medium shot</span>';

  const btnRow = document.createElement("div");
  btnRow.style.cssText = "display:flex;gap:3px;flex-wrap:wrap;";

  function btn(t, fn, title) {
    const b = document.createElement("button");
    b.textContent = t;
    b.title = title || t;
    b.style.cssText = "background:#333;color:#ccc;border:1px solid #555;padding:1px 8px;border-radius:3px;cursor:pointer;font-size:10px;line-height:1.6;";
    b.onclick = fn;
    return b;
  }

  const resetViewBtn = btn("重置视角", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      centerCameraOnPeople(node._st);
      node._st.controls.update();
      updatePreview(node._st);
      if (node._st.onUpdate) node._st.onUpdate(serializeState(node._st));
    }
  }, "重置相机视角到默认位置");
  
  const resetPoseBtn = btn("重置骨骼", () => { if (node._st) { resetPoseState(node._st); syncState(node); updatePreview(node._st); } }, "重置骨骼姿势到默认状态");
  const rotP = btn("+30°", () => { if (node._st) { rotatePoseState(node._st, 30); syncState(node); updatePreview(node._st); } }, "顺时针旋转30度");
  const rotN = btn("-30°", () => { if (node._st) { rotatePoseState(node._st, -30); syncState(node); updatePreview(node._st); } }, "逆时针旋转30度");
  const flipBtn = btn("镜像", () => { if (node._st) { flipPoseState(node._st); syncState(node); updatePreview(node._st); } }, "水平镜像翻转");
  
  // Camera view buttons - rotate around model center
  const frontViewBtn = btn("正视", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      const target = node._st.controls.target.clone();
      node._st.camera.position.set(target.x, target.y, target.z + 1.8);
      node._st.controls.update();
      updatePreview(node._st);
      if (node._st.onUpdate) node._st.onUpdate(serializeState(node._st));
    }
  }, "切换到正视图");
  
  const sideViewBtn = btn("侧视", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      const target = node._st.controls.target.clone();
      node._st.camera.position.set(target.x + 1.8, target.y, target.z);
      node._st.controls.update();
      updatePreview(node._st);
      if (node._st.onUpdate) node._st.onUpdate(serializeState(node._st));
    }
  }, "切换到侧视图");
  
  const topViewBtn = btn("顶视", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      const target = node._st.controls.target.clone();
      node._st.camera.position.set(target.x, target.y + 1.8, target.z + 0.001);
      node._st.controls.update();
      updatePreview(node._st);
      if (node._st.onUpdate) node._st.onUpdate(serializeState(node._st));
    }
  }, "切换到顶视图");

  const toggleBoneLengths = btn("骨骼", () => {
    if (node._st) {
      node._st.showBoneLengths = !node._st.showBoneLengths;
      if (node._st.showBoneLengths) {
        if (node._st.people.length > 0) {
          createBoneLengthLabels(node._st, node._st.people[0]);
        }
      } else {
        clearBoneLengthLabels(node._st);
      }
    }
  }, "显示/隐藏骨骼长度约束");

  btnRow.append(resetViewBtn, resetPoseBtn, rotP, rotN, flipBtn, frontViewBtn, sideViewBtn, topViewBtn, toggleBoneLengths);
  wrap.append(cvWrap, preview, cameraInfo, btnRow);

  node._poseContainer = cvWrap;
  node._posePreviewEl = preview;

  let st = null;

  const widget = node.addDOMWidget("openpose_editor", "3D姿态编辑", wrap, {
    getValue: () => node._poseData || "{}",
    setValue: (v) => {
      node._poseData = v;
      if (st) loadData(st, v);
    }
  });
  widget.computeSize = (w) => [w || 300, (w || 300) + 100];

  node.setSize([Math.max(340, node.size[0]), Math.max(460, node.size[1])]);

  loadThree(() => {
    st = buildScene(cvWrap);
    st.previewEl = preview;
    st.node = node;
    st.onUpdate = (data) => {
      node._poseData = data;
      // Update both widget and properties
      if (pdW) pdW.value = data;
      node.properties.pose_data = data;
      app.graph.setDirtyCanvas(true, true);
    };
    node._st = st;

    // Update renderer size after DOM is ready
    requestAnimationFrame(() => {
      const w = cvWrap.clientWidth || 300;
      const h = cvWrap.clientHeight || w; // Default to square
      st.renderer.setSize(w, h);
      st.camera.aspect = w / h;
      st.camera.updateProjectionMatrix();
      st.renderer.render(st.scene, st.camera);
    });

    const initData = node._poseData || pdW?.value || node.properties?.pose_data || "";
    if (initData && initData !== "{}") loadData(st, initData);
    else { resetPoseState(st); syncState(node); }
  });

  const origRemoved = node.onRemoved;
  node.onRemoved = function () {
    if (st) { 
      st.ro?.disconnect(); 
      if (st.controls && st.useOrbitControls) {
        st.controls.dispose();
      }
      clearAll(st); 
    }
    origRemoved?.apply(this, arguments);
  };
}

/* ---------- load / sync ---------- */

function loadData(st, jsonStr) {
  if (!jsonStr || !jsonStr.trim() || jsonStr === "{}") { resetPoseState(st); return; }
  try {
    const data = JSON.parse(jsonStr);
    clearAll(st);
    const pd = data.people || [];
    if (!pd.length) { resetPoseState(st); return; }
    pd.forEach(p => {
      const kp3d = p.pose_keypoints_3d || p.pose_keypoints_2d || [];
      if (kp3d.length === 54) {
        const kp4d = [];
        for (let i = 0; i < 18; i++) kp4d.push(kp3d[i * 3], kp3d[i * 3 + 1], 0, kp3d[i * 3 + 2] || 1);
        addPerson(st, kp4d);
      } else {
        addPerson(st, kp3d);
      }
    });
    
    // Center camera on loaded people
    centerCameraOnPeople(st);
    
    updatePreview(st);
  } catch (e) { resetPoseState(st); }
}

function syncState(node) {
  if (!node._st) return;
  const data = serializeState(node._st);
  node._poseData = data;
  // Update both widget and properties
  const w = node.widgets?.find(w => w.name === "pose_data");
  if (w) w.value = data;
  node.properties.pose_data = data;
  app.graph.setDirtyCanvas(true, true);
}

/* ---------- extension registration ---------- */

app.registerExtension({
  name: "CJNodes.OpenPoseEditor",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "CJOpenPoseEditor") return;
    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = onCreated?.apply(this, arguments);
      buildUI(this);
      return r;
    };
  }
});
