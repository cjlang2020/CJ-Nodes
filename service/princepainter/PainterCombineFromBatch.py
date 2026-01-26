import torch
import math


class PainterCombineFromBatch:
    INPUT_IS_LIST = True
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "overlap_frames": ("INT", {"default": 5, "min": 0, "max": 50, "step": 1}),
                "trim_frames": ("INT", {"default": 0, "min": 0, "max": 20, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "combine"
    CATEGORY = "Painter/Video"

    def combine(self, images, overlap_frames, trim_frames):
        overlap = overlap_frames[0] if isinstance(overlap_frames, list) else overlap_frames
        trim = trim_frames[0] if isinstance(trim_frames, list) else trim_frames
        
        # Trim frames from the beginning of each segment
        if trim > 0:
            trimmed_images = []
            for img in images:
                if img.shape[0] > trim:
                    trimmed_images.append(img[trim:])
                else:
                    # If segment is too short, keep at least 1 frame or empty
                    if img.shape[0] > 0:
                        trimmed_images.append(img[-1:])  # Keep last frame as fallback
            images = trimmed_images
        
        if len(images) == 0:
            # Return empty tensor with correct shape if all trimmed
            empty = torch.zeros((1, 64, 64, 3), device='cpu')
            return (empty,)
        
        if len(images) == 1:
            return (images[0],)
        
        if overlap == 0:
            return (torch.cat(images, dim=0),)
        
        result_parts = []
        num_segments = len(images)
        
        for i in range(num_segments):
            curr_seg = images[i]
            curr_len = curr_seg.shape[0]
            
            if i == 0:
                # First segment: reserve tail for next blend if possible
                if curr_len > overlap:
                    result_parts.append(curr_seg[:-overlap])
                else:
                    result_parts.append(curr_seg)
            else:
                prev_seg = images[i-1]
                prev_len = prev_seg.shape[0]
                
                # Dynamic overlap: cannot exceed either segment's length
                actual_overlap = min(overlap, prev_len, curr_len)
                
                if actual_overlap > 0:
                    prev_tail = prev_seg[-actual_overlap:]
                    curr_head = curr_seg[:actual_overlap]
                    
                    # Cosine ease-in-out dissolve
                    t = torch.linspace(0, 1, actual_overlap, device=curr_seg.device).view(-1, 1, 1, 1)
                    alpha = 0.5 * (1 - torch.cos(t * math.pi))
                    blended = prev_tail * (1 - alpha) + curr_head * alpha
                    result_parts.append(blended)
                    
                    # Remaining part of current segment
                    remaining = curr_seg[actual_overlap:]
                    
                    if i < num_segments - 1:
                        # Middle segment: reserve tail for next blend
                        if remaining.shape[0] > overlap:
                            result_parts.append(remaining[:-overlap])
                        else:
                            result_parts.append(remaining)
                    else:
                        # Last segment: keep all remaining
                        result_parts.append(remaining)
                else:
                    # Segment too short for overlap, append as-is
                    result_parts.append(curr_seg)
        
        output = torch.cat(result_parts, dim=0)
        return (output,)


NODE_CLASS_MAPPINGS = {
    "PainterCombineFromBatch": PainterCombineFromBatch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PainterCombineFromBatch": "Painter Combine From Batch",
}
