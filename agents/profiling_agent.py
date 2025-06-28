import openai
import json
import logging
import time

class PlayerProfilingAgent:
    CANONICAL = {
        'courage': 'bravery',
        'curiosity': 'curiosity',
        'empathy': 'empathy',
        'communication': 'communication',
        'trust': 'trust',
    }

    def __init__(self, state):
        self.state = state
        # ensure the state has storage for the last analysis
        if not hasattr(self.state, "last_personality_analysis"):
            self.state.last_personality_analysis = ""

    def infer_traits_from_choice(self, choice_text, context, retries=2):
        """
        Prompts GPT to return strictly valid JSON mapping trait names to float deltas
        in the range [-0.5, +0.5], one decimal place.
        Keys: bravery, curiosity, empathy, communication, trust.
        Output only the JSON object.
        """
        prompt = (
            f"Context (scene snippet): {context}\n"
            f"Player choice: \"{choice_text}\"\n\n"
            "Return strictly valid JSON mapping each of these traits to a float between -0.5 and +0.5\n"
            "with exactly one decimal place:\n"
            "  bravery, curiosity, empathy, communication, trust\n"
            "Do NOT output any extra text—only the JSON object.\n"
            "Example:\n"
            "{\n"
            '  "bravery": 0.3,\n'
            '  "curiosity": -0.2,\n'
            '  "empathy": 0.0,\n'
            '  "communication": 0.1,\n'
            '  "trust": -0.4\n'
            "}"
        )

        traits = {}
        for attempt in range(retries):
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": "You infer small player trait changes and output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=120,
                    temperature=0.5,
                    request_timeout=30
                )
                raw = resp.choices[0].message.content.strip()
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    start = raw.find('{')
                    end   = raw.rfind('}')
                    parsed = json.loads(raw[start:end+1])
                if isinstance(parsed, dict):
                    traits = parsed
                    break
            except Exception as e:
                logging.warning(f"[PlayerProfilingAgent] inference attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)

        # sanitize, clamp and round
        clean = {}
        for k, raw_v in traits.items():
            key = k.strip().lower()
            key = self.CANONICAL.get(key, key)
            try:
                val = float(raw_v)
            except (ValueError, TypeError):
                val = 0.0
            # clamp [-0.5, 0.5]
            val = max(min(val, 0.5), -0.5)
            # one decimal place
            clean[key] = round(val, 1)

        return clean

    def infer_personality_analysis(
        self,
        prev_profile,
        prev_analysis,
        choice_text,
        context,
        updated_profile,
        retries=2
    ):
        """
        Given previous profile, previous analysis, the snippet, and the player's choice,
        plus the updated profile, prompt GPT to produce a concise personality analysis
        (under 100 words), building on the prior analysis.
        """
        prompt = (
            f"Previous profile: {prev_profile}\n"
            f"Previous analysis: {prev_analysis}\n"
            f"Scene snippet: {context}\n"
            f"Player choice: \"{choice_text}\"\n"
            f"Updated profile: {updated_profile}\n\n"
            "Based on these, provide a concise (under 100 words) personality analysis "
            "of the player character—highlight how their ongoing choices and trait shifts "
            "refine or evolve the analysis. Output only the analysis."
        )

        analysis = ""
        for attempt in range(retries):
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": "You are an expert in character psychology; build on prior analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7,
                    request_timeout=30
                )
                analysis = resp.choices[0].message.content.strip()
                break
            except Exception as e:
                logging.warning(f"[PlayerProfilingAgent] analysis attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)

        return analysis

    def update_profile(self, choice_index, choices, context):
        """
        After the player makes a choice:
          1) Infer small float trait deltas.
          2) Apply them to state.player_profile (clamped 0.0–10.0).
          3) Generate a short personality analysis.
        Saves the analysis to state.last_personality_analysis and returns:
          - 'deltas': {trait: delta, ...}
          - 'analysis': "<new analysis>"
        """
        if choice_index < 0 or choice_index >= len(choices):
            return {"deltas": {}, "analysis": ""}

        choice = choices[choice_index]
        prev_profile  = dict(self.state.player_profile)
        prev_analysis = self.state.last_personality_analysis or ""

        # 1) infer float deltas
        deltas = self.infer_traits_from_choice(choice, context)

        # 2) apply and clamp to [0.0, 10.0]
        for trait, delta in deltas.items():
            old = float(self.state.player_profile.get(trait, 0.0))
            new = old + delta
            # clamp & round
            new = round(max(min(new, 10.0), 0.0), 1)
            self.state.player_profile[trait] = new

        updated_profile = dict(self.state.player_profile)

        # 3) personality analysis
        analysis = self.infer_personality_analysis(
            prev_profile, prev_analysis, choice, context, updated_profile
        )

        # persist
        self.state.last_personality_analysis = analysis
        try:
            self.state.save_game()
        except Exception:
            pass

        return {"deltas": deltas, "analysis": analysis}
