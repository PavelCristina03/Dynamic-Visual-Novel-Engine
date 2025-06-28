import logging
import json
import openai


class BranchingAgent:
    def __init__(self, state, api_key=None, use_ai=True):
        self.state = state
        self.use_ai = use_ai
        self.api_key = api_key

        if self.use_ai:
            openai.api_key = api_key

        if not self.state.branch_map:
            self.state.branch_map = {"0": {}}
            self.state.current_story_point = "0"
            self.state.record_location("0")

    def update_story_point(self, choice_index, choices, scene_text=None):
        current = self.state.current_story_point
        text = choices[choice_index]
        next_id = str(self.state.next_node_id)
        self.state.next_node_id += 1

        self.state.branch_map[current][text] = next_id
        self.state.branch_map[next_id] = {}
        self.state.current_story_point = next_id
        self.state.record_location(next_id)
        self.state.add_memory(text)

        if self.use_ai and scene_text:
            self.check_map_transition(scene_text, text)
            
        if scene_text:
            self.update_party_from_scene(scene_text)


    def visualize_branch_map(self, max_depth=3):
        def build(node, depth=0):
            if depth > max_depth or node not in self.state.branch_map:
                return ""
            s = "  " * depth + f"{node}:\n"
            for ch, child in self.state.branch_map[node].items():
                s += "  " * (depth + 1) + f"{ch} -> {child}\n"
                s += build(child, depth + 2)
            return s

        print("Branch Map:")
        print(build("0"))

    def check_map_transition(self, scene_text, choice_text):
        """
        Uses GPT-4 to decide whether a location change has occurred.
        Updates GameState accordingly and logs changes.
        """
        place_list = list(self.state.world_map_hierarchy.keys())

        prompt = f"""
The following is a scene from a visual novel, followed by a choice the player made.

SCENE:
{scene_text}

CHOICE:
{choice_text}

Below is a list of all valid locations in the game world:
{json.dumps(place_list)}

Did the player move to a new location within this scene, including after their choice? 
Respond with a JSON object:
{{"moved": true, "new_location": "Subarea Name"}} if a valid place from the list,
or {{"moved": false}} otherwise.
""".strip()

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're a game continuity checker for a text-based adventure."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)

            if result.get("moved"):
                new_loc = result.get("new_location")
                if new_loc in self.state.world_map_hierarchy:
                    node = self.state.world_map_hierarchy[new_loc]
                    if node.get("type") == "subarea":
                        region = node["region"]
                        desc = node.get("description", "")
                        self.state.current_location = {
                            "location_name": region,
                            "subarea_name": new_loc,
                            "subarea_description": desc
                        }
                        self.state.current_location_name = new_loc
                        self.state.record_location(new_loc)
                        print(f"[LOG] Player moved to: {new_loc} — {desc}")
        except Exception as e:
            print(f"[ERROR] Location transition check failed: {e}")

    def check_backstory_visits(self):
        """
        Uses GPT-4 to estimate which locations the player has previously visited
        based on their backstory. Adds them to visited_by_backstory if valid.
        """
        backstory = self.state.story_outline.get("player_backstory", {}).get("origin_story", "")
        place_list = list(self.state.world_map_hierarchy.keys())

        if not backstory or not place_list:
            return

        prompt = f"""
The player has the following backstory:
"{backstory}"

Here is a list of all possible locations in the game world:
{json.dumps(place_list)}

Based only on the backstory, which locations would the player most likely have visited before the game began?
Respond with a JSON array of location names taken from the list above. Do not include any other locations.
""".strip()

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You're a world-building assistant for a branching visual novel."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            suggested = json.loads(content)

            for loc in suggested:
                if loc in self.state.world_map_hierarchy and loc not in self.state.visited_by_backstory:
                    self.state.visited_by_backstory.append(loc)
                    print(f"[LOG] Backstory visit inferred: {loc}")

        except Exception as e:
            print(f"[ERROR] Backstory location check failed: {e}")

    def update_party_from_scene(self, scene_text: str):
        """
        Updates the party based on which NPCs speak or are mentioned in the scene.
        Adds new ones with dialogue, removes those who are no longer present.
        """
        if not scene_text:
            return

        npcs = self.state.story_outline.get("npcs", [])
        name_to_id = {npc["name"]: npc["id"] for npc in npcs}
        id_to_name = {npc["id"]: npc["name"] for npc in npcs}
        current_party_ids = set(self.state.current_party)

        mentioned_by_dialogue = set()
        mentioned_by_name = set()

        # Check for exact matches of dialogue lines (Name: "...")
        for line in scene_text.splitlines():
            line = line.strip()
            if ":" in line and '"' in line:
                speaker = line.split(":", 1)[0].strip()
                if speaker in name_to_id:
                    mentioned_by_dialogue.add(name_to_id[speaker])

        # Check for name mentions anywhere in text
        scene_lower = scene_text.lower()
        for name, npc_id in name_to_id.items():
            if name.lower() in scene_lower:
                mentioned_by_name.add(npc_id)

        # Add new party members with dialogue
        for npc_id in mentioned_by_dialogue:
            if npc_id not in current_party_ids:
                self.state.current_party.append(npc_id)
                print(f"[LOG] Added '{id_to_name[npc_id]}' to current party.")

        # Remove party members who are neither speaking nor mentioned
        updated_party = []
        for npc_id in self.state.current_party:
            if npc_id in mentioned_by_dialogue or npc_id in mentioned_by_name:
                updated_party.append(npc_id)
            else:
                print(f"[LOG] Removed '{id_to_name[npc_id]}' from party (no longer present).")

        self.state.current_party = updated_party

