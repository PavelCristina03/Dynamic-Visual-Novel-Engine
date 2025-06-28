# Dynamic Visual Novel Engine

A modular, agent-driven visual novel engine powered by OpenAI’s GPT and image models. This project allows you to craft rich, branching narratives augmented with dynamically generated character portraits and scene illustrations. Each component—from story flow to image creation—is encapsulated in an _agent_, making the system highly extensible and easy to customize.

---

## 📖 What It Is

The **Dynamic Visual Novel Engine** is a Python-based framework for creating interactive visual novels where narrative, character art, and user-driven choices are all generated on the fly by AI:

-   **StoryAgent**: Drives the narrative by generating descriptive text and branching options at each step.
-   **CharacterImageAgent**: Produces or selects character portraits based on the player’s profile, mood, and story context.
-   **ImageAgent**: Generates scene illustrations that match the current narrative beat or environment.
-   **CompanionAgent & CompanionGenerator**: Manages an AI “companion” persona that interacts with the player, offering commentary or hints.
-   **PremiseAgent**: Validates and structures incoming story premises against a JSON schema, ensuring consistent data flow.
-   **ProfilingAgent**: Tracks player decisions and builds a profile (e.g., personality traits, preferences) that influences later scenes.
-   **BranchingAgent**: Orchestrates story transitions, mapping player choices to new narrative branches.

Together, these agents create a closed-loop pipeline: the player makes a choice, the engine updates the game state, agents generate the next text and images, and the UI renders them.

---

## ✨ Key Features

-   **Fully Dynamic Content**: No pre-authored story beats—every line of dialogue and illustration is generated in real time.
-   **Adaptive Story Profiles**: Player choices feed into a dynamic profile that shapes character dialogue, visual style, and branching weights.
-   **Modular Agent Architecture**: Add, remove, or extend agents with minimal changes to the core engine.
-   **Dual Interfaces**: Choose between a lightweight CLI mode (`--mode cli`) for rapid prototyping or a full-featured PySide6 GUI (`ui.py`) for a polished desktop experience.
-   **Configurable & Extensible**: Nearly every aspect (models, caching, retry logic, file paths) is set via environment variables and JSON schemas.

---

## 🏗 Architecture Overview

-   **GameEngine** (in `main.py`): Central loop and orchestrator.
-   **GameState** (`game_state.py`): Maintains persistent state (player profile, history, variables).
-   **Agents**: Independent modules that receive inputs (state, prompt) and return outputs (text, images, profiling updates).
-   **UI Layer** (`ui.py`): Renders agent outputs and captures user interactions.

---

## 🚀 Quick Start

Follow these steps to get up and running:

1. **Clone & Setup**
    ```bash
    git clone https://github.com/yourusername/dynamic-visual-novel-engine.git
    cd dynamic-visual-novel-engine
    python -m venv venv
    source venv/bin/activate or .\venv\Scripts\activate on Windows
    pip install openai python-dotenv jsonschema pillow requests PySide6
    cp .env.example .env
    ```
2. **Configure**

    - Open `.env` and set your `OPENAI_API_KEY`.
    - (Optional) Adjust other settings such as log levels, file paths, and model parameters.

3. **Run**

    python ui.py

4. **Play & Extend**
    - Modify or add agents in the `agents/` directory.
    - Tweak JSON schemas or default prompts to shape narrative style.

---

## 🛠️ Configuration & Customization

All key settings are managed via environment variables and JSON schema files:

| Variable         | Purpose                        | Default    |
| ---------------- | ------------------------------ | ---------- |
| `OPENAI_API_KEY` | API key for GPT & image models | _required_ |

See `.env.example` for the full list of options.

---

## 📂 Directory Structure

```
├── agents/                   # All agent modules
│   ├── branching_agent.py
│   ├── character_image_agent.py
│   ├── companion_agent.py
│   ├── companion_generator.py
│   ├── image_agent.py
│   ├── premise_agent.py
│   ├── profiling_agent.py
│   └── story_agent.py
├── game_state.py             # Persistent game state & save/load
├── main.py                   # Engine entry point and CLI
├── ui.py                     # PySide6 GUI implementation
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variable template
```

---

## 🤝 Contributing & License

Contributions are welcome! Please open issues and submit pull requests.  
Licensed under the MIT License.

---

© 2025 Dynamic Visual Novel Engine Project
