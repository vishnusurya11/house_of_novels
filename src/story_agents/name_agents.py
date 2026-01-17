"""
Multi-agent debate system for character name generation.

3 agents propose, critique, and vote on character names with random
alphabet constraints for first/last name initials.
"""

import random
import string
import json
from typing import Optional, Dict
from collections import Counter

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import NameProposal, NameCritiques, NameVote
from src.config import DEFAULT_MODEL, NAME_DEBATE_ROUNDS


# =============================================================================
# Name Generation Agents
# =============================================================================

class NameCreativeAgent(BaseStoryAgent):
    """Proposes creative, memorable names with phonetic appeal."""

    @property
    def name(self) -> str:
        return "NAME_CREATIVE"

    @property
    def role(self) -> str:
        return "Creative name designer"

    @property
    def system_prompt(self) -> str:
        return """You are a creative naming expert specializing in MEMORABLE, EVOCATIVE character names.

Your naming philosophy:
- Names should have PHONETIC APPEAL and rhythm
- Names can carry HIDDEN MEANINGS or symbolism that reflect character traits
- Names should be DISTINCTIVE and stick in readers' minds
- Consider how the name SOUNDS when spoken aloud

You balance creativity with readability - names should be imaginative but not unpronounceable."""


class NameAuthenticAgent(BaseStoryAgent):
    """Proposes authentic, setting-appropriate names."""

    @property
    def name(self) -> str:
        return "NAME_AUTHENTIC"

    @property
    def role(self) -> str:
        return "Authenticity advocate"

    @property
    def system_prompt(self) -> str:
        return """You are an authenticity expert specializing in GROUNDED, BELIEVABLE character names.

Your naming philosophy:
- Names should feel GENUINE to the story's world and time period
- Names should follow realistic NAMING CONVENTIONS for the setting
- Names should be PRONOUNCEABLE for readers
- Consider cultural/historical accuracy when appropriate

You prioritize names that feel real and organic to the world being built."""


class NameDistinctiveAgent(BaseStoryAgent):
    """Proposes unique names that stand apart from other characters."""

    @property
    def name(self) -> str:
        return "NAME_DISTINCTIVE"

    @property
    def role(self) -> str:
        return "Distinctiveness champion"

    @property
    def system_prompt(self) -> str:
        return """You are a distinctiveness expert ensuring character names are UNIQUE and DISTINGUISHABLE.

Your naming philosophy:
- Names must be CLEARLY DIFFERENT from other characters in the story
- Avoid similar-sounding names that could confuse readers
- Each name should have a UNIQUE FIRST LETTER when possible among the cast
- Names should be instantly IDENTIFIABLE to their character

You ensure readers never confuse one character for another based on name similarity."""


# =============================================================================
# Name Debate Orchestration
# =============================================================================

def _extract_old_name_from_role(role: str) -> Optional[str]:
    """
    Extract old name from role description.

    E.g., "A charismatic prophet named Zarek" -> "Zarek"
         "Elder Miriam" -> "Miriam"
         "The village baker" -> None (no extractable name)
    """
    role_lower = role.lower()

    # Pattern 1: "named X" or "called X"
    for keyword in ["named ", "called "]:
        if keyword in role_lower:
            # Get text after keyword
            idx = role_lower.find(keyword)
            after_keyword = role[idx + len(keyword):]
            # Take first name-like chunk, strip punctuation and qualifiers
            old_name = after_keyword.split(",")[0].split(" who")[0].split(" the")[0].split(" -")[0].strip()
            # Remove trailing punctuation
            old_name = old_name.rstrip(".,;:!?")
            if old_name and len(old_name) > 1:
                return old_name

    # Pattern 2: Simple name (1-2 words, likely a name if capitalized)
    words = role.split()
    if len(words) <= 2:
        # Filter out common non-name words
        non_names = {"the", "a", "an", "old", "young", "wise", "evil", "good"}
        name_words = [w for w in words if w.lower() not in non_names]
        if name_words:
            return " ".join(name_words)

    # Pattern 3: "Elder X", "Lord X", "Queen X" etc.
    title_prefixes = ["elder ", "lord ", "lady ", "queen ", "king ", "prince ", "princess ",
                      "master ", "grandmother ", "grandfather ", "uncle ", "aunt "]
    for prefix in title_prefixes:
        if role_lower.startswith(prefix):
            name_part = role[len(prefix):].split(",")[0].split(" who")[0].strip()
            if name_part:
                return role  # Return full "Elder X" as the name

    return None


