# game_state.py

import json
import os
import logging

class GameState:
    def __init__(self):
        # ─── Story state ───────────────────────────────────────────────────
        self.current_story_point        = "0"
        self.player_profile             = {}
        self.selected_genre             = None
        self.global_artstyle            = None     # New: store user’s chosen artstyle
        self.plot_phase                 = "intro"
        self.turn_counter               = 0
        self.branch_map                 = {}
        self.story_memory               = {}
        self.visited_locations          = []

        # ─── Five‐act planner ───────────────────────────────────────────────
        self.acts                       = []
        self.act_snippet_counts         = []
        self.current_act_index          = 0
        self.act_snippet_counter        = 0

        # ─── Map system ─────────────────────────────────────────────────────
        self.world_map                  = {}  # adjacency dictionary
        self.world_map_hierarchy        = {}  # nested metadata
        self.visited_map_locations      = []
        self.visited_by_backstory       = []
        self.current_location_name      = None

        # ─── Node→pretty-name lookup ────────────────────────────────────────
        self.node_names                 = {}

        # ─── Companion & rest of state ─────────────────────────────────────
        self.companion_name             = None
        self.companion_description      = None
        self.companion_profile          = {}
        self.companion_visual_desc      = ""
        self.next_node_id               = 1
        self.story_outline              = None

        # ─── Inventory / Clues ─────────────────────────────────────────────
        self.inventory                  = []
        self.clues                      = []

        # ─── Party tracking ────────────────────────────────────────────────
        self.current_party              = []

        # ─── Image tracking ────────────────────────────────────────────────
        self.character_image_urls       = {}

        # ─── Resume support ────────────────────────────────────────────────
        self.last_scene_text            = None
        self.last_scene_choices         = []
        self.last_scene_image_url       = None

        # ─── Personality analysis ──────────────────────────────────────────
        # Added for PlayerProfilingAgent
        self.last_personality_analysis  = ""

        # Try to load existing save
        self.load_game()

    def save_game(self):
        save_data = {
            # Story state
            "current_story_point":       self.current_story_point,
            "player_profile":            self.player_profile,
            "selected_genre":            self.selected_genre,
            "global_artstyle":           self.global_artstyle,
            "plot_phase":                self.plot_phase,
            "turn_counter":              self.turn_counter,
            "branch_map":                self.branch_map,
            "story_memory":              self.story_memory,
            "visited_locations":         self.visited_locations,

            # Five‐act planner
            "acts":                      self.acts,
            "act_snippet_counts":        self.act_snippet_counts,
            "current_act_index":         self.current_act_index,
            "act_snippet_counter":       self.act_snippet_counter,

            # Map system
            "world_map":                 self.world_map,
            "world_map_hierarchy":       self.world_map_hierarchy,
            "visited_map_locations":     self.visited_map_locations,
            "visited_by_backstory":      self.visited_by_backstory,
            "current_location_name":     self.current_location_name,

            # Node lookup
            "node_names":                self.node_names,

            # Companion & outline
            "companion_name":            self.companion_name,
            "companion_description":     self.companion_description,
            "companion_profile":         self.companion_profile,
            "companion_visual_desc":     self.companion_visual_desc,
            "next_node_id":              self.next_node_id,
            "story_outline":             self.story_outline,

            # Inventory / Clues
            "inventory":                 self.inventory,
            "clues":                     self.clues,

            # Party
            "current_party":             self.current_party,

            # Character images
            "character_image_urls":      self.character_image_urls,

            # Resume support
            "last_scene_text":           self.last_scene_text,
            "last_scene_choices":        self.last_scene_choices,
            "last_scene_image_url":      self.last_scene_image_url,

            # Personality analysis
            "last_personality_analysis": self.last_personality_analysis,
        }
        try:
            with open("savegame.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save game: {e}")

    def load_game(self):
        if not os.path.exists("savegame.json"):
            # first‐run defaults
            self.branch_map            = {"0": {}}
            return

        try:
            with open("savegame.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load savegame: {e}")
            return

        # ─── Story state
        self.current_story_point       = data.get("current_story_point",   self.current_story_point)
        self.player_profile            = data.get("player_profile",        self.player_profile)
        self.selected_genre            = data.get("selected_genre",        self.selected_genre)
        self.global_artstyle           = data.get("global_artstyle",       self.global_artstyle)
        self.plot_phase                = data.get("plot_phase",            self.plot_phase)
        self.turn_counter              = data.get("turn_counter",          self.turn_counter)
        self.branch_map                = data.get("branch_map",            self.branch_map)
        self.story_memory              = data.get("story_memory",          self.story_memory)
        self.visited_locations         = data.get("visited_locations",     self.visited_locations)

        # ─── Five‐act planner
        self.acts                      = data.get("acts",                  self.acts)
        self.act_snippet_counts        = data.get("act_snippet_counts",    self.act_snippet_counts)
        self.current_act_index         = data.get("current_act_index",     self.current_act_index)
        self.act_snippet_counter       = data.get("act_snippet_counter",   self.act_snippet_counter)

        # ─── Map system
        self.world_map                 = data.get("world_map",             self.world_map)
        self.world_map_hierarchy       = data.get("world_map_hierarchy",   self.world_map_hierarchy)
        self.visited_map_locations     = data.get("visited_map_locations", self.visited_map_locations)
        self.visited_by_backstory      = data.get("visited_by_backstory",  self.visited_by_backstory)
        self.current_location_name     = data.get("current_location_name", self.current_location_name)

        # ─── Node lookup
        self.node_names                = data.get("node_names",            self.node_names)

        # ─── Companion & outline
        self.companion_name            = data.get("companion_name",        self.companion_name)
        self.companion_description     = data.get("companion_description", self.companion_description)
        self.companion_profile         = data.get("companion_profile",     self.companion_profile)
        self.companion_visual_desc     = data.get("companion_visual_desc", self.companion_visual_desc)
        self.next_node_id              = data.get("next_node_id",          self.next_node_id)
        self.story_outline             = data.get("story_outline",         self.story_outline)

        # ─── Inventory / Clues
        self.inventory                 = data.get("inventory",             self.inventory)
        self.clues                     = data.get("clues",                 self.clues)

        # ─── Party
        self.current_party             = data.get("current_party",         self.current_party)

        # ─── Character images
        self.character_image_urls      = data.get("character_image_urls",  self.character_image_urls)

        # ─── Resume support
        self.last_scene_text           = data.get("last_scene_text",       self.last_scene_text)
        self.last_scene_choices        = data.get("last_scene_choices",    self.last_scene_choices)
        self.last_scene_image_url      = data.get("last_scene_image_url",  self.last_scene_image_url)

        # ─── Personality analysis
        self.last_personality_analysis = data.get("last_personality_analysis", self.last_personality_analysis)

    def clamp_profiles(self, min_val=0, max_val=10):
        for profile in (self.player_profile, self.companion_profile):
            for k, v in list(profile.items()):
                profile[k] = max(min(v, max_val), min_val)

    def advance_plot_phase(self):
        self.turn_counter += 1
        if self.turn_counter > 6:
            self.plot_phase = "resolution"
        elif self.turn_counter > 3:
            self.plot_phase = "conflict"
        else:
            self.plot_phase = "intro"

    def advance_act(self):
        if self.current_act_index < len(self.acts) - 1:
            self.current_act_index += 1
            self.act_snippet_counter = 0
            print(f"[DEBUG] → ADVANCED TO ACT {self.current_act_index+1}/{len(self.acts)}")

    def add_memory(self, key, value=True):
        self.story_memory[key] = value

    def record_location(self, location):
        if location not in self.visited_map_locations:
            self.visited_map_locations.append(location)

    def add_image(self, url: str):
        if not hasattr(self, "images"):
            self.images = []
        self.images.append({'turn': self.turn_counter, 'url': url})

    def reveal_map_location(self):
        pass

    def get_revealed_map(self):
        visited = set(self.visited_map_locations) | set(self.visited_by_backstory)
        revealed = set(visited)
        for loc in visited:
            for nbr in self.world_map.get(loc, []):
                revealed.add(nbr)
        return visited, revealed

    def get_current_location_name(self):
        return self.current_location_name

    def add_inventory(self, item):
        if item not in self.inventory:
            self.inventory.append(item)

    def add_clue(self, clue):
        if clue not in self.clues:
            self.clues.append(clue)
