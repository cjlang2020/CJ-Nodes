import { app } from "../../../../scripts/app.js";

/* ---------- constants (matching original OpenPoseEditor) ---------- */

const CONNECT = [[0,1],[1,2],[2,3],[3,4],[1,5],[5,6],[6,7],[1,8],[8,9],[9,10],[1,11],[11,12],[12,13],[14,0],[14,16],[15,0],[15,17]];

const COLORS = [
  [0,0,255],[255,0,0],[255,170,0],[255,255,0],[255,85,0],[170,255,0],[85,255,0],[0,255,0],
  [0,255,85],[0,255,170],[0,255,255],[0,170,255],[0,85,255],[85,0,255],[170,0,255],[255,0,255],[255,0,170],[255,0,85]
];

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
    controls: null, useOrbitControls: false
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
  m.raycast = THREE.Mesh.prototype.raycast; // Ensure raycast works
  st.scene.add(m);
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

  // Helper: calculate vector length
  const vecLen = (v) => Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
  
  // Helper: normalize vector
  const vecNorm = (v) => {
    const len = vecLen(v);
    return len > 0 ? { x: v.x / len, y: v.y / len, z: v.z / len } : { x: 0, y: 1, z: 0 };
  };

  // Helper: get center of two points
  const getCenter = (p1, p2) => p1 && p2 ? {
    x: (p1.x + p2.x) / 2,
    y: (p1.y + p2.y) / 2,
    z: (p1.z + p2.z) / 2
  } : null;

  // ========== 1. Analyze base posture (standing/sitting/squatting/lying) ==========
  const shoulderCenter = getCenter(p[2], p[5]);
  const hipCenter = getCenter(p[8], p[11]);
  
  if (shoulderCenter && hipCenter && p[1]) {
    const spineVector = {
      x: p[1].x - hipCenter.x,
      y: p[1].y - hipCenter.y,
      z: p[1].z - hipCenter.z
    };
    const spineLen = vecLen(spineVector);
    
    if (spineLen > 0) {
      const spineDir = vecNorm(spineVector);
      const verticalAngle = Math.acos(Math.abs(spineDir.y)) * 180 / Math.PI;
      
      // Calculate hip height relative to ankles
      const avgAnkleY = ((p[10] ? p[10].y : 0) + (p[13] ? p[13].y : 0)) / 2;
      const hipHeight = hipCenter.y - avgAnkleY;
      const bodyHeight = spineLen;
      
      if (verticalAngle < 45) {
        // Nearly vertical - standing poses
        if (spineDir.z < -0.6) {
          parts.push("后仰");
        } else if (spineDir.z > 0.6) {
          if (hipHeight < bodyHeight * 0.3) {
            parts.push("坐姿俯身");
          } else {
            parts.push("站立俯身");
          }
        } else if (spineDir.z < -0.3) {
          parts.push("微微后仰");
        } else if (spineDir.z > 0.3) {
          parts.push("微微前倾");
        } else {
          if (hipHeight < bodyHeight * 0.3) {
            // Might be sitting
            const avgKneeY = ((p[9] ? p[9].y : 0) + (p[12] ? p[12].y : 0)) / 2;
            if (avgKneeY > hipCenter.y + 0.05) {
              // Check if cross-legged
              if (p[10] && p[13] && p[9] && p[12]) {
                const legsCrossed = (p[10].x > p[12].x && p[13].x < p[9].x) ||
                                   (p[13].x > p[9].x && p[10].x < p[12].x);
                parts.push(legsCrossed ? "盘腿坐" : "跪坐");
              } else {
                parts.push("坐姿");
              }
            } else {
              parts.push("坐姿");
            }
          } else if (hipHeight < bodyHeight * 0.6) {
            parts.push("蹲姿");
          } else {
            parts.push("站立");
          }
        }
      } else if (verticalAngle > 75) {
        // Nearly horizontal - lying poses
        const shoulderHipDiff = shoulderCenter.y - hipCenter.y;
        if (shoulderHipDiff > 0.2) {
          parts.push("仰卧");
        } else if (shoulderHipDiff < -0.2) {
          parts.push("俯卧");
        } else {
          parts.push("侧卧");
        }
      } else {
        // Tilted
        if (spineDir.z < -0.5) parts.push("大幅度后仰");
        else if (spineDir.z > 0.5) parts.push("大幅度前倾");
        else if (spineDir.z < -0.2) parts.push("后仰");
        else if (spineDir.z > 0.2) parts.push("前倾");
        else parts.push("倾斜姿态");
      }
    }
  }

  // ========== 2. Analyze arm movements (detailed) ==========
  const analyzeArm = (shoulder, elbow, wrist, side) => {
    if (!shoulder || !elbow || !wrist) return;
    
    const wristRel = {
      x: wrist.x - shoulder.x,
      y: wrist.y - shoulder.y,
      z: wrist.z - shoulder.z
    };
    const wristLen = vecLen(wristRel);
    
    if (wristLen > 0) {
      const wristDir = vecNorm(wristRel);
      
      // Up/down direction
      if (wristDir.y > 0.3) parts.push(`${side}手举起`);
      else if (wristDir.y < -0.3) parts.push(`${side}手放下`);
      
      // Front/back direction
      if (wristDir.z > 0.2) parts.push(`${side}手在身体前面`);
      else if (wristDir.z < -0.1) parts.push(`${side}手在身体后面`);
    }
  };
  
  analyzeArm(p[2], p[3], p[4], "右");
  analyzeArm(p[5], p[6], p[7], "左");

  // ========== 3. Analyze leg movements (detailed) ==========
  const analyzeLeg = (hip, knee, ankle, side) => {
    if (!hip || !knee || !ankle) return;
    
    const kneeLocal = { x: knee.x - hip.x, y: knee.y - hip.y, z: knee.z - hip.z };
    const ankleLocal = { x: ankle.x - knee.x, y: ankle.y - knee.y, z: ankle.z - knee.z };
    
    const kneeLen = vecLen(kneeLocal);
    if (kneeLen > 0) {
      const kneeDir = vecNorm(kneeLocal);
      
      // Knee lift degree
      if (kneeDir.z > 0.7) parts.push(`${side}腿膝盖大幅抬起`);
      else if (kneeDir.z > 0.4) parts.push(`${side}腿膝盖抬起`);
      else if (kneeDir.z > 0.2) parts.push(`${side}腿膝盖微微抬起`);
    }
    
    // Foot lift degree
    const footLen = Math.sqrt(ankleLocal.y * ankleLocal.y + ankleLocal.z * ankleLocal.z);
    if (footLen > 0) {
      const footDirY = ankleLocal.y / footLen;
      if (footDirY > 0.7) parts.push(`${side}脚大幅抬起`);
      else if (footDirY > 0.4) parts.push(`${side}脚抬起`);
    }
  };
  
  analyzeLeg(p[8], p[9], p[10], "右");
  analyzeLeg(p[11], p[12], p[13], "左");

  // ========== 4. Analyze leg spread ==========
  if (p[9] && p[12] && p[8] && p[11]) {
    const leftKneeRel = { x: p[9].x - p[8].x, y: p[9].y - p[8].y, z: p[9].z - p[8].z };
    const rightKneeRel = { x: p[12].x - p[11].x, y: p[12].y - p[11].y, z: p[12].z - p[11].z };
    
    const kneeDistanceX = Math.abs(leftKneeRel.x - rightKneeRel.x);
    
    if (kneeDistanceX > 0.25) parts.push("双腿大幅分开");
    else if (kneeDistanceX > 0.17) parts.push("双腿分开");
    else if (kneeDistanceX > 0.08) parts.push("双腿微微分开");
    else if (kneeDistanceX < 0.03) parts.push("双腿并拢");
  }

  // ========== 5. Head tilt ==========
  if (p[0] && p[1] && Math.abs(p[0].x - p[1].x) > 0.04) {
    parts.push(p[0].x > p[1].x ? "头部右偏" : "头部左偏");
  }

  return parts.length ? parts.join("，") : "标准站立姿势";
}

