import openai
import json
import logging

# Try to import the v1+ client class
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

_USE_V0 = hasattr(openai, "ChatCompletion")

class CompanionGenerator:
    def __init__(self, api_key, use_ai=True):
        self.use_ai = use_ai
        if self.use_ai:
            if _USE_V0:
                openai.api_key = api_key
                self.client = openai
            else:
                if OpenAI is None:
                    raise RuntimeError("OpenAI v1+ is required but not installed.")
                self.client = OpenAI(api_key=api_key)

    def generate_companions(self, genre, world_data=None, num=3):
        """
        Generate companions that fit the specified genre and world.

        world_data: dict containing at least 'world_name' and 'world_overview'.
        """
        if not self.use_ai:
            return self._fallback_companions()

        # Build context about the world, if available
        world_name = world_data.get("world_name", "") if world_data else ""
        world_overview = world_data.get("world_overview", "") if world_data else ""

        prompt = (
            f"Generate {num} unique companion characters for an interactive {genre} story set in the world '{world_name}'.\n"
            f"World Overview: {world_overview}\n\n"
            "For each companion, produce a JSON object with:\n"
            "  • name: string (1–3 words)\n"
            "  • description: string (one sentence summarizing their personality or role)\n"
            "  • visual_description: string (one sentence describing their appearance)\n"
            "  • traits: object with numeric values for 'trust', 'fear', 'affection'\n"
            "Return a JSON array of these companion objects."
        )

        try:
            if _USE_V0:
                resp = self.client.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You create vivid game companions with stats that fit the given world."},
                        {"role": "user",   "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.8,
                    request_timeout=30
                )
                content = resp.choices[0].message.content.strip()
            else:
                resp = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You create vivid game companions with stats that fit the given world."},
                        {"role": "user",   "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.8,
                    timeout=30
                )
                content = resp.choices[0].message.content.strip()

            data = json.loads(content)
            companions = []
            for item in data:
                if (
                    isinstance(item, dict)
                    and "name" in item
                    and "description" in item
                    and "visual_description" in item
                    and "traits" in item
                    and all(k in item["traits"] for k in ("trust", "fear", "affection"))
                ):
                    companions.append({
                        "name": item["name"],
                        "description": item["description"],
                        "visual_description": item["visual_description"],
                        "traits": {
                            k: int(item["traits"][k])
                            for k in ("trust", "fear", "affection")
                        }
                    })

            if len(companions) < num:
                raise ValueError(f"Expected {num} companions, got {len(companions)}")
            return companions[:num]

        except Exception as e:
            logging.warning(f"Companion generation failed: {e}")
            return self._fallback_companions()

    def _fallback_companions(self):
        return [
            {
                "name": "Wary Swordsman",
                "description": "A battle-scarred warrior who trusts few but fights loyally.",
                "visual_description": "A tall, heavily muscled human male with a buzzcut and numerous scars crisscrossing his arms, wearing dented chainmail.",
                "traits": {"trust": 5, "fear": 2, "affection": 3}
            },
            {
                "name": "Stoic Mage",
                "description": "A quiet spellcaster whose calm presence soothes the uneasy.",
                "visual_description": "A slender elf with pale skin, silver hair tied in a braid, and glowing emerald runes on her robes.",
                "traits": {"trust": 4, "fear": 1, "affection": 4}
            },
            {
                "name": "Cheerful Rogue",
                "description": "A nimble trickster with a heart of gold and a quick smile.",
                "visual_description": "A short halfling with curly auburn hair, bright green eyes, and a patchwork leather jacket full of hidden pockets.",
                "traits": {"trust": 3, "fear": 3, "affection": 5}
            }
        ]
