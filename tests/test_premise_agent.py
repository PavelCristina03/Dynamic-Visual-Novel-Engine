# test_premise_agent.py

import os
import json
import logging

from dotenv import load_dotenv
from agents.premise_agent import PremiseAgent

# ¹ Load all variables from .env into os.environ
load_dotenv()

# Configure logging so you can see any debug/validation messages
logging.basicConfig(level=logging.DEBUG)


class DummyState:
    """
    A minimal stand‐in for whatever 'state' object PremiseAgent expects.
    Just needs a 'selected_genre' attribute, and will receive 'story_outline'.
    """
    def __init__(self, genre: str):
        self.selected_genre = genre
        self.story_outline = None


def main():
    # ² After load_dotenv(), this reads the key from your .env file:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment. Make sure .env is present and formatted correctly.")

    # Create a dummy state with your chosen genre
    state = DummyState(genre="fantasy")

    # Instantiate the PremiseAgent
    agent = PremiseAgent(api_key=api_key, state=state)

    # Call generate_premise (with default retries=2)
    outline = agent.generate_premise()

    # Pretty-print the resulting JSON structure
    print(json.dumps(outline, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
