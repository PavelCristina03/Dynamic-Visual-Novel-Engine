import os
import openai
import logging
import time
import re
from typing import Optional
from io import BytesIO
from PIL import Image, ImageFilter
import requests

# Configure module-level logger
logger = logging.getLogger(__name__)

class ImageAgent:
    """
    Uses GPT-4 to craft a scenery-focused, environment-only prompt from your narrative snippet (and optional location context),
    then feeds that prompt to DALL·E-3 to generate the final image. After downloading, it applies a little sharpening/upsampling to boost quality.
    Now also supports a global 'artstyle' prefix that will be prepended to every scenery prompt and to the final DALL·E prompt itself.

    This version defaults to a DALL·E-supported landscape size (1792×1024) and upsamples to 3584×2048.
    """

    def __init__(self, api_key: Optional[str] = None, debug: bool = False, artstyle: Optional[str] = None):
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.chat_model = "gpt-4"
        self.image_model = "dall-e-3"

        # ─── Use a supported landscape resolution ────────────────────────
        self.base_size   = "1792x1024"    # DALL·E supports 1792×1024 (landscape) or 1024×1792 (portrait)
        self.upsample_to = (3584, 2048)    # Double it to keep ~16:9 aspect ratio when upscaling

        self.debug = debug
        self.artstyle = artstyle            # Optional “global artstyle” prefix

    def _generate_image_prompt(self, scene_text: str, location: Optional[str] = None) -> str:
        """
        Given the raw scene_text and an optional location name, return one
        strict, under-450 character, single-line DALL·E prompt.
        """

        # Log received scene text
        logger.debug("_generate_image_prompt received scene_text: %s", scene_text)

        style_prefix = f"(STYLE: {self.artstyle}) " if self.artstyle else ""
        loc_prefix = f"(LOCATION: {location}) " if location else ""

        # Tighter system message forbidding invented details
        system_msg = (
            "You are a professional prompt engineer. Output EXACTLY one line, under 450 characters, "
            "describing only the environment—no people, no characters, no actions. "
            "You MUST use ONLY environment details explicitly mentioned in the scene description; do NOT invent any new objects, furniture, or props. "
            "Prefer a **close-up**, detail-rich view. Include aspect ratio --ar 16:9 at the end."
        )

        user_msg = (
            f"{style_prefix}{loc_prefix}Scene description:\n"
            f"{scene_text}\n\n"
            "Now produce a concise, single-sentence DALL·E prompt. "
            "Focus on the visual elements, plus lighting, mood, and composition. "
            "Emphasize intimate, close-range detail—textures, props, walls, floor, nearby structures or furnishings. If outdoors, detail the landscape, flora, or other applicable elements."
        )

        if self.debug:
            print(
                "[DEBUG] Sending to GPT-4 for DALL·E prompt generation.\n"
                f"       System message: {system_msg}\n"
                f"       User message: {user_msg}\n"
            )

        resp = openai.ChatCompletion.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.2,
            max_tokens=200,
        )

        prompt = resp.choices[0].message.content.strip()
        if self.debug:
            print(f"[DEBUG] Received DALL·E prompt:\n  {prompt}\n")

        # Hallucination filter: ensure overlap with scene_text
        scene_words = set(re.findall(r"\w+", scene_text.lower()))
        prompt_words = set(re.findall(r"\w+", prompt.lower()))
        if not (scene_words & prompt_words):
            # fallback to raw scene_text if GPT drifts
            fallback = (
                f"{style_prefix}{loc_prefix}{scene_text} --ar 16:9"
            )
            prompt = fallback
            if self.debug:
                logger.debug("Falling back to raw scene_text for DALL·E prompt.")

        return prompt

    def _postprocess_image(self, raw_bytes: bytes, filename: str) -> Optional[str]:
        """
        Take the raw 1792x1024 image bytes, apply a mild sharpen filter,
        upscale to 3584x2048, save locally, and return that local path.
        """
        try:
            img = Image.open(BytesIO(raw_bytes)).convert("RGBA")

            # Mildly sharpen
            img = img.filter(ImageFilter.SHARPEN)

            # Upscale to 3584×2048 using bicubic
            img = img.resize(self.upsample_to, Image.Resampling.BICUBIC)

            # Ensure output directory exists
            out_dir = "generated_images"
            os.makedirs(out_dir, exist_ok=True)

            # Save to disk as PNG using provided filename
            filepath = os.path.join(out_dir, f"{filename}.png")
            img.save(filepath, format="PNG")

            return filepath
        except Exception as e:
            logger.error(f"Post-processing image failed: {e}")
            return None

    def generate_scene_image(
        self,
        scene_text: str,
        location: Optional[str] = None,
        size: Optional[str] = None
    ) -> str:
        """
        1) Generate an image prompt via GPT-4.
        2) Prepend the artstyle to the DALL·E prompt itself.
        3) Send that prompt to DALL·E-3 (1792×1024 by default, quality=hd), download bytes,
           post-process (sharpen + upscale), save to disk, and return the local path.
        """
        # Log scene_text for debugging
        logger.debug("generate_scene_image called with scene_text: %s", scene_text)

        # Create a fresh prompt from GPT
        image_prompt = self._generate_image_prompt(scene_text, location)

        # Prepend global artstyle to the final DALL·E prompt
        if self.artstyle:
            image_prompt = f"artstyle {self.artstyle} " + image_prompt

        # Log final image prompt
        logger.debug("Final DALL·E prompt: %s", image_prompt)

        try:
            if self.debug:
                print(
                    f"[DEBUG] Calling openai.Image.create(model={self.image_model}, size={self.base_size}, quality='hd') with prompt:\n"
                    f"  \"{image_prompt}\"\n"
                )

            resp = openai.Image.create(
                model=self.image_model,
                prompt=image_prompt,
                n=1,
                size=size or self.base_size,
                quality="hd"
            )
            url = resp["data"][0]["url"]

            # Download the image bytes
            img_resp = requests.get(url)
            img_resp.raise_for_status()
            raw_bytes = img_resp.content

            # Post-process: sharpen + upscale → local PNG

            # Always use incremental numeric filenames like 1.png, 2.png, etc.
            out_dir = "generated_images"
            os.makedirs(out_dir, exist_ok=True)

            existing = [
                f for f in os.listdir(out_dir)
                if f.endswith(".png") and f[:-4].isdigit()
            ]
            existing_numbers = [int(f[:-4]) for f in existing]
            next_number = max(existing_numbers) + 1 if existing_numbers else 1
            filename = str(next_number)


            final_path = self._postprocess_image(raw_bytes, filename)
            if final_path:
                if self.debug:
                    print(f"[DEBUG] Image saved locally at {final_path}\n")
                return final_path
            else:
                # If post-processing fails, return the original URL
                return url

        except Exception as e:
            logger.error(f"DALL·E generation failed: {e}")
            placeholder = "https://example.com/placeholder.png"
            return placeholder

    def generate_location_image(
        self,
        location_name: str,
        location_description: str,
        size: Optional[str] = None
    ) -> str:
        """
        Pre-generate a “background” image specifically for a location.
        """
        scene_text = f"Location: {location_name}. {location_description}"
        return self.generate_scene_image(scene_text, location=location_name, size=size)