function updatePreview(st) {
  let el = st.previewEl;
  if (!el && st.node) el = st.node.querySelector('.cj-pose-preview');
  if (!el) return;
  if (!st.people.length) { el.textContent = "未检测到人物"; return; }
  // Only show posture description without "人物1:" prefix
  const txt = analyzePerson(st.people[0].joints);
  if (el.textContent !== txt) el.textContent = txt;
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
  
  // Get camera info
  const cam = st.camera;
  const cameraInfo = {
    position: { x: cam.position.x, y: cam.position.y, z: cam.position.z },
    target: { x: st.controls?.target?.x || 0, y: st.controls?.target?.y || 0, z: st.controls?.target?.z || 0 }
  };
  
  return JSON.stringify({ 
    width: 1024, 
    height: 1024, 
    people: all,
    posture_description: postureDesc,
    camera: cameraInfo
  });
}

function sendUpdate(st) {
  if (st.onUpdate) st.onUpdate(serializeState(st));
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
          st.selJoint.mesh.position.copy(st.hitPt).add(st.dragOff);
          rebuildBones(st, st.selJoint.person);
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

  const resetBtn = btn("重置", () => { if (node._st) { resetPoseState(node._st); syncState(node); } }, "重置姿态到默认状态");
  const rotP = btn("+30°", () => { if (node._st) { rotatePoseState(node._st, 30); syncState(node); } }, "顺时针旋转30度");
  const rotN = btn("-30°", () => { if (node._st) { rotatePoseState(node._st, -30); syncState(node); } }, "逆时针旋转30度");
  const flipBtn = btn("镜像", () => { if (node._st) { flipPoseState(node._st); syncState(node); } }, "水平镜像翻转");
  
  // Camera view buttons - rotate around model center
  const frontViewBtn = btn("正视", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      const target = node._st.controls.target.clone();
      node._st.camera.position.set(target.x, target.y, target.z + 1.8);
      node._st.controls.update();
    }
  }, "切换到正视图");
  
  const sideViewBtn = btn("侧视", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      const target = node._st.controls.target.clone();
      node._st.camera.position.set(target.x + 1.8, target.y, target.z);
      node._st.controls.update();
    }
  }, "切换到侧视图");
  
  const topViewBtn = btn("顶视", () => {
    if (node._st && node._st.controls && node._st.useOrbitControls) {
      const target = node._st.controls.target.clone();
      node._st.camera.position.set(target.x, target.y + 1.8, target.z + 0.001);
      node._st.controls.update();
    }
  }, "切换到顶视图");

  btnRow.append(resetBtn, rotP, rotN, flipBtn, frontViewBtn, sideViewBtn, topViewBtn);
  wrap.append(cvWrap, preview, btnRow);

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
  widget.computeSize = (w) => [w || 300, (w || 300) + 80];

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
