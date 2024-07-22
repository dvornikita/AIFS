from io import BytesIO
from typing import Optional

import requests
import torch
from PIL import Image

from diffusers import (
    DPMSolverMultistepScheduler,
    StableDiffusionXLPipeline,
)
from diffusers.utils import logging
from diffusers.utils.logging import set_verbosity
from caption import caption_image


set_verbosity(logging.ERROR)  # to not show cross_attention_kwargs..by AttnProcessor2_0 warnings


def get_pipeline(device: Optional[str] = "cuda") -> StableDiffusionXLPipeline:
    pipeline = StableDiffusionXLPipeline.from_pretrained(
        "SG161222/RealVisXL_V4.0", variant="fp16", torch_dtype=torch.float16
    ).to(device)

    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)
    pipeline.scheduler.config.use_karras_sigmas = True

    pipeline.load_ip_adapter(
        "h94/IP-Adapter",
        subfolder="sdxl_models",
        weight_name="ip-adapter-plus_sdxl_vit-h.safetensors",
        image_encoder_folder="models/image_encoder",
    )
    pipeline.set_ip_adapter_scale(0.4)
    pipeline.enable_freeu(s1=0.7, s2=0.7, b1=1.2, b2=1.1)
    return pipeline


def generate_image(image_path: str, pipeline=None, api_key=None, verbose=False) -> Image.Image:
    """Uses Stable Diffusion Xl pipeline to generate an image of Tylor Swift wearing the garment, based on the provided
    image_path or image_url of the garment. Uses IP-Adapter to condition generation on the image of the garment.
    """
    if image_path.startswith("http"):
        image_url = image_path
        response = requests.get(image_url)
        image_path = BytesIO(response.content)
        image_caption = caption_image(image_url=image_url, mode="recognize", api_key=api_key)
    else:
        image_caption = caption_image(image_path=image_path, mode="recognize", api_key=api_key)
    ip_image = Image.open(image_path)

    if verbose:
        print("Image Caption:", image_caption)

    prompt = f"high quality photo of a tylor swift wearing {image_caption}, highly detailed, professional, dramatic ambient light, focus, full body, high resolution, high quality, high fidelity, clear face of tylor swift, high dynamic range, high clarity, high realism"
    negative_prompt = "unrealistic face, unrealistic eyes, small eyes, long_neck, morphed, weird face, gigantic head, uneven eyes, deformed, mutated, uneven eyes, tilted head, unrealistic lips, visible tongue, bent head, hunching, strange nose, unrealistic lips, lips too large, wearing a hat, earings, artifacts around eyes and lips, blurry eyes, distorted eyes, crossed eyes, glowing eyes, oversized eyes, cartoonish eyes, misaligned eyes, blurry lips, distorted lips, uneven lips, chapped lips, asymmetrical lips, oversized lips, underdefined lips, smudged lips, cartoonish lips, unevenly lit lips, closed eyes, eyes half closed, squinted eyes"

    pipeline = pipeline or get_pipeline()
    image = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt,
        height=1024,
        width=1024,
        guidance_scale=8.5,
        num_inference_steps=25,
        ip_adapter_image=ip_image,
        strength=1,
    ).images[0]

    return image
