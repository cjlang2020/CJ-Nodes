import torch
import comfy.utils
import comfy.model_management
import nodes
import node_helpers


class PainterMultiF2V:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "width": ("INT", {"default": 832, "min": 16, "max": nodes.MAX_RESOLUTION, "step": 16}),
                "height": ("INT", {"default": 480, "min": 16, "max": nodes.MAX_RESOLUTION, "step": 16}),
                "length": ("INT", {"default": 81, "min": 1, "max": nodes.MAX_RESOLUTION, "step": 4}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096}),
            },
            "optional": {
                "positive": ("LIST",),
                "negative": ("LIST",),
                "start_image": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT", "INT")
    RETURN_NAMES = ("positive", "negative", "latent", "segment_count")
    OUTPUT_IS_LIST = (True, True, True, False)
    FUNCTION = "generate_segments"
    CATEGORY = "Painter/Wan"

    def generate_segments(self, clip, vae, width, height, length, batch_size,
                         positive=None, negative=None,
                         start_image=None, image_2=None, image_3=None, image_4=None):
        images = []
        if start_image is not None:
            images.append(start_image)
        if image_2 is not None:
            images.append(image_2)
        if image_3 is not None:
            images.append(image_3)
        if image_4 is not None:
            images.append(image_4)

        if len(images) == 0:
            raise ValueError("At least start_image must be provided")

        if len(images) == 1:
            num_segments = 1
            image_pairs = [(images[0], None)]
        else:
            num_segments = len(images) - 1
            image_pairs = [(images[i], images[i + 1]) for i in range(num_segments)]

        if positive is None:
            raise ValueError("positive is required. Please connect 'PromptList.prompt_list' to this input.")
        
        if not isinstance(positive, list):
            positive = [positive]
        
        if len(positive) != num_segments:
            raise ValueError(f"Prompt count ({len(positive)}) must match segment count ({num_segments}). "
                           f"You provided {len(images)} images, generating {num_segments} segments. "
                           f"Please ensure PromptList has {num_segments} non-empty prompts.")

        if negative is None:
            negative = [""] * num_segments
        elif not isinstance(negative, list):
            negative = [negative] * num_segments
        elif len(negative) < num_segments:
            last_neg = negative[-1] if negative else ""
            negative = negative + [last_neg] * (num_segments - len(negative))
        else:
            negative = negative[:num_segments]

        positive_out = []
        negative_out = []
        latent_out = []

        spacial_scale = vae.spacial_compression_encode()
        latent_width = width // spacial_scale
        latent_height = height // spacial_scale
        latent_length = ((length - 1) // 4) + 1

        for i, (start_img, end_img) in enumerate(image_pairs):
            prompt_text = positive[i]
            neg_text = negative[i]
            
            tokens = clip.tokenize(prompt_text)
            positive_cond = clip.encode_from_tokens_scheduled(tokens)
            
            neg_tokens = clip.tokenize(neg_text)
            negative_cond = clip.encode_from_tokens_scheduled(neg_tokens)

            latent = torch.zeros([batch_size, vae.latent_channels, latent_length, latent_height, latent_width],
                               device=comfy.model_management.intermediate_device())

            if start_img is not None:
                start_proc = comfy.utils.common_upscale(start_img[:length].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
            else:
                start_proc = None

            if end_img is not None:
                end_proc = comfy.utils.common_upscale(end_img[-length:].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
            else:
                end_proc = None

            image = torch.ones((length, height, width, 3)) * 0.5
            mask = torch.ones((1, 1, latent_length * 4, latent_height, latent_width))

            if start_proc is not None:
                image[:start_proc.shape[0]] = start_proc
                mask[:, :, :start_proc.shape[0] + 3] = 0.0

            if end_proc is not None:
                image[-end_proc.shape[0]:] = end_proc
                mask[:, :, -end_proc.shape[0]:] = 0.0

            concat_latent_image = vae.encode(image[:, :, :, :3])
            mask = mask.view(1, mask.shape[2] // 4, 4, mask.shape[3], mask.shape[4]).transpose(1, 2)

            positive_final = node_helpers.conditioning_set_values(positive_cond, {
                "concat_latent_image": concat_latent_image,
                "concat_mask": mask
            })
            negative_final = node_helpers.conditioning_set_values(negative_cond, {
                "concat_latent_image": concat_latent_image,
                "concat_mask": mask
            })

            positive_out.append(positive_final)
            negative_out.append(negative_final)
            latent_out.append({"samples": latent})

        return (positive_out, negative_out, latent_out, num_segments)


NODE_CLASS_MAPPINGS = {
    "PainterMultiF2V": PainterMultiF2V,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PainterMultiF2V": "Painter Multi F2V",
}
