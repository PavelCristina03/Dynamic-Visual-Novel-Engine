import os
import openai
import logging
import requests
import time
from typing import Optional

class CharacterImageAgent:
    """
    Generates visual-novel–style character portraits using DALL·E.
    Now also accepts a 'genre' parameter and 'artstyle' parameter to tailor prompts.
    For each character, crafts a succinct prompt to produce a head–and–shoulders bust with an anime/visual-novel aesthetic,
    consistent lighting, and expressive features.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        debug: bool = False,
        genre: Optional[str] = None,
        artstyle: Optional[str] = None   # New parameter
    ):
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # Portraits are typically square for visual novel interfaces.
        self.image_size = "512x512"
        self.debug = debug
        self.genre = genre        # Store the genre for possible prompt adjustments
        self.artstyle = artstyle  # New: store global artstyle

    def generate_character_image(
        self,
        name: str,
        description: str,
        traits: dict,
        visual_description: Optional[str] = None,
        size: Optional[str] = None
    ) -> str:
        # — Sanitize inputs —
        safe_desc = " ".join(description.split())
        safe_visual = " ".join(visual_description.split()) if visual_description else None

        # — Build prompt —
        style_phrase = f"Artstyle: {self.artstyle}, " if self.artstyle else ""
        genre_phrase = f"Genre: {self.genre}. " if self.genre else ""
        if safe_visual:
            dalle_prompt = (
                f"{style_phrase}{genre_phrase}"
                f"{safe_visual}, head-and-shoulders bust on a plain background, "
                "no UI elements or text, consistent lighting, expressive features."
            )
        else:
            dalle_prompt = (
                f"{style_phrase}{genre_phrase}"
                f"Head-and-shoulders bust: {safe_desc}, on a plain background, "
                "no UI or interface, no text, consistent lighting, expressive features."
            )

        if self.debug:
            logging.debug(f"[CharacterImageAgent] DALL·E prompt: {dalle_prompt}")

        # — 1) DALL·E with retries —
        dalle_kwargs = {
            "prompt": dalle_prompt,
            "model": "dall-e-3",
            "size": size or self.image_size,
        }
        url = ""
        for attempt in range(3):
            try:
                resp = openai.Image.create(**dalle_kwargs)
                if self.debug:
                    logging.debug(f"[CharacterImageAgent] DALL·E response (try {attempt+1}): {resp}")
                candidate = resp["data"][0].get("url", "")
                if candidate:
                    url = candidate
                    break
                logging.warning(f"[CharacterImageAgent] No URL returned (try {attempt+1})")
            except Exception:
                logging.exception(f"[CharacterImageAgent] DALL·E error on try {attempt+1}")
            time.sleep(2 ** attempt)

        # — 2) Download with retries —
        if url:
            folder = "character_portraits"
            os.makedirs(folder, exist_ok=True)
            filename = f"{name.strip().lower().replace(' ', '_')}.png"
            path = os.path.join(folder, filename)

            for dl_try in range(3):
                try:
                    r = requests.get(url, timeout=10)
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        f.write(r.content)
                    if self.debug:
                        logging.debug(f"[CharacterImageAgent] Downloaded image to {path}")
                    return path
                except Exception:
                    logging.exception(f"[CharacterImageAgent] Download error (try {dl_try+1})")
                    time.sleep(2 ** dl_try)

            # if all downloads fail, return URL
            return url

        # — Fallback silhouette —
        if self.debug:
            logging.debug("[CharacterImageAgent] Fallback: returning silhouette")
        return "character_portraits/unknown_character.png"
