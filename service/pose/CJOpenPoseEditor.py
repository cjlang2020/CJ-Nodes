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

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("dw_pose_image", "posture_text")
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
        
        # 获取各关键点（支持3D和2D）
        def get_point(idx):
            if idx < len(kps) and kps[idx] is not None:
                p = kps[idx]
                return {"x": p[0], "y": p[1], "z": p[2] if len(p) > 2 else 0}
            return None
        
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
        
        # 计算中心点
        def get_center(p1, p2):
            if p1 and p2:
                return {
                    "x": (p1["x"] + p2["x"]) / 2,
                    "y": (p1["y"] + p2["y"]) / 2,
                    "z": (p1["z"] + p2["z"]) / 2
                }
            return None
        
        shoulder_center = get_center(l_shoulder, r_shoulder)
        hip_center = get_center(l_hip, r_hip)
        
        # ========== 1. 分析基本姿势（站立/坐姿/蹲姿/躺姿）==========
        if shoulder_center and hip_center and neck:
            # 计算脊柱向量
            spine_vector = {
                "x": neck["x"] - hip_center["x"],
                "y": neck["y"] - hip_center["y"],
                "z": neck["z"] - hip_center["z"]
            }
            spine_len = (spine_vector["x"]**2 + spine_vector["y"]**2 + spine_vector["z"]**2) ** 0.5
            
            if spine_len > 0:
                spine_dir = {
                    "x": spine_vector["x"] / spine_len,
                    "y": spine_vector["y"] / spine_len,
                    "z": spine_vector["z"] / spine_len
                }
                
                import math
                vertical_angle = math.acos(abs(spine_dir["y"])) * 180 / math.pi
                
                # 计算臀部高度
                avg_ankle_y = 0
                ankle_count = 0
                if l_ankle:
                    avg_ankle_y += l_ankle["y"]
                    ankle_count += 1
                if r_ankle:
                    avg_ankle_y += r_ankle["y"]
                    ankle_count += 1
                if ankle_count > 0:
                    avg_ankle_y /= ankle_count
                
                hip_height = hip_center["y"] - avg_ankle_y
                body_height = spine_len
                
                if vertical_angle < 45:
                    # 接近垂直 - 站立类姿势
                    if spine_dir["z"] < -0.6:
                        base_posture = "后仰"
                    elif spine_dir["z"] > 0.6:
                        if hip_height < body_height * 0.3:
                            base_posture = "坐姿俯身"
                        else:
                            base_posture = "站立俯身"
                    elif spine_dir["z"] < -0.3:
                        base_posture = "微微后仰"
                    elif spine_dir["z"] > 0.3:
                        base_posture = "微微前倾"
                    else:
                        if hip_height < body_height * 0.3:
                            # 可能是坐姿
                            avg_knee_y = 0
                            knee_count = 0
                            if l_knee:
                                avg_knee_y += l_knee["y"]
                                knee_count += 1
                            if r_knee:
                                avg_knee_y += r_knee["y"]
                                knee_count += 1
                            if knee_count > 0:
                                avg_knee_y /= knee_count
                            
                            if avg_knee_y > hip_center["y"] + 20:
                                # 检查是否盘腿
                                if l_ankle and r_ankle and l_knee and r_knee:
                                    legs_crossed = (l_ankle["x"] > r_knee["x"] and r_ankle["x"] < l_knee["x"]) or \
                                                   (r_ankle["x"] > l_knee["x"] and l_ankle["x"] < r_knee["x"])
                                    base_posture = "盘腿坐" if legs_crossed else "跪坐"
                                else:
                                    base_posture = "坐姿"
                            else:
                                base_posture = "坐姿"
                        elif hip_height < body_height * 0.6:
                            base_posture = "蹲姿"
                        else:
                            base_posture = "站立"
                elif vertical_angle > 75:
                    # 接近水平 - 躺姿
                    shoulder_hip_diff = shoulder_center["y"] - hip_center["y"]
                    if shoulder_hip_diff > 20:
                        base_posture = "仰卧"
                    elif shoulder_hip_diff < -20:
                        base_posture = "俯卧"
                    else:
                        base_posture = "侧卧"
                else:
                    # 倾斜
                    if spine_dir["z"] < -0.5:
                        base_posture = "大幅度后仰"
                    elif spine_dir["z"] > 0.5:
                        base_posture = "大幅度前倾"
                    elif spine_dir["z"] < -0.2:
                        base_posture = "后仰"
                    elif spine_dir["z"] > 0.2:
                        base_posture = "前倾"
                    else:
                        base_posture = "倾斜姿态"
                
                parts.append(base_posture)
        
        # ========== 2. 分析手臂动作（详细）==========
        def analyze_arm(shoulder, elbow, wrist, side):
            if not shoulder or not elbow or not wrist:
                return
            
            # 计算手腕相对肩膀的方向
            wrist_rel = {
                "x": wrist["x"] - shoulder["x"],
                "y": wrist["y"] - shoulder["y"],
                "z": wrist["z"] - shoulder["z"]
            }
            wrist_len = (wrist_rel["x"]**2 + wrist_rel["y"]**2 + wrist_rel["z"]**2) ** 0.5
            
            if wrist_len > 0:
                wrist_dir = {
                    "x": wrist_rel["x"] / wrist_len,
                    "y": wrist_rel["y"] / wrist_len,
                    "z": wrist_rel["z"] / wrist_len
                }
                
                # 上下方向
                if wrist_dir["y"] > 0.3:
                    parts.append(f"{side}手举起")
                elif wrist_dir["y"] < -0.3:
                    parts.append(f"{side}手放下")
                
                # 前后方向
                if wrist_dir["z"] > 0.2:
                    parts.append(f"{side}手在身体前面")
                elif wrist_dir["z"] < -0.1:
                    parts.append(f"{side}手在身体后面")
        
        analyze_arm(l_shoulder, l_elbow, l_wrist, "左")
        analyze_arm(r_shoulder, r_elbow, r_wrist, "右")
        
        # ========== 3. 分析腿部动作（详细）==========
        def analyze_leg(hip, knee, ankle, side):
            if not hip or not knee or not ankle:
                return
            
            knee_local = {
                "x": knee["x"] - hip["x"],
                "y": knee["y"] - hip["y"],
                "z": knee["z"] - hip["z"]
            }
            ankle_local = {
                "x": ankle["x"] - knee["x"],
                "y": ankle["y"] - knee["y"],
                "z": ankle["z"] - knee["z"]
            }
            
            knee_len = (knee_local["x"]**2 + knee_local["y"]**2 + knee_local["z"]**2) ** 0.5
            
            if knee_len > 0:
                knee_dir = {
                    "x": knee_local["x"] / knee_len,
                    "y": knee_local["y"] / knee_len,
                    "z": knee_local["z"] / knee_len
                }
                
                # 膝盖抬起程度
                if knee_dir["z"] > 0.7:
                    parts.append(f"{side}腿膝盖大幅抬起")
                elif knee_dir["z"] > 0.4:
                    parts.append(f"{side}腿膝盖抬起")
                elif knee_dir["z"] > 0.2:
                    parts.append(f"{side}腿膝盖微微抬起")
            
            # 脚抬起程度
            foot_len = (ankle_local["y"]**2 + ankle_local["z"]**2) ** 0.5
            if foot_len > 0:
                foot_dir_y = ankle_local["y"] / foot_len
                if foot_dir_y > 0.7:
                    parts.append(f"{side}脚大幅抬起")
                elif foot_dir_y > 0.4:
                    parts.append(f"{side}脚抬起")
        
        analyze_leg(l_hip, l_knee, l_ankle, "左")
        analyze_leg(r_hip, r_knee, r_ankle, "右")
        
        # ========== 4. 分析双腿分开程度 ==========
        if l_knee and r_knee and l_hip and r_hip:
            left_knee_rel = {
                "x": l_knee["x"] - l_hip["x"],
                "y": l_knee["y"] - l_hip["y"],
                "z": l_knee["z"] - l_hip["z"]
            }
            right_knee_rel = {
                "x": r_knee["x"] - r_hip["x"],
                "y": r_knee["y"] - r_hip["y"],
                "z": r_knee["z"] - r_hip["z"]
            }
            
            knee_distance_x = abs(left_knee_rel["x"] - right_knee_rel["x"])
            
            if knee_distance_x > 120:
                parts.append("双腿大幅分开")
            elif knee_distance_x > 80:
                parts.append("双腿分开")
            elif knee_distance_x > 40:
                parts.append("双腿微微分开")
            elif knee_distance_x < 15:
                parts.append("双腿并拢")
        
        # ========== 5. 分析头部方向 ==========
        if nose and neck:
            head_tilt = abs(nose["x"] - neck["x"])
            if head_tilt > 30:
                parts.append("头部右偏" if nose["x"] > neck["x"] else "头部左偏")
        
        result = "，".join(parts) if parts else "标准站立姿势"
        return result

    def pose3d_to_pixel(self, x, y, camera_info=None):
        """将3D坐标投影到2D像素坐标，支持相机视角"""
        if camera_info:
            # 从相机信息获取位置和目标点
            cam_pos = camera_info.get('position', {})
            cam_target = camera_info.get('target', {})
            
            cx = cam_pos.get('x', 0)
            cy = cam_pos.get('y', 0)
            cz = cam_pos.get('z', 1.8)
            
            tx = cam_target.get('x', 0)
            ty = cam_target.get('y', 0)
            tz = cam_target.get('z', 0)
            
            # 计算相机方向向量
            dx = tx - cx
            dy = ty - cy
            dz = tz - cz
            
            # 计算距离（假设焦距与距离相关）
            dist = (dx*dx + dy*dy + dz*dz) ** 0.5
            if dist < 0.01:
                dist = 1.0
            
            # 简单透视投影：将3D点相对于相机位置投影
            # 相机看向-z方向，需要转换坐标
            rel_x = x - cx
            rel_y = y - cy
            rel_z = 0 - cz  # 假设z=0平面
            
            # 投影到2D（简化版，假设焦距为1）
            scale = 1.0 / max(abs(cz), 0.1) * 200  # 缩放因子
            px = rel_x * scale + 256
            py = -rel_y * scale + 256
            
            return px, py
        else:
            # 原始的简单投影
            return x * 470 + 256, -y * 470 + 256

    def extract_keypoints_2d(self, pose_json):
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
                        px, py = self.pose3d_to_pixel(kp3d[idx], kp3d[idx + 1], camera_info)
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
                        px, py = self.pose3d_to_pixel(kp3d[idx], kp3d[idx + 1], camera_info)
                        kps.append((int(px * scale_x), int(py * scale_y)))
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
        else:
            dw_pose_np = self.render_dw_pose(pose_data, output_width, output_height)
            
            # Directly use posture_description from frontend
            try:
                data = json.loads(pose_data)
                posture_text = data.get("posture_description", "标准站立姿势")
            except:
                posture_text = "标准站立姿势"

        dw_pose_image = torch.from_numpy(dw_pose_np.astype(np.float32) / 255.0).unsqueeze(0)
        return (dw_pose_image, posture_text)
