#!/usr/bin/env python3
import os
import logging
import shutil
from dotenv import load_dotenv

from game.game_state import GameState
from agents.premise_agent import PremiseAgent
from agents.story_agent import StoryAgent
from agents.branching_agent import BranchingAgent
from agents.profiling_agent import PlayerProfilingAgent
from agents.companion_agent import CompanionAgent
from agents.companion_generator import CompanionGenerator
from agents.image_agent import ImageAgent
from agents.character_image_agent import CharacterImageAgent

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict


class GameEngine:
    """
    A headless game engine that can be driven entirely via UI. It exposes:
      - has_save(): bool
      - resume_game(): loads existing state (no prompts)
      - start_new_game(genre, artstyle, premise_choice=None): steps through premise + returns companion list
      - select_companion(index, companion_list): records choice + generates portraits (parallel) + sets up agents
      - get_current_text() / get_current_choices() / make_choice(...) /
        get_current_image_path()
    """

    def __init__(self):
        load_dotenv()
        self.API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.API_KEY:
            raise RuntimeError("Missing OPENAI_API_KEY in environment or .env file.")

        # Prepare logger (console + file).
        self._setup_logging()

        # Game state
        self.state: Optional[GameState] = None

        # Story‐phase agents
        self._companion_options = []
        self._story_agent = None
        self._branching_agent = None
        self._profiling_agent = None
        self._companion_agent = None
        self._image_agent = None

        # Track last choice & last‐drawn image text
        self._last_choice = None
        self._first_turn = True
        self._last_image_text = None

    def _archive_old_data(self):
        portrait_dir = "character_portraits"
        generated_dir = "generated_images"
        save_file = "savegame.json"
        log_file = "game.log"
        archive_root = "archive"

        has_portraits = os.path.isdir(portrait_dir) and os.listdir(portrait_dir)
        has_generated = os.path.isdir(generated_dir) and os.listdir(generated_dir)
        has_save = os.path.isfile(save_file)
        has_log = os.path.isfile(log_file)

        if not (has_portraits or has_generated or has_save or has_log):
            return

        os.makedirs(archive_root, exist_ok=True)
        existing = [
            d for d in os.listdir(archive_root)
            if os.path.isdir(os.path.join(archive_root, d)) and d.startswith("save")
        ]
        nums = []
        for d in existing:
            try:
                nums.append(int(d.replace("save", "")))
            except ValueError:
                pass
        next_num = max(nums) + 1 if nums else 1
        save_folder = os.path.join(archive_root, f"save{next_num}")
        images_root = os.path.join(save_folder, "images")
        char_arch = os.path.join(images_root, "character_portraits")
        gen_arch = os.path.join(images_root, "generated_images")
        story_arch = os.path.join(save_folder, "story")
        os.makedirs(char_arch, exist_ok=True)
        os.makedirs(gen_arch, exist_ok=True)
        os.makedirs(story_arch, exist_ok=True)

        if has_portraits:
            for fname in os.listdir(portrait_dir):
                shutil.move(os.path.join(portrait_dir, fname), os.path.join(char_arch, fname))
        if has_generated:
            for fname in os.listdir(generated_dir):
                shutil.move(os.path.join(generated_dir, fname), os.path.join(gen_arch, fname))
        if has_save:
            shutil.move(save_file, os.path.join(story_arch, save_file))
        if has_log:
            shutil.move(log_file, os.path.join(story_arch, log_file))

        print(f"[DEBUG] Archived data to '{save_folder}/'")

    def _setup_logging(self):
        if hasattr(self, "logger"):
            for h in self.logger.handlers[:]:
                h.close()
                self.logger.removeHandler(h)

        self.logger = logging.getLogger("GameEngine")
        self.logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        fh = logging.FileHandler("game.log", mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(fmt)
        self.logger.addHandler(ch)

    def _teardown_logging(self):
        if not hasattr(self, "logger"):
            return
        for h in self.logger.handlers[:]:
            h.close()
            self.logger.removeHandler(h)

    def has_save(self) -> bool:
        return os.path.isfile("savegame.json")

    def resume_game(self):
        """
        Load existing state, generate missing player portrait, initialize agents,
        and restore image-text tracking so we don’t redraw the last scene.
        """
        self.state = GameState()

        # Backward compatibility
        if not hasattr(self.state, "character_image_urls"):
            self.state.character_image_urls = {}
        if not hasattr(self.state, "last_scene_image_url"):
            self.state.last_scene_image_url = None

        # Generate missing player portrait...
        po = self.state.story_outline["player_backstory"]
        player = po["name"]
        if player not in self.state.character_image_urls:
            cia = CharacterImageAgent(
                api_key=self.API_KEY,
                debug=True,
                genre=self.state.selected_genre,
                artstyle=self.state.global_artstyle
            )
            prompt = f"Character portrait of {player}, origin: {po['origin_story']}."
            try:
                url = cia.generate_character_image(
                    name=player,
                    description=prompt,
                    traits=self.state.player_profile,
                    visual_description=None,
                    size="1024x1024"
                )
                if url:
                    self.state.character_image_urls[player] = url
                    self.logger.debug("Generated missing player portrait: %s → %s", player, url)
                else:
                    self.logger.warning("No URL returned for player portrait: %s", player)
            except Exception as e:
                self.logger.error("Failed to generate player portrait on resume: %s", e)
            self.state.save_game()

        # Initialize all story‐phase agents
        self._initialize_story_phase_agents()

        # Clear choice flag
        self._last_choice = None

        # **Critical**: seed last‐image-text so we reuse the saved image
        self._last_image_text = self.state.last_scene_text

        self._first_turn = True
        self.logger.info("Resumed existing savegame.")

    def start_new_game(
        self,
        genre: str,
        artstyle: str,
        premise_choice: Optional[str] = None
    ) -> list:
        self._teardown_logging()
        self._archive_old_data()
        self._setup_logging()

        self.state = GameState()
        self.state.character_image_urls = {}
        self.state.last_scene_image_url = None

        self.state.selected_genre = genre
        self.state.global_artstyle = artstyle or None
        self.logger.info("New game: Genre='%s', Artstyle='%s'",
                         self.state.selected_genre, self.state.global_artstyle)

        if premise_choice is None:
            choice = input("Generate a custom premise or use the default one? (custom/default): ")
        else:
            choice = premise_choice

        agent = PremiseAgent(api_key=self.API_KEY, state=self.state)
        if choice.lower().startswith("d"):
            full = agent._load_default()
            self.logger.info("Loaded default premise.")
        else:
            full = agent.generate_premise()
            self.logger.info("Generated custom premise via AI.")

        world_data       = full["world_data"]
        plot_outline     = full["plot_outline"]
        player_backstory = full["player_backstory"]

        self.state.story_outline      = full
        self.state.acts               = [a["act_title"] for a in plot_outline["five_act_plan"]]
        self.state.act_snippet_counts = [a["scenes_count"] for a in plot_outline["five_act_plan"]]
        self.state.player_profile     = player_backstory["starting_traits"].copy()
        self.state.current_act_index   = 0
        self.state.act_snippet_counter = 0

        first_npc = plot_outline["five_act_plan"][0]["tie_npc"]
        self.state.current_party        = [first_npc]
        self.state.visited_by_backstory = player_backstory.get("starting_locations", [])

        self.state.save_game()
        self.logger.debug("Premise saved to state.")
        self._initialize_story_phase_agents()
        self._branching_agent.check_backstory_visits()


        self._companion_options = CompanionGenerator(
            api_key=self.API_KEY
        ).generate_companions(self.state.selected_genre, world_data)
        return self._companion_options

    def select_companion(self, index: int, companion_list: list):
        comp = companion_list[index]
        self.state.companion_name        = comp["name"]
        self.state.companion_description = comp["description"]
        self.state.companion_profile     = comp["traits"]
        self.state.companion_visual_desc = comp.get("visual_description", "")

        char_image_agent = CharacterImageAgent(
            api_key=self.API_KEY,
            debug=True,
            genre=self.state.selected_genre,
            artstyle=self.state.global_artstyle
        )

        tasks = []
        pb = self.state.story_outline["player_backstory"]
        tasks.append((
            "player",
            pb["name"],
            f"Character portrait of {pb['name']}, origin: {pb['origin_story']}.",
            self.state.player_profile,
            None
        ))
        tasks.append((
            "companion",
            comp["name"],
            comp["description"],
            comp["traits"],
            comp.get("visual_description", "")
        ))
        for npc in self.state.story_outline["npcs"]:
            tasks.append((
                f"npc_{npc['id']}",
                npc["name"],
                npc.get("description", ""),
                {},
                npc.get("visual_description", "")
            ))

        futures = {}
        with ThreadPoolExecutor(max_workers=len(tasks)) as exe:
            for kind, name, prompt, traits, vis in tasks:
                fut = exe.submit(
                    char_image_agent.generate_character_image,
                    name=name,
                    description=prompt,
                    traits=traits,
                    visual_description=vis,
                    size="1024x1024"
                )
                futures[fut] = (kind, name)

            for fut in as_completed(futures):
                kind, char_name = futures[fut]
                try:
                    url = fut.result()
                except Exception as e:
                    self.logger.error("Error generating portrait for %s: %s", char_name, e)
                    url = None

                if url and "unknown_character" in url:
                    self.logger.warning("Got placeholder for %s—skipping that image.", char_name)
                    url = None

                if url:
                    self.state.character_image_urls[char_name] = url
                    self.logger.debug("Portrait URL for %s: %s", char_name, url)
                else:
                    self.logger.warning("No portrait URL saved for %s", char_name)

        self.state.save_game()
        self.logger.info("All character portraits generated and saved.")
        #self._initialize_story_phase_agents()

    def _initialize_story_phase_agents(self):
        self._story_agent     = StoryAgent(api_key=self.API_KEY, state=self.state)
        self._branching_agent = BranchingAgent(api_key=self.API_KEY, state=self.state)
        self._profiling_agent = PlayerProfilingAgent(self.state)
        self._companion_agent = CompanionAgent(self.state)
        self._image_agent     = ImageAgent(
            api_key=self.API_KEY,
            debug=True,
            artstyle=self.state.global_artstyle
        )
        # only reset choice & first_turn here:
        self._last_choice = None
        self._first_turn  = True
        self.logger.info("Story-phase agents initialized.")

    def get_current_text(self) -> str:
        # If we have text and no new choice, return it
        if self.state.last_scene_text and self._last_choice is None:
            return self.state.last_scene_text

        # Real “new choice” → regenerate new snippet
        text, choices = self._story_agent.generate_scene(self._last_choice)
        self.state.last_scene_text    = text
        self.state.last_scene_choices = choices
        self._last_choice             = None # no choice made yet, as snippet was just generated
        self.state.save_game()
        self.logger.debug("[STORY] Generated new scene: %r", text)
        return text

    def get_current_choices(self) -> list:
        if getattr(self.state, "last_scene_choices", None):
            return self.state.last_scene_choices
        _ = self.get_current_text()
        return self.state.last_scene_choices or []

    def make_choice(self, choice_text: str):
        choices = self.get_current_choices()

        if choice_text in choices:
            # a preset choice button was clicked
            idx = choices.index(choice_text)
            self._profiling_agent.update_profile(idx, choices, self.state.last_scene_text or "")
            self._companion_agent.update_companion_profile(idx, choices, self.state.last_scene_text or "")
            self._branching_agent.update_story_point(idx, choices, self.state.last_scene_text or "")
            self.state.advance_plot_phase()
        else:
            # custom‐typed choice: leave idx alone (None) so StoryAgent sees raw text
            idx = None

        # record exactly what the player typed
        self._last_choice = choice_text
        self.state.save_game()

    def get_current_image_path(self) -> Optional[str]:
        # Pull the scene text
        text = self.state.last_scene_text or self.get_current_text()

        # Only regenerate if we have no image or the text has changed
        if (not self.state.last_scene_image_url
            or text != self._last_image_text):

            self.logger.debug("[IMAGE] Generating image for scene_text:\n%s", text)
            url = self._image_agent.generate_scene_image(text)
            self.state.last_scene_image_url = url
            self._last_image_text = text
            self.state.save_game()

        return self.state.last_scene_image_url

'''
if __name__ == "__main__":
    engine = GameEngine()
    if engine.has_save():
        engine.resume_game()
    else:
        genre = input("Choose a genre: ")
        style = input("Choose an artstyle (or blank): ")
        comps = engine.start_new_game(genre, style)
        print("\nPick your companion:")
        for i, c in enumerate(comps, 1):
            print(f"{i}. {c['name']} — {c['description']}")
        choice = int(input("Enter # → ")) - 1
        engine.select_companion(choice, comps)

    text = engine.get_current_text()
    print(text)
    print(engine.get_current_choices())
'''