import openai
import json
import time
import re

# Try to import the new v1+ client class
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Decide which OpenAI interface to use
_USE_V0 = hasattr(openai, "ChatCompletion")


class StoryAgent:
    def __init__(self, api_key, state, use_ai=True):
        self.use_ai  = use_ai
        self.state   = state
        self.history = []  # keep last few scene texts

        # Build a flat lookup of all locations and subareas
        self._build_world_map_hierarchy()

        # If loading from a saved state, initialize current_location
        saved = self.state.story_outline.get("current_location")
        if saved:
            self.state.current_location = {
                "location_name":        saved.get("location_name"),
                "subarea_name":         saved.get("subarea_name"),
                "subarea_description":  saved.get("subarea_description"),
            }

        if self.use_ai:
            if _USE_V0:
                openai.api_key = api_key
                self.client = openai
            else:
                if OpenAI is None:
                    raise RuntimeError("OpenAI v1+ is required but not installed.")
                self.client = OpenAI(api_key=api_key)

    def _build_world_map_hierarchy(self):
        """
        Populate `state.world_map_hierarchy` from `state.story_outline["world_data"]`
        so generate_scene can look up name/description/type for any location.
        """
        wd = self.state.story_outline.get("world_data", {})
        hierarchy = {}

        for loc in wd.get("key_locations", []):
            loc_name = loc["location_name"]
            hierarchy[loc_name] = {
                "name": loc_name,
                "description": "",
                "type": "region"
            }
            for sub in loc.get("subareas", []):
                sub_name = sub["name"]
                hierarchy[sub_name] = {
                    "name": sub_name,
                    "description": sub["description"],
                    "type": "subarea",
                    "region": loc_name
                }

        self.state.world_map_hierarchy = hierarchy

    def generate_scene(self, last_choice=None, retries=2):
        """
        Generate one scene snippet plus 3 branching options,
        enriched with world_data and your precise instructions.
        Also asks the model to indicate if the player has moved to a new subarea.
        """
        if not self.use_ai:
            raise ValueError("AI generation is not enabled.")

        # 1) Gather act & snippet info
        idx            = self.state.current_act_index
        total_acts     = len(self.state.acts)
        act_title      = self.state.acts[idx]
        num_snips      = self.state.act_snippet_counts[idx]
        act_obj        = self.state.story_outline["plot_outline"]["five_act_plan"][idx]
        inciting_text  = act_obj["inciting_incident"]
        tied_mystery   = act_obj["tied_mystery"]
        tie_npc_id     = act_obj["tie_npc"]

        # 2) Mystery details
        mystery_obj = next(m for m in self.state.story_outline["mysteries"]
                           if m["id"] == tied_mystery)

        # 3) NPCs & who’s present
        all_npcs    = [n["name"] for n in self.state.story_outline["npcs"]]
        present_ids = getattr(self.state, "current_party", [])
        present     = [n["name"] for n in self.state.story_outline["npcs"] if n["id"] in present_ids]
        npc_list     = "All NPCs: " + ", ".join(all_npcs) + "."
        present_list = "Present with you: " + (", ".join(present) if present else "None") + "."

        # 4) Memory of last 4 snippets
        mem_summary = ""
        recent = self.state.story_memory.get("recent_snippets", [])
        if recent:
            mem_summary = "Recent scenes:\n" + "\n\n".join(recent) + "\n\n"


        # 5) Player backstory
        pb           = self.state.story_outline["player_backstory"]
        first_sent   = pb["origin_story"].split('.', 1)[0] + "."
        backstory_summary = (
            f"{pb['name']}’s origin: {first_sent} "
            f"Starting traits: {pb['starting_traits']}."
        )

        # 6) World overview & factions
        wd             = self.state.story_outline["world_data"]
        overview       = wd["world_overview"]
        factions_descr = "; ".join(f"{f['name']} ({f['description']})" for f in wd["factions"])
        faction_summary = "Factions: " + factions_descr + "."

        # 7) Location metadata (from state.current_location)
        cur_loc = getattr(self.state, "current_location", {})
        loc_name = cur_loc.get("subarea_name", "[Unknown]")
        loc_desc = cur_loc.get("subarea_description", "")
        loc_type = f"subarea of {cur_loc.get('location_name', '')}"
        location_summary = f"Location: {loc_name} ({loc_type})\nDescription: {loc_desc}\n\n"

        # 8) Companion info
        comp_name = getattr(self.state, "companion_name", "")
        comp_desc = getattr(self.state, "companion_description", "")

        # 9) Last choices
        last_choices = getattr(self.state, "last_scene_choices", [])
        choice_list = ""
        if last_choices:
            lines = [f"{i+1}. {c}" for i, c in enumerate(last_choices)]
            choice_list = "The player's previous choices:\n" + "\n".join(lines) + "\n\n"

        # 10) Build prompt
        prompt  = f"INTERACTIVE {self.state.selected_genre.upper()} — ACT {idx+1}/{total_acts}: \"{act_title}\"\n"
        prompt += f"Inciting Incident: {inciting_text}\n"
        prompt += (
            f"Tied Mystery: {mystery_obj['prompt']}  "
            f"(Answer: {mystery_obj['answer']}; Twist: {mystery_obj['twist']})\n"
        )
        prompt += npc_list + "\n" + present_list + "\n\n"
        prompt += mem_summary
        prompt += backstory_summary + "\n\n"
        prompt += f"World Overview: {overview}\n{faction_summary}\n\n"
        prompt += location_summary
        prompt += choice_list
        if last_choice:
            prompt += f"The player chose: '{last_choice}'.\n\n"
        prompt += "Player Profile: " + ", ".join(f"{k}:{v}" for k,v in self.state.player_profile.items()) + "\n"
        if comp_name:
            prompt += f"Companion: {comp_name} — {comp_desc}.\n\n"

        # Enforce dialogue lines each on their own line in the required format
        prompt += (
            "— Continue the scene in 10-15 paragraphs, alternating narrative (2-3 sentences each) and "
            "dialogue lines, each on its own line in this exact format:\n"
            "Full Character Name: \"Their words.\"\n"
            "Do NOT include any narrative in the same line as dialogue, nor any dialogue in the narrative paragraphs. "
            "After the generated scene, provide exactly 3 numbered branching options, labeled 1., 2., 3., "
            "which can be either dialogue or actions taken by the player's character.\n\n"
            "Make sure to naturally draw the story towards a decisive point that is in line with the current act."
            "Begin:\n"
        )

        # 11) Call OpenAI & parse
        for attempt in range(retries):
            try:
                messages = [
                    {"role": "system", "content":
                        "You write immersive interactive scenes with tight continuity."},
                    {"role": "user",   "content": prompt}
                ]

                if _USE_V0:
                    resp = self.client.ChatCompletion.create(
                        model="gpt-4",
                        messages=messages,
                        max_tokens=800,
                        temperature=0.75,
                        request_timeout=60
                    )
                    raw = resp.choices[0].message.content.strip()
                else:
                    resp = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=messages,
                        max_tokens=800,
                        temperature=0.75,
                        timeout=60
                    )
                    raw = resp.choices[0].message.content.strip()

                scene, choices = self._parse_output(raw)

                # Advance snippet/act counters
                self.state.act_snippet_counter += 1
                if self.state.act_snippet_counter >= num_snips:
                    self.state.advance_act()

                # Apply any location update
                # self._apply_location_update(raw)

                return scene, choices

            except Exception as e:
                print(f"[WARNING] Story generation attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)

        # 12) Fallback
        return (
            "The story stalls for a moment as you consider your next move.",
            [
                "Continue cautiously and observe.",
                "Take a bold action.",
                "Reflect silently."
            ]
        )

    def _parse_output(self, output):
        """
        Splits the model's output into:
          - scene text (up to the first “1.”)
          - exactly 3 choice strings
        """
        lines   = output.splitlines()
        scene   = []
        choices = []

        for line in lines:
            if re.match(r"\s*1\.\s+", line):
                break
            scene.append(line.rstrip())

        for line in lines:
            m = re.match(r"\s*(\d+)\.\s*(.+)", line)
            if m and 1 <= int(m.group(1)) <= 3:
                choices.append(m.group(2).strip())

        while len(choices) < 3:
            choices.append("Continue cautiously.")

        scene_text = "\n".join(scene).strip()
        
        if scene_text:
            # keep only the last 4 snippets
            self.history.append(scene_text)
            self.history = self.history[-4:]

            # persist into the GameState so it survives reloads
            self.state.story_memory["recent_snippets"] = list(self.history)

        scene = self._normalize_dialogue_names(scene_text)
        
        return scene_text, choices

    def _apply_location_update(self, raw):
        """
        Parses a LocationUpdate JSON from the raw output, and if moved=True,
        updates self.state.current_location accordingly.
        """
        m = re.search(r"LocationUpdate:\s*(\{.*\})", raw)
        if not m:
            return

        try:
            info = json.loads(m.group(1))
        except Exception:
            return

        if info.get("moved"):
            new_loc = info.get("new_location")
            node = self.state.world_map_hierarchy.get(new_loc)
            if node and node.get("type") == "subarea":
                region = node.get("region")
                desc   = node.get("description", "")
                self.state.current_location = {
                    "location_name":       region,
                    "subarea_name":        new_loc,
                    "subarea_description": desc
                }

    def _normalize_dialogue_names(self, scene_text: str) -> str:
        """
        For every line matching “Speaker: "…"" check if Speaker (case-insensitive)
        is one of your known characters (player, companion, NPCs). If so, replace
        it with the exact name from state; otherwise leave it alone.
        """
        # Build a lookup of proper names
        known = { }
        # player
        player = self.state.story_outline["player_backstory"]["name"]
        known[player.lower()] = player
        # companion
        comp = getattr(self.state, "companion_name", "")
        if comp:
            known[comp.lower()] = comp
        # NPCs
        for npc in self.state.story_outline.get("npcs", []):
            name = npc["name"]
            known[name.lower()] = name

        def fix_line(line):
            m = re.match(r'^([^:]+):\s*"(.*)"$', line)
            if not m:
                return line
            speaker, rest = m.groups()
            key = speaker.strip().lower()
            if key in known:
                return f'{known[key]}: "{rest}"'
            return line

        return "\n".join(fix_line(l) for l in scene_text.splitlines())
