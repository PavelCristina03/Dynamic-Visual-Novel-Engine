import openai
import json
import logging
import time

class CompanionAgent:
    def __init__(self, state):
        self.state = state

    def infer_traits_from_choice(self, choice_text, context, retries=2):
        """
        Prompts GPT to return strictly valid JSON with float deltas for:
          - trust
          - fear
          - affection

        Each delta is clamped to the range [-0.5, +0.5] and rounded to 1 decimal place.
        """
        prompt = (
            f"Context: {context}\n"
            f"Player choice: \"{choice_text}\"\n\n"
            "Return strictly valid JSON with float values (one decimal place) for keys:\n"
            "  \"trust\", \"fear\", \"affection\"\n"
            "Each float must be between -0.5 and +0.5 (inclusive).\n"
            "Example:\n"
            "{\n"
            "  \"trust\": 0.3,\n"
            "  \"fear\": -0.4,\n"
            "  \"affection\": 0.1\n"
            "}\n"
            "Output ONLY the JSON object."
        )

        changes = {}
        for attempt in range(retries):
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You infer small emotional deltas and output only valid JSON."},
                        {"role": "user",   "content": prompt}
                    ],
                    max_tokens=100,
                    temperature=0.5,
                    request_timeout=30
                )
                raw = resp.choices[0].message.content.strip()
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    # Fallback: isolate first {...}
                    start = raw.find('{')
                    end   = raw.rfind('}')
                    parsed = json.loads(raw[start:end+1])
                if isinstance(parsed, dict):
                    changes = parsed
                    break
            except Exception as e:
                logging.warning(f"[CompanionAgent] attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)

        # Clamp and sanitize to [-0.5, +0.5], one decimal place
        safe = {}
        for k in ("trust", "fear", "affection"):
            raw_val = changes.get(k, 0.0)
            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                val = 0.0
            # clamp
            val = max(min(val, 0.5), -0.5)
            # round to 1 decimal
            safe[k] = round(val, 1)

        return safe

    def update_companion_profile(self, choice_index, choices, context):
        """
        After the player picks a choice, infer how the companion's traits should shift,
        apply them (clamped to [0,10]) and return the float deltas.
        """
        if choice_index < 0 or choice_index >= len(choices):
            return {}

        choice_text = choices[choice_index]
        deltas = self.infer_traits_from_choice(choice_text, context)

        for trait, delta in deltas.items():
            # apply delta
            old = self.state.companion_profile.get(trait, 0.0)
            new = old + delta
            # clamp into [0, 10] and round to 1 decimal
            new = round(max(min(new, 10.0), 0.0), 1)
            self.state.companion_profile[trait] = new

        return deltas