def _extract_character_roles_from_outline(outline: dict) -> list[dict]:
    """
    Extract unique character roles/descriptions from story outline with type info.

    Returns list of dicts with:
        - role: The role description string
        - character_type: "protagonist", "antagonist", or "supporting"
    """
    characters = []
    seen_roles = set()

    # Get protagonist (type = "protagonist")
    if outline.get("protagonist"):
        role = outline["protagonist"]
        characters.append({
            "role": role,
            "character_type": "protagonist",
        })
        seen_roles.add(role)

    # Get antagonist (type = "antagonist")
    if outline.get("antagonist"):
        role = outline["antagonist"]
        if role not in seen_roles:
            characters.append({
                "role": role,
                "character_type": "antagonist",
            })
            seen_roles.add(role)

    # Extract characters from all scenes (type = "supporting")
    for act in outline.get("acts", []):
        for scene in act.get("scenes", []):
            for char in scene.get("characters", []):
                if char not in seen_roles:
                    characters.append({
                        "role": char,
                        "character_type": "supporting",
                    })
                    seen_roles.add(char)

    return characters


def _run_single_name_debate(
    character_role: str,
    first_initial: str,
    last_initial: str,
    logline: str,
    setting_prompt: str,
    existing_names: list[str],
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Run a 3-agent debate to generate a single character name.

    Returns dict with:
        - role: character role
        - first_initial, last_initial: alphabet constraints
        - proposals: list of name proposals with reasoning
        - critiques: all agent critiques
        - votes: agent votes
        - final_name: selected name
        - selection_reason: why this name was chosen
    """
    # Initialize agents
    creative = NameCreativeAgent(model=model)
    authentic = NameAuthenticAgent(model=model)
    distinctive = NameDistinctiveAgent(model=model)
    agents = [creative, authentic, distinctive]

    existing_names_str = ", ".join(existing_names) if existing_names else "None yet"

    # Build context prompt
    context = f"""CHARACTER ROLE: {character_role}

STORY LOGLINE: {logline}

WORLD SETTING: {setting_prompt}

EXISTING CHARACTER NAMES (must be distinct from these): {existing_names_str}

CONSTRAINTS:
- First name MUST start with: {first_initial}
- Last name MUST start with: {last_initial}"""

    # ==========================================================================
    # Round 1: Each agent proposes a name
    # ==========================================================================
    proposals = []
    proposal_prompt = f"""{context}

Propose a character name that:
1. Starts with {first_initial} for first name
2. Starts with {last_initial} for last name
3. Fits the character's role and story setting
4. Is distinct from existing names"""

    print(f"    Generating proposals for {character_role}...")
    for agent in agents:
        try:
            proposal: NameProposal = agent.invoke_structured(
                proposal_prompt, NameProposal, max_tokens=500
            )
            proposals.append({
                "agent": agent.name,
                "first_name": proposal.first_name,
                "last_name": proposal.last_name,
                "full_name": f"{proposal.first_name} {proposal.last_name}",
                "reasoning": proposal.reasoning,
            })
        except Exception as e:
            # Fallback: generate a simple name
            proposals.append({
                "agent": agent.name,
                "first_name": f"{first_initial}ara",
                "last_name": f"{last_initial}ith",
                "full_name": f"{first_initial}ara {last_initial}ith",
                "reasoning": f"Fallback name due to error: {str(e)[:50]}",
            })

    # ==========================================================================
    # Round 2: Each agent critiques all proposals
    # ==========================================================================
    critiques = []
    proposals_text = "\n".join([
        f"Proposal {i}: {p['full_name']} - {p['reasoning'][:100]}..."
        for i, p in enumerate(proposals)
    ])

    critique_prompt = f"""{context}

PROPOSALS TO CRITIQUE:
{proposals_text}

Critique ALL 3 proposals. For each, evaluate:
- How well it fits the character role and setting
- Phonetic appeal and memorability
- Distinctiveness from existing names
- Overall effectiveness

Score each from 1-10."""

    print(f"    Gathering critiques...")
    for agent in agents:
        try:
            agent_critiques: NameCritiques = agent.invoke_structured(
                critique_prompt, NameCritiques, max_tokens=1000
            )
            critiques.append({
                "agent": agent.name,
                "reviews": [
                    {
                        "proposal": r.proposal_index,
                        "strengths": r.strengths,
                        "weaknesses": r.weaknesses,
                        "score": r.score,
                    }
                    for r in agent_critiques.reviews
                ]
            })
        except Exception as e:
            # Fallback: neutral scores
            critiques.append({
                "agent": agent.name,
                "reviews": [
                    {"proposal": i, "strengths": "N/A", "weaknesses": "N/A", "score": 5}
                    for i in range(3)
                ],
                "error": str(e)[:50],
            })

    # ==========================================================================
    # Round 3: Each agent votes (can't vote for own proposal)
    # ==========================================================================
    votes = {}
    vote_prompt = f"""{context}

PROPOSALS:
{proposals_text}

CRITIQUES SUMMARY:
{json.dumps(critiques, indent=2)[:2000]}

Vote for the BEST name. You CANNOT vote for your own proposal (proposal index matches your position).
Agent positions: NAME_CREATIVE=0, NAME_AUTHENTIC=1, NAME_DISTINCTIVE=2"""

    print(f"    Collecting votes...")
    for i, agent in enumerate(agents):
        try:
            vote: NameVote = agent.invoke_structured(vote_prompt, NameVote, max_tokens=300)
            # Ensure agent doesn't vote for own proposal
            voted_for = vote.voted_for
            if voted_for == i:
                # Force different vote
                voted_for = (i + 1) % 3
            votes[agent.name] = {
                "voted_for": voted_for,
                "reasoning": vote.vote_reasoning,
            }
        except Exception as e:
            # Fallback: vote for next proposal
            votes[agent.name] = {
                "voted_for": (i + 1) % 3,
                "reasoning": f"Fallback vote due to error: {str(e)[:30]}",
            }

    # ==========================================================================
    # Tally votes and determine winner
    # ==========================================================================
    vote_counts = Counter(v["voted_for"] for v in votes.values())
    vote_tally = {proposals[i]["full_name"]: count for i, count in vote_counts.items()}

    # Find winner(s)
    max_votes = max(vote_counts.values())
    winners = [i for i, count in vote_counts.items() if count == max_votes]

    if len(winners) == 1:
        winner_idx = winners[0]
        selection_reason = f"Majority vote ({max_votes} votes)"
    else:
        # Tie breaker: highest average critique score
        avg_scores = []
        for i in winners:
            scores = [
                r["score"]
                for c in critiques
                for r in c["reviews"]
                if r["proposal"] == i
            ]
            avg = sum(scores) / len(scores) if scores else 0
            avg_scores.append((i, avg))
        winner_idx = max(avg_scores, key=lambda x: x[1])[0]
        selection_reason = f"Tie broken by highest average critique score ({avg_scores})"

    final_name = proposals[winner_idx]["full_name"]

    return {
        "role": character_role,
        "first_initial": first_initial,
        "last_initial": last_initial,
        "proposals": proposals,
        "critiques": critiques,
        "votes": votes,
        "vote_tally": vote_tally,
        "final_name": final_name,
        "selection_reason": selection_reason,
    }


def generate_character_names_via_debate(
    outline_json: str,
    setting_prompt: str,
    model: str = DEFAULT_MODEL,
    max_characters: int = None,
) -> tuple[list[dict], list[dict], Dict[str, str]]:
    """
    Generate names for all characters via 3-agent debate.

    Args:
        outline_json: Story outline JSON string
        setting_prompt: World setting description
        model: LLM model to use
        max_characters: Maximum number of characters to name (None = all)

    Returns:
        Tuple of:
        - names: List of {role, character_type, old_name, final_name, first_initial, last_initial}
        - debates: Full debate metadata for each character
        - name_mapping: Direct mapping of old_name -> final_name for substitution
    """
    outline = json.loads(outline_json)
    logline = outline.get("logline", "A story unfolds.")

    # Extract character roles from outline (now returns list of dicts with type info)
    character_entries = _extract_character_roles_from_outline(outline)

    # Limit if specified
    if max_characters and len(character_entries) > max_characters:
        character_entries = character_entries[:max_characters]

    print(f"\n>>> Generating names for {len(character_entries)} characters via debate...")

    names = []
    debates = []
    existing_names = []
    name_mapping: Dict[str, str] = {}

    for i, entry in enumerate(character_entries):
        role = entry["role"]
        character_type = entry["character_type"]

        # Extract old name from role at debate time
        old_name = _extract_old_name_from_role(role)

        # Generate random initials
        first_initial = random.choice(string.ascii_uppercase)
        last_initial = random.choice(string.ascii_uppercase)

        print(f"\n>>> Character {i+1}/{len(character_entries)}: {role}")
        print(f"    Type: {character_type}")
        if old_name:
            print(f"    Old name: {old_name}")
        print(f"    Initials: {first_initial}.{last_initial}.")

        debate_result = _run_single_name_debate(
            character_role=role,
            first_initial=first_initial,
            last_initial=last_initial,
            logline=logline,
            setting_prompt=setting_prompt,
            existing_names=existing_names,
            model=model,
        )

        final_name = debate_result["final_name"]

        names.append({
            "role": role,
            "character_type": character_type,
            "old_name": old_name,
            "final_name": final_name,
            "first_initial": first_initial,
            "last_initial": last_initial,
        })
        debates.append(debate_result)
        existing_names.append(final_name)

        # Build the direct mapping for substitution
        if old_name and old_name != final_name:
            name_mapping[old_name] = final_name

        print(f"    Selected: {final_name}")
        print(f"    Reason: {debate_result['selection_reason']}")

    return names, debates, name_mapping
