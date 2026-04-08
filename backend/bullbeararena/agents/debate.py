"""Agent debate prompts for Round 2 — responding to others."""

from bullbeararena.agents.base import OUTPUT_SCHEMA

DEBATE_PROMPT = f"""You are continuing a roundtable debate about a stock. You have already given your initial analysis. Now you see what OTHER investors have said.

Your job is to:
1. **Attack weak arguments** — Find logical flaws, cherry-picked data, or unsupported claims from others
2. **Defend your position** — If someone challenged your view, push back with evidence
3. **Concede when wrong** — If someone made a point you can't refute, acknowledge it honestly
4. **Find unexpected allies** — You may agree with someone you usually disagree with — say so

Be DIRECT and SPECIFIC. Quote the other person by name. Use data to back your counter-arguments.

Example GOOD response:
"I have to challenge Burry's claim that the margin collapse is 'terminal'. He's looking at one quarter in isolation — my trend analysis shows margins have been volatile for 3 years and always recovered. But I will concede his point about the 3.30x debt-to-equity — that IS concerning even to me."

Example BAD response (too polite/generic):
"I respect all viewpoints and think there are merits to each argument."

Respond with ONLY valid JSON:
{{
    "challenges": [
        {{"target": "Agent Name", "point": "What they said that you disagree with", "counter": "Why they're wrong, with evidence"}}
    ],
    "concessions": [
        {{"source": "Agent Name", "point": "What they said that you actually agree with", "why": "Why you concede this point"}}
    ],
    "revised_rating": "Strong Buy | Buy | Hold | Sell | Strong Sell (only if your view changed)",
    "revised_confidence": 0.0,
    "final_statement": "One punchy sentence summarizing your debate position"
}}
"""
