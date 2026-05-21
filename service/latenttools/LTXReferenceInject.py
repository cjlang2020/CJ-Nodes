"""
LTXReferenceInject
==================
Injects VAE-encoded reference images into LTX cross-attention (attn2) as
additional K/V tokens.

Unlike CLIP-based approaches, VAE latent tokens are in the model's NATIVE
representation space, so the model can correctly interpret the visual
information and use it for generation.

Architecture:
  ref_image → VAE encode → [1, 128, H, W] latent
    → flatten spatial → [1, H*W, 128]
    → Linear(128 → model_dim) → [1, H*W, model_dim]
    → concatenate to text K/V in each attn2
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import comfy.model_management
import comfy.utils


class LatentTokenProjector(nn.Module):
    """Projects VAE latent features to model's cross-attention dimension."""

    def __init__(self, in_channels: int, model_dim: int):
        super().__init__()
        self.proj = nn.Linear(in_channels, model_dim, bias=False)
        nn.init.xavier_uniform_(self.proj.weight, gain=0.5)

    def forward(self, latent_flat: torch.Tensor):
        return self.proj(latent_flat)


def _detect_model_config(model):
    diff_model = model.model.diffusion_model
    if not hasattr(diff_model, "transformer_blocks"):
        raise ValueError("Model does not have transformer_blocks — not an LTX model.")
    blocks = diff_model.transformer_blocks
    if len(blocks) == 0:
        raise ValueError("Model has no transformer blocks.")
    first = blocks[0]
    if hasattr(first, "attn2"):
        return first.attn2.to_k.out_features, ["attn2"]
    raise ValueError("Unsupported block type — no attn2 found.")


def _build_patched_forward(img_k: torch.Tensor, img_v: torch.Tensor):
    """Patched forward: inject image K/V tokens into attn2."""

    def patched_forward(self, x, context=None, mask=None, pe=None, k_pe=None, transformer_options={}):
        from comfy.ldm.lightricks.model import apply_rotary_emb
        import comfy.ldm.modules.attention as attn_mod

        q = self.q_norm(self.to_q(x))
        context = x if context is None else context

        k_text = self.k_norm(self.to_k(context))
        v_text = self.to_v(context)

        if img_k is not None:
            batch = q.shape[0]
            k_img = img_k.to(dtype=q.dtype, device=q.device).unsqueeze(0).expand(batch, -1, -1)
            v_img = img_v.to(dtype=q.dtype, device=q.device).unsqueeze(0).expand(batch, -1, -1)
            k = torch.cat([k_text, k_img], dim=1)
            v = torch.cat([v_text, v_img], dim=1)
            if mask is not None:
                pad = torch.zeros(mask.shape[0], mask.shape[1], k_img.shape[1],
                                  device=mask.device, dtype=mask.dtype)
                mask = torch.cat([mask, pad], dim=-1)
        else:
            k = k_text
            v = v_text

        if pe is not None:
            q = apply_rotary_emb(q, pe)
            k = apply_rotary_emb(k, pe if k_pe is None else k_pe)

        if mask is None:
            out = attn_mod.optimized_attention(
                q, k, v, self.heads,
                attn_precision=self.attn_precision,
                transformer_options=transformer_options,
            )
        else:
            out = attn_mod.optimized_attention_masked(
                q, k, v, self.heads, mask,
                attn_precision=self.attn_precision,
                transformer_options=transformer_options,
            )

        if self.to_gate_logits is not None:
            gate_logits = self.to_gate_logits(x)
            b, t, _ = out.shape
            out = out.view(b, t, self.heads, self.dim_head)
            out = out * (2.0 * torch.sigmoid(gate_logits)).unsqueeze(-1)
            out = out.view(b, t, self.heads * self.dim_head)

        return self.to_out(out)

    return patched_forward


class LTXReferenceInject:
    """
    Inject VAE-encoded reference images into LTX cross-attention.

    Uses the model's own VAE to encode images into latent space, then
    injects the latent features as additional K/V tokens in each attn2.
    Because the features are in the model's native representation space,
    the model can correctly interpret the visual information.

    For multiple images: stack as batch, use comma-separated strengths.
    For semantic separation (person from img0, bg from img1), pair with
    LTX Director's temporal prompt segmentation.

    Inputs:
      model         — LTX model (MODEL)
      vae           — Video VAE (VAE)
      ref_images    — batch of images (IMAGE, N×H×W×C)
      strengths     — per-image strength, comma-separated
      latent_resolution — spatial resolution for VAE encoding (e.g. 32=1024x512)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "vae": ("VAE",),
                "ref_images": ("IMAGE",),
                "strengths": ("STRING", {
                    "default": "1.0",
                    "tooltip": "Per-image strengths, comma-separated. "
                               "Higher = more influence."
                }),
                "latent_resolution": ("INT", {
                    "default": 32, "min": 16, "max": 128, "step": 8,
                    "tooltip": "VAE encode resolution divisor. "
                               "32 for LTX (width/32, height/32 spatial tokens)."
                }),
            }
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "apply"
    CATEGORY = "luy/ltx"

    def apply(self, model, vae, ref_images, strengths="1.0", latent_resolution=32):
        strength_list = [float(s.strip()) for s in strengths.split(",") if s.strip()]
        num_images = ref_images.shape[0]

        while len(strength_list) < num_images:
            strength_list.append(strength_list[-1] if strength_list else 1.0)
        strength_list = strength_list[:num_images]

        if all(s <= 0 for s in strength_list):
            return (model,)

        device = comfy.model_management.intermediate_device()
        model_dim, attrs = _detect_model_config(model)
        diff_model = model.model.diffusion_model
        model_dtype = diff_model.dtype

        in_channels = getattr(vae, "latent_channels", 128)

        projector = LatentTokenProjector(in_channels, model_dim)
        projector.to(device=device, dtype=model_dtype)

        all_k, all_v = [], []

        for i in range(num_images):
            img = ref_images[i:i + 1]

            # vae.encode handles 4D→5D, device management, scaling
            latent = vae.encode(img[:, :, :, :3].contiguous())  # [1, 128, 1, H', W']
            latent = latent.to(dtype=model_dtype).squeeze(2)  # [1, 128, H', W']

            latent_flat = latent.flatten(2).permute(0, 2, 1)  # [1, H'*W', 128]

            k_i = projector(latent_flat)
            v_i = projector(latent_flat)
            all_k.append(k_i * strength_list[i])
            all_v.append(v_i * strength_list[i])

        img_k = torch.cat(all_k, dim=1).squeeze(0)
        img_v = torch.cat(all_v, dim=1).squeeze(0)

        model_clone = model.clone()
        patched_fn = _build_patched_forward(img_k, img_v)

        for idx, block in enumerate(diff_model.transformer_blocks):
            for attr in attrs:
                module = getattr(block, attr, None)
                if module is None:
                    continue
                model_clone.add_object_patch(
                    f"diffusion_model.transformer_blocks.{idx}.{attr}.forward",
                    patched_fn.__get__(module, module.__class__),
                )

        projector.to("cpu")
        del projector, img_k, img_v

        return (model_clone,)


NODE_CLASS_MAPPINGS = {
    "LTXReferenceInject": LTXReferenceInject,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXReferenceInject": "LTX Reference Inject",
}
