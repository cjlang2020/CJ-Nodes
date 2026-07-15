import json
import numpy as np
import torch
import cv2
import math

LIMB_SEQ = [[2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8], [2, 9], [9, 10], [10, 11], [2, 12], [12, 13], [13, 14], [2, 1], [1, 15], [15, 17], [1, 16], [16, 18]]

COLORS = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0], [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]

COCO_NAMES = ["鼻子","颈部","右肩","右肘","右腕","左肩","左肘","左腕","右髋","右膝","右踝","左髋","左膝","左踝","右眼","左眼","右耳","左耳"]


class CJOpenPoseEditor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "output_width": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 64}),
                "output_height": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 64}),
            },
            "optional": {
                "pose_data": ("STRING", {"multiline": True, "rows": 5, "default": "", "hidden": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("dw_pose_image", "posture_text", "camera_prompt")
    FUNCTION = "process"
    CATEGORY = "luy/姿态"

    def analyze_pose(self, kps, camera_pos=None):
        """分析姿态并生成详细描述词（基于3D坐标向量分析）
        
        Args:
            kps: 关键点列表，每个关键点为 (x, y, z) 或 (x, y) 或 None
            camera_pos: 相机位置，用于判断人物朝向
        """
        valid = [k for k in kps if k is not None]
        if len(valid) < 4:
            return "未检测到有效姿势"
        
        parts = []
        
        def get_point(idx):
            if idx < len(kps) and kps[idx] is not None:
                p = kps[idx]
                return {"x": p[0], "y": p[1], "z": p[2] if len(p) > 2 else 0}
            return None
        
        def vec_len(v):
            return (v["x"]**2 + v["y"]**2 + v["z"]**2) ** 0.5
        
        def vec_norm(v):
            l = vec_len(v)
            return {"x": v["x"]/l, "y": v["y"]/l, "z": v["z"]/l} if l > 0 else {"x": 0, "y": 1, "z": 0}
        
        def calc_angle(v1, v2):
            dot = v1["x"]*v2["x"] + v1["y"]*v2["y"] + v1["z"]*v2["z"]
            l1, l2 = vec_len(v1), vec_len(v2)
            if l1 == 0 or l2 == 0:
                return 0
            return math.acos(max(-1, min(1, dot / (l1 * l2)))) * 180 / math.pi
        
        nose = get_point(0)
        neck = get_point(1)
        r_shoulder = get_point(2)
        r_elbow = get_point(3)
        r_wrist = get_point(4)
        l_shoulder = get_point(5)
        l_elbow = get_point(6)
        l_wrist = get_point(7)
        r_hip = get_point(8)
        r_knee = get_point(9)
        r_ankle = get_point(10)
        l_hip = get_point(11)
        l_knee = get_point(12)
        l_ankle = get_point(13)
        
        def get_center(p1, p2):
            if p1 and p2:
                return {"x": (p1["x"]+p2["x"])/2, "y": (p1["y"]+p2["y"])/2, "z": (p1["z"]+p2["z"])/2}
            return None
        
        shoulder_center = get_center(l_shoulder, r_shoulder)
        hip_center = get_center(l_hip, r_hip)
        
        # ========== 1. 基本姿势 ==========
        if shoulder_center and hip_center and neck:
            spine_vector = {"x": neck["x"]-hip_center["x"], "y": neck["y"]-hip_center["y"], "z": neck["z"]-hip_center["z"]}
            spine_len = vec_len(spine_vector)
            
            if spine_len > 0:
                spine_dir = vec_norm(spine_vector)
                vertical_angle = math.acos(abs(spine_dir["y"])) * 180 / math.pi
                
                avg_ankle_y = 0
                ankle_count = 0
                if l_ankle: avg_ankle_y += l_ankle["y"]; ankle_count += 1
                if r_ankle: avg_ankle_y += r_ankle["y"]; ankle_count += 1
                if ankle_count > 0: avg_ankle_y /= ankle_count
                
                hip_height = hip_center["y"] - avg_ankle_y
                body_height = spine_len
                
                if vertical_angle < 45:
                    if spine_dir["z"] < -0.6:
                        base_posture = "身体大幅后仰"
                    elif spine_dir["z"] > 0.6:
                        base_posture = "坐姿身体前倾" if hip_height < body_height * 0.3 else "站立身体前倾"
                    elif spine_dir["z"] < -0.3:
                        base_posture = "身体微微后仰"
                    elif spine_dir["z"] > 0.3:
                        base_posture = "身体微微前倾"
                    else:
                        if hip_height < body_height * 0.3:
                            avg_knee_y = 0
                            knee_count = 0
                            if l_knee: avg_knee_y += l_knee["y"]; knee_count += 1
                            if r_knee: avg_knee_y += r_knee["y"]; knee_count += 1
                            if knee_count > 0: avg_knee_y /= knee_count
                            
                            if avg_knee_y > hip_center["y"] + 20:
                                if l_ankle and r_ankle and l_knee and r_knee:
                                    legs_crossed = (l_ankle["x"] > r_knee["x"] and r_ankle["x"] < l_knee["x"]) or \
                                                   (r_ankle["x"] > l_knee["x"] and l_ankle["x"] < r_knee["x"])
                                    base_posture = "盘腿坐姿" if legs_crossed else "跪坐姿势"
                                else:
                                    base_posture = "坐姿"
                            else:
                                base_posture = "坐姿"
                        elif hip_height < body_height * 0.6:
                            base_posture = "蹲姿"
                        else:
                            base_posture = "标准站立"
                elif vertical_angle > 75:
                    shoulder_hip_diff = shoulder_center["y"] - hip_center["y"]
                    if shoulder_hip_diff > 20: base_posture = "仰卧姿势"
                    elif shoulder_hip_diff < -20: base_posture = "俯卧姿势"
                    else: base_posture = "侧卧姿势"
                else:
                    if spine_dir["z"] < -0.5: base_posture = "身体大幅度后仰倾斜"
                    elif spine_dir["z"] > 0.5: base_posture = "身体大幅度前倾倾斜"
                    elif spine_dir["z"] < -0.2: base_posture = "身体后仰倾斜"
                    elif spine_dir["z"] > 0.2: base_posture = "身体前倾倾斜"
                    else: base_posture = "身体倾斜姿态"
                
                parts.append(base_posture)
        
        # ========== 2. 手臂动作（详细分析）==========
        def analyze_arm(shoulder, elbow, wrist, side):
            if not shoulder or not elbow or not wrist:
                return
            
            upper_arm_rel = {"x": elbow["x"]-shoulder["x"], "y": elbow["y"]-shoulder["y"], "z": elbow["z"]-shoulder["z"]}
            forearm_rel = {"x": wrist["x"]-elbow["x"], "y": wrist["y"]-elbow["y"], "z": wrist["z"]-elbow["z"]}
            wrist_rel = {"x": wrist["x"]-shoulder["x"], "y": wrist["y"]-shoulder["y"], "z": wrist["z"]-shoulder["z"]}
            wrist_len = vec_len(wrist_rel)
            
            if wrist_len > 0:
                wrist_dir = vec_norm(wrist_rel)
                
                if wrist_dir["y"] > 0.6: parts.append(f"{side}手高举过头顶")
                elif wrist_dir["y"] > 0.3: parts.append(f"{side}手举起")
                elif wrist_dir["y"] < -0.6: parts.append(f"{side}手自然下垂")
                elif wrist_dir["y"] < -0.3: parts.append(f"{side}手放下")
                
                if wrist_dir["z"] > 0.3: parts.append(f"{side}手向前伸展")
                elif wrist_dir["z"] > 0.1: parts.append(f"{side}手在身体前面")
                elif wrist_dir["z"] < -0.3: parts.append(f"{side}手向后伸展")
                elif wrist_dir["z"] < -0.1: parts.append(f"{side}手在身体后面")
                
                if abs(wrist_dir["x"]) > 0.3: parts.append(f"{side}手向外侧伸展")
            
            upper_arm_len = vec_len(upper_arm_rel)
            forearm_len = vec_len(forearm_rel)
            if upper_arm_len > 0 and forearm_len > 0:
                elbow_angle = calc_angle(vec_norm(upper_arm_rel), vec_norm(forearm_rel))
                if elbow_angle < 45: parts.append(f"{side}手臂弯曲")
                elif elbow_angle > 135: parts.append(f"{side}手臂伸直")
        
        analyze_arm(l_shoulder, l_elbow, l_wrist, "左")
        analyze_arm(r_shoulder, r_elbow, r_wrist, "右")
        
        # ========== 3. 腿部动作（详细分析）==========
        def analyze_leg(hip, knee, ankle, side):
            if not hip or not knee or not ankle:
                return
            
            knee_local = {"x": knee["x"]-hip["x"], "y": knee["y"]-hip["y"], "z": knee["z"]-hip["z"]}
            ankle_local = {"x": ankle["x"]-knee["x"], "y": ankle["y"]-knee["y"], "z": ankle["z"]-knee["z"]}
            
            knee_len = vec_len(knee_local)
            if knee_len > 0:
                knee_dir = vec_norm(knee_local)
                if knee_dir["z"] > 0.7: parts.append(f"{side}腿膝盖大幅抬起")
                elif knee_dir["z"] > 0.4: parts.append(f"{side}腿膝盖抬起")
                elif knee_dir["z"] > 0.2: parts.append(f"{side}腿膝盖微微抬起")
                
                if knee_dir["y"] < -0.3: parts.append(f"{side}腿弯曲")
                elif knee_dir["y"] > 0.3: parts.append(f"{side}腿伸直")
            
            foot_len = (ankle_local["y"]**2 + ankle_local["z"]**2) ** 0.5
            if foot_len > 0:
                foot_dir_y = ankle_local["y"] / foot_len
                foot_dir_z = ankle_local["z"] / foot_len
                if foot_dir_y > 0.7: parts.append(f"{side}脚大幅抬起")
                elif foot_dir_y > 0.4: parts.append(f"{side}脚抬起")
                if foot_dir_z > 0.3: parts.append(f"{side}脚向前伸")
                elif foot_dir_z < -0.3: parts.append(f"{side}脚向后伸")
        
        analyze_leg(l_hip, l_knee, l_ankle, "左")
        analyze_leg(r_hip, r_knee, r_ankle, "右")
        
        # ========== 4. 双腿分开程度 ==========
        if l_knee and r_knee and l_hip and r_hip:
            left_knee_rel = {"x": l_knee["x"]-l_hip["x"], "y": l_knee["y"]-l_hip["y"], "z": l_knee["z"]-l_hip["z"]}
            right_knee_rel = {"x": r_knee["x"]-r_hip["x"], "y": r_knee["y"]-r_hip["y"], "z": r_knee["z"]-r_hip["z"]}
            knee_distance_x = abs(left_knee_rel["x"] - right_knee_rel["x"])
            
            if knee_distance_x > 120: parts.append("双腿大幅分开站立")
            elif knee_distance_x > 80: parts.append("双腿分开站立")
            elif knee_distance_x > 40: parts.append("双腿微微分开")
            elif knee_distance_x < 15: parts.append("双腿并拢站立")
        
        # ========== 5. 头部方向和倾斜 ==========
        if nose and neck:
            head_tilt = abs(nose["x"] - neck["x"])
            if head_tilt > 30: parts.append("头部向右倾斜" if nose["x"] > neck["x"] else "头部向左倾斜")
            elif head_tilt > 15: parts.append("头部微微右偏" if nose["x"] > neck["x"] else "头部微微左偏")
            
            head_z = nose["z"] - neck["z"]
            if head_z > 15: parts.append("头部向前伸")
            elif head_z < -15: parts.append("头部向后仰")
        
        # ========== 6. 重心分布 ==========
        if r_ankle and l_ankle and r_hip and l_hip:
            left_weight = l_ankle["x"] - l_hip["x"]
            right_weight = r_ankle["x"] - r_hip["x"]
            if abs(left_weight - right_weight) > 50:
                parts.append("重心偏向左侧" if left_weight > right_weight else "重心偏向右侧")
        
        result = "，".join(parts) if parts else "标准站立姿势"
        return result

    def pose3d_to_pixel(self, x, y, camera_info=None, output_width=1024, output_height=1024):
        """将3D坐标投影到2D像素坐标，支持相机视角和自定义输出尺寸"""
        # 计算中心点和缩放比例
        # 3D坐标范围约±0.55，需要映射到输出尺寸的80%区域
        center_x = output_width / 2
        center_y = output_height / 2
        
        if camera_info:
            # 从相机信息获取位置
            cam_pos = camera_info.get('position', {})
            cx = cam_pos.get('x', 0)
            cy = cam_pos.get('y', 0)
            cz = cam_pos.get('z', 1.8)
            
            # 根据相机距离计算缩放，使骨架填充约80%的画面
            # 相机距离1.8时，3D坐标±0.55应该映射到画面的80%
            zoom = 1.0 / max(abs(cz), 0.1)
            scale = min(output_width, output_height) * 0.4 * zoom  # 0.4 = 80% / 2
            
            rel_x = x - cx
            rel_y = y - cy
            
            px = rel_x * scale + center_x
            py = -rel_y * scale + center_y
            
            return px, py
        else:
            # 无相机信息时，直接缩放填充画面
            # 3D范围约1.1，映射到输出尺寸的80%
            scale = min(output_width, output_height) * 0.4  # 0.4 = 80% / 2 / 0.55 ≈ 0.36，取0.4使骨架更大
            return x * scale + center_x, -y * scale + center_y

    def extract_keypoints_2d(self, pose_json, output_width=1024, output_height=1024):
        """提取关键点，支持3D和2D格式，返回包含z坐标的元组"""
        try:
            data = json.loads(pose_json)
        except json.JSONDecodeError:
            return []
        
        # 获取相机信息
        camera_info = data.get('camera', None)
        
        people = data.get('people', [])
        result = []
        for person in people:
            kp3d = person.get('pose_keypoints_3d', [])
            kp2d = person.get('pose_keypoints_2d', [])
            kps = []
            if kp3d and len(kp3d) >= 72:
                # 3D格式: [x, y, z, confidence] * 18
                for i in range(18):
                    idx = i * 4
                    if kp3d[idx + 3] > 0:
                        px, py = self.pose3d_to_pixel(kp3d[idx], kp3d[idx + 1], camera_info, output_width, output_height)
                        pz = kp3d[idx + 2]  # 保留z坐标
                        kps.append((px, py, pz))
                    else:
                        kps.append(None)
            elif kp2d and len(kp2d) >= 54:
                # 2D格式: [x, y, confidence] * 18
                for i in range(18):
                    idx = i * 3
                    if kp2d[idx + 2] > 0:
                        kps.append((kp2d[idx], kp2d[idx + 1], 0))
                    else:
                        kps.append(None)
            else:
                kps = [None] * 18
            result.append(kps)
        return result

    def render_dw_pose(self, pose_json, width, height):
        if not pose_json or not pose_json.strip():
            return np.zeros((height, width, 3), dtype=np.uint8)
        try:
            data = json.loads(pose_json)
        except json.JSONDecodeError:
            return np.zeros((height, width, 3), dtype=np.uint8)

        target_w, target_h = width, height
        original_w = data.get('width', target_w) or target_w
        original_h = data.get('height', target_h) or target_h
        scale_x = target_w / original_w if original_w > 0 else 1
        scale_y = target_h / original_h if original_h > 0 else 1

        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        people = data.get('people', [])
        if not people:
            return canvas

        # 获取相机信息
        camera_info = data.get('camera', None)

        base_thickness = 2.0
        target_max_side = max(target_w, target_h)
        scale_factor = target_max_side / 512.0
        jr = int(max(1, base_thickness * scale_factor))
        sw = jr

        for person in people:
            kp3d = person.get('pose_keypoints_3d', [])
            kp2d = person.get('pose_keypoints_2d', [])
            kps = []
            if kp3d and len(kp3d) >= 72:
                for i in range(18):
                    idx = i * 4
                    if kp3d[idx + 3] > 0:
                        px, py = self.pose3d_to_pixel(kp3d[idx], kp3d[idx + 1], camera_info, target_w, target_h)
                        kps.append((int(px), int(py)))
                    else:
                        kps.append(None)
            elif kp2d and len(kp2d) >= 54:
                for i in range(18):
                    idx = i * 3
                    if kp2d[idx + 2] > 0:
                        kps.append((int(kp2d[idx] * scale_x), int(kp2d[idx + 1] * scale_y)))
                    else:
                        kps.append(None)
            else:
                kps = [None] * 18

            for limb, color in zip(LIMB_SEQ, COLORS):
                k1 = limb[0] - 1
                k2 = limb[1] - 1
                if k1 >= len(kps) or k2 >= len(kps):
                    continue
                p1 = kps[k1]
                p2 = kps[k2]
                if p1 is None or p2 is None:
                    continue
                Y = np.array([p1[0], p2[0]])
                X = np.array([p1[1], p2[1]])
                mX, mY = np.mean(X), np.mean(Y)
                length = np.sqrt((X[0] - X[1])**2 + (Y[0] - Y[1])**2)
                angle = math.degrees(math.atan2(X[0] - X[1], Y[0] - Y[1]))
                poly = cv2.ellipse2Poly((int(mY), int(mX)), (int(length / 2), sw), int(angle), 0, 360, 1)
                cv2.fillConvexPoly(canvas, poly, [int(c * 0.6) for c in color])

            for i, kp in enumerate(kps):
                if kp is None or i >= len(COLORS):
                    continue
                cv2.circle(canvas, kp, jr, COLORS[i], thickness=-1)

        return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

    def process(self, output_width, output_height, pose_data=""):
        if not pose_data or not pose_data.strip():
            dw_pose_np = np.zeros((output_height, output_width, 3), dtype=np.uint8)
            posture_text = "未检测到有效姿势"
            camera_prompt = ""
        else:
            dw_pose_np = self.render_dw_pose(pose_data, output_width, output_height)
            
            # Directly use posture_description and camera_prompt from frontend
            try:
                data = json.loads(pose_data)
                posture_text = data.get("posture_description", "标准站立姿势")
                camera_prompt = data.get("camera_prompt", "")
            except:
                posture_text = "标准站立姿势"
                camera_prompt = ""

        dw_pose_image = torch.from_numpy(dw_pose_np.astype(np.float32) / 255.0).unsqueeze(0)
        return (dw_pose_image, posture_text, camera_prompt)
