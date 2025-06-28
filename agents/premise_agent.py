import openai
import json
import logging
import time
import os

from jsonschema import validate, ValidationError

class PremiseAgent:
    def __init__(self, api_key, state):
        self.state = state
        openai.api_key = api_key
        self.client = openai

    def _load_schema(self):
        this_dir = os.path.dirname(__file__)
        path = os.path.join(this_dir, "schemas", "premise_schema.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_default(self):
        this_dir = os.path.dirname(__file__)
        path = os.path.join(this_dir, "defaults", "default_premise.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_premise(self, retries=4):
        """
        1) Load and attach the JSON schema as a function parameter.
        2) Call GPT-4, asking it to generate exactly the required counts:
           - 5 key_locations (each 1–4 subareas)
           - 3–5 factions
           - 4 mysteries
           - 5–6 npcs
           - 5 acts (12–35 scenes each)
           plus player_backstory and current_location.
        3) Clamp traits, inject current_location, validate against schema.
        4) Retry up to `retries` times if validation fails.
        5) Otherwise fall back to your default JSON.
        """
        self.state.story_outline = {}
        genre = self.state.selected_genre

        # 1) Load schema
        try:
            schema = self._load_schema()
        except Exception as e:
            logging.error(f"[PremiseAgent] Failed to load schema: {e}")
            schema = None

        if schema:
            function_def = {
                "name": "generate_story_premise",
                "description": "Generate a complete story premise according to the provided schema.",
                "parameters": schema
            }

            system_prompt = (
                "You are an expert story designer. You MUST return exactly one function call "
                "\"generate_story_premise\" with JSON that *strictly* matches the given schema. "
                "Produce no other text."
            )

            user_prompt = (
                f"I need a richly detailed, immersive {genre} world. Follow these counts exactly:\n"
                "• **world_data.key_locations**: EXACTLY 5 entries, each with:\n"
                "    - `location_name` (string)\n"
                "    - `subareas`: 1-4 entries, each with `name` & multi-sentence `description`\n"
                "• **world_data.factions**: EXACTLY 3-5 entries, each with `name` & multi-sentence `description`\n"
                "• **mysteries**: EXACTLY 4 entries, with ids “m1”-“m4”, and `prompt`, `answer`, `twist`\n"
                "• **npcs**: EXACTLY 5-6 entries, each with id “npc1”-“npc6”, plus `name`, `role`, multi-sentence `description`, `goal`, 3-5 sentence `visual_description`\n"
                "• **player_backstory**: has `name`, ≥4-sentence `origin_story` referencing at least one NPC id and one mystery id, and `starting_traits` of five integers 1-5\n"
                "• **plot_outline.five_act_plan**: EXACTLY 5 acts, each with `act_title`, `inciting_incident`, `tied_mystery` (m1-m4), `tie_npc` (npc1-npc6), `twist`, and `scenes_count` (integer 12–35).\n\n"
                "After you generate `world_data.key_locations`, also set **current_location** to the first location's first subarea, "
                "including `location_name`, `subarea_name`, `subarea_description`.\n\n"
                "Return ONLY a JSON argument to `generate_story_premise`—no explanations, no extra fields."
            )

            messages = [
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_prompt}
            ]

            # 2) Retry loop
            for attempt in range(1, retries + 1):
                try:
                    resp = self.client.ChatCompletion.create(
                        model="gpt-4-0613",
                        messages=messages,
                        functions=[function_def],
                        function_call={"name": "generate_story_premise"},
                        temperature=0.8,
                        max_tokens=6000,
                        request_timeout=180
                    )

                    call = resp.choices[0].message.get("function_call")
                    if not call:
                        raise ValueError("No function_call returned")

                    outline = json.loads(call["arguments"])

                    # 3a) Clamp traits
                    traits = outline.get("player_backstory", {}).get("starting_traits", {})
                    for t in ("bravery","curiosity","empathy","communication","trust"):
                        raw = traits.get(t, 1)
                        try:
                            traits[t] = max(1, min(int(raw), 10))
                        except:
                            traits[t] = 1

                    # 3b) Inject current_location
                    try:
                        kl0 = outline["world_data"]["key_locations"][0]
                        sa0 = kl0["subareas"][0]
                        current = {
                            "location_name":       kl0["location_name"],
                            "subarea_name":        sa0["name"],
                            "subarea_description": sa0["description"]
                        }
                        outline["current_location"] = current
                    except:
                        pass

                    # 3c) Validate
                    validate(instance=outline, schema=schema)

                    # Success!
                    self.state.story_outline    = outline
                    self.state.current_location = outline.get("current_location", {})
                    return outline

                except ValidationError as ve:
                    logging.warning(f"[PremiseAgent] Attempt {attempt} schema error: {ve.message}")
                except Exception as e:
                    logging.warning(f"[PremiseAgent] Attempt {attempt} failed: {e}")

                # exponential backoff
                time.sleep(2 ** (attempt - 1))

            logging.error("[PremiseAgent] All attempts failed schema validation or API.")

        # 4) Fallback to default
        logging.warning("[PremiseAgent] Loading default premise JSON.")
        try:
            default = self._load_default()
        except Exception as e:
            logging.error(f"[PremiseAgent] Failed to load default: {e}")
            default = {}

        # Inject current_location into default
        try:
            kl0 = default["world_data"]["key_locations"][0]
            sa0 = kl0["subareas"][0]
            default["current_location"] = {
                "location_name":       kl0["location_name"],
                "subarea_name":        sa0["name"],
                "subarea_description": sa0["description"]
            }
            self.state.current_location = default["current_location"]
        except:
            pass

        self.state.story_outline = default
        return default
