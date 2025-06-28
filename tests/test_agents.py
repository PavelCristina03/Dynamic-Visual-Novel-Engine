# test_agents.py

import os
import json
import logging

from dotenv import load_dotenv
from agents.premise_agent import PremiseAgent
from agents.story_agent import StoryAgent

# ¹ Load all variables from .env into os.environ
load_dotenv()

# Configure logging so you can see debug/validation messages
logging.basicConfig(level=logging.DEBUG)


class DummyPremiseState:
    """
    Minimal stand‐in for PremiseAgent's state.
    Just needs a 'selected_genre' attribute, and will receive 'story_outline'.
    """
    def __init__(self, genre: str):
        self.selected_genre = genre
        self.story_outline = None


class DummyStoryState:
    """
    Minimal stand‐in for StoryAgent's state.
    - world_map: mapping of node IDs to whatever
    - node_names: mapping of node IDs to human names
    - current_location_name: the node ID we're at
    - record_location(): called when movement is detected
    """
    def __init__(self, start_node: str, world_map: dict, node_names: dict):
        self.world_map = world_map
        self.node_names = node_names
        self.current_location_name = start_node
        self.recorded = []

    def get_current_location_name(self):
        return self.current_location_name

    def record_location(self, new_node_id: str):
        self.recorded.append(new_node_id)


def test_premise_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment.")

    # Premise test
    premise_state = DummyPremiseState(genre="fantasy")
    premise_agent = PremiseAgent(api_key=api_key, state=premise_state)
    outline = premise_agent.generate_premise()
    print("=== Premise Outline ===")
    print(json.dumps(outline, indent=2, ensure_ascii=False))
    assert isinstance(outline, dict), "Expected JSON dict from PremiseAgent"


def test_story_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment.")

    # Define a tiny map with two nodes: forest → castle
    world_map = {
        "forest": {},
        "castle": {}
    }
    node_names = {
        "forest": "Enchanted Forest",
        "castle": "Ancient Castle"
    }
    # Start in the forest
    story_state = DummyStoryState(start_node="forest", world_map=world_map, node_names=node_names)

    story_agent = StoryAgent(
        api_key=api_key,
        state=story_state,
        config_path=None,   # will fall back to defaults
        use_ai=True,
        retries=1
    )

    # Monkey-patch the actual AI call to return a snippet that clearly moves us to the castle.
    def fake_call(self, last_choice):
        snippet = "You exit the Enchanted Forest and arrive at the Ancient Castle gates."
        choices = ["Enter the castle", "Go back to the forest"]
        return snippet, choices

    StoryAgent._call_story_model = fake_call

    scene, choices = story_agent.generate_scene()
    print("\n=== Story Scene ===")
    print(scene)
    print("Choices:", choices)
    print("Recorded movement:", story_state.recorded)

    # After movement inference, we should have moved from 'forest' → 'castle'
    assert story_state.current_location_name == "castle", "Expected to infer move to 'castle'"
    assert "castle" in story_state.recorded, "Expected 'castle' to be recorded"


if __name__ == "__main__":
    test_premise_agent()
    test_story_agent()
    print("\nAll tests passed!")
