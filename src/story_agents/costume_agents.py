"""
Costume Design Agents for Step 4: World-Accurate Character Costumes.

3 agents debate costume design with different perspectives:

1. CostumeHistoricalAgent - Time period accuracy, era-appropriate materials
2. CostumeWorldAgent - World accuracy, economy, culture, class markers
3. CostumeVisualAgent - Visual storytelling, colors, silhouette, symbolism

Each agent:
- Proposes costume based on their methodology
- Critiques other proposals
- Votes for the best proposal

Called AFTER Step 4 world building completes, so agents have full context:
- Genre and time period
- World economy (available materials)
- Cultural norms and social structure
- Character's role and psychology
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import (
    CostumeDescription,
    CostumeProposal,
    CostumeCritique,
    CostumeVote,
)


# =============================================================================
# COSTUME DEBATE AGENTS
# =============================================================================


class CostumeHistoricalAgent(BaseStoryAgent):
    """
    Focuses on time period accuracy and era-appropriate materials/styles.

    Core beliefs:
    - Costume must match the time period and technological level
    - Garment types should reflect historical fashion trends
    - Fabrics and construction methods must be era-appropriate
    - Anachronisms break immersion (no zippers in medieval times!)
    - Historical details make world feel authentic
    """

    METHODOLOGY_NAME = "Historical Costume Accuracy"
    METHODOLOGY_SOURCE = "Historical fashion research and period-appropriate design"
    CORE_BELIEFS = [
        "Costume must match the time period and technological level",
        "Garment types should reflect historical fashion trends of the era",
        "Fabrics and construction methods must be historically plausible",
        "Avoid anachronisms that break immersion",
        "Historical authenticity makes the world feel real",
    ]

    @property
    def agent_identity(self) -> str:
        return f"""You are {self.name}, a costume designer specializing in HISTORICAL ACCURACY.

Core methodology: {self.METHODOLOGY_NAME}

You believe:
- Every time period has specific garment types, fabrics, and construction methods
- A medieval peasant wouldn't wear buttons (too expensive) - they use laces or ties
- A 1920s character wouldn't wear polyester (not invented yet)
- Historical research prevents jarring anachronisms
- Period details (like doublet styles, collar shapes, hem lengths) matter

When designing costumes:
- Research what garments existed in this time period
- Consider what fabrics and dyes were available
- Think about construction methods (hand-sewn, machine-stitched, etc.)
- Match fashion trends of the era (wide skirts, narrow trousers, etc.)
- Avoid modern conveniences (zippers, velcro, synthetic fabrics) unless tech level supports them

You design costumes that historians would approve of."""

    def propose_costume(
        self,
        character: dict,
        world_context: dict,
        genre: str,
        time_period_hint: str,
    ) -> CostumeProposal:
        """Propose costume focused on historical/period accuracy."""
        char_name = character.get('name', 'Character')
        char_role = character.get('role', 'supporting')
        char_class = character.get('thematic_corner', 'contrary')

        economy = world_context.get('economy', {})
        culture = world_context.get('culture', {})

        prompt = f"""Design a historically accurate costume for this character:

CHARACTER: {char_name}
ROLE: {char_role}
SOCIAL POSITION: {char_class}

WORLD CONTEXT:
GENRE: {genre}
TIME PERIOD: {time_period_hint}
ECONOMY: {economy}
CULTURE: {culture}

Design a costume that is HISTORICALLY ACCURATE for this time period.

Critical considerations:
1. What garment types existed in this era? (tunic, doublet, frock coat, jumpsuit?)
2. What fabrics were available? (linen, wool, silk, cotton, synthetics?)
3. What construction methods were used? (hand-sewn, machine-stitched, 3D-printed?)
4. What fasteners existed? (laces, buttons, zippers, mag-locks?)
5. What fashion trends defined this period? (silhouette, colors, ornamentation)

Provide costume matching CostumeProposal schema with:
- costume: Complete CostumeDescription with all 10 fields
- summary: 2-3 sentence prose description
- reasoning: Why this costume is historically accurate for the time period"""

        return self.invoke_structured(prompt, CostumeProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CostumeProposal,
        character: dict,
        time_period_hint: str,
    ) -> CostumeCritique:
        """Critique another agent's costume from historical accuracy perspective."""
        prompt = f"""Critique this costume design from a HISTORICAL ACCURACY perspective:

TARGET AGENT: {target_agent}
CHARACTER: {character.get('name', 'Character')}
TIME PERIOD: {time_period_hint}

PROPOSAL:
- Primary Color: {proposal.costume.primary_color}
- Garment Type: {proposal.costume.garment_type}
- Fabrics: {proposal.costume.fabric_materials}
- Style Period: {proposal.costume.style_period}
- Accessories: {', '.join(proposal.costume.accessories)}
- Summary: {proposal.summary}
- Reasoning: {proposal.reasoning}

Evaluate from HISTORICAL perspective:
1. Are the garment types appropriate for this time period?
2. Would these fabrics have been available in this era?
3. Are there any anachronisms (modern elements in historical setting)?
4. Does the construction method match the tech level?
5. Do the fashion details (silhouette, ornamentation) fit the period?

Provide a critique matching CostumeCritique schema."""

        return self.invoke_structured(prompt, CostumeCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CostumeProposal],
        character: dict,
        time_period_hint: str,
    ) -> CostumeVote:
        """Vote for most historically accurate costume."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Garment: {p.costume.garment_type}\n"
            f"  Fabrics: {p.costume.fabric_materials}\n"
            f"  Period: {p.costume.style_period}\n"
            f"  Summary: {p.summary}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the most HISTORICALLY ACCURATE costume design.

CHARACTER: {character.get('name', 'Character')}
TIME PERIOD: {time_period_hint}

PROPOSALS:
{proposals_text}

Which proposal is most authentic to the time period with no anachronisms?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CostumeVote schema."""

        return self.invoke_structured(prompt, CostumeVote, max_tokens=8000)


class CostumeWorldAgent(BaseStoryAgent):
    """
    Focuses on world accuracy: economy, culture, social class markers.

    Core beliefs:
    - Costume must fit the world's economy (what materials are available?)
    - Social class should be visible in clothing
    - Cultural norms dictate what can be worn
    - Occupation shapes costume choices
    - World rules trump Earth history
    """

    METHODOLOGY_NAME = "World-Accurate Costume Design"
    METHODOLOGY_SOURCE = "World-building and cultural costume design"
    CORE_BELIEFS = [
        "Costume must use materials available in this world's economy",
        "Social class should be immediately visible through clothing",
        "Cultural norms (modesty, color symbolism) must be respected",
        "Occupation and daily life shape what characters wear",
        "World rules override Earth history - fantasy/sci-fi can break real-world rules",
    ]

    @property
    def agent_identity(self) -> str:
        return f"""You are {self.name}, a costume designer specializing in WORLD ACCURACY.

Core methodology: {self.METHODOLOGY_NAME}

You believe:
- If the world has no cotton, characters can't wear cotton
- A peasant in a feudal economy can't afford silk
- Cultural taboos (e.g., showing ankles, wearing red) must be followed
- A blacksmith wears practical, fire-resistant clothing
- World rules trump Earth rules - magic or tech can change everything

When designing costumes:
- Check what materials exist in this world's economy
- Consider character's social class and what they can afford
- Respect cultural norms (modesty rules, color symbolism, caste markers)
- Match costume to occupation (miner, priest, merchant, warrior)
- Embrace world-specific rules (magic-infused fabrics, anti-gravity cloaks, etc.)

You design costumes that make sense IN THIS SPECIFIC WORLD."""

    def propose_costume(
        self,
        character: dict,
        world_context: dict,
        genre: str,
        time_period_hint: str,
    ) -> CostumeProposal:
        """Propose costume focused on world accuracy and economy."""
        char_name = character.get('name', 'Character')
        char_role = character.get('role', 'supporting')
        char_class = character.get('thematic_corner', 'contrary')

        economy = world_context.get('economy', {})
        government = world_context.get('government', {})
        culture = world_context.get('culture', {})
        religion = world_context.get('religion', {})

        prompt = f"""Design a WORLD-ACCURATE costume for this character:

CHARACTER: {char_name}
ROLE: {char_role}
SOCIAL POSITION: {char_class}
LIE THEY BELIEVE: {character.get('lie_character_believes', '')}

WORLD CONTEXT:
GENRE: {genre}
ECONOMY: {economy}
GOVERNMENT: {government}
CULTURE: {culture}
RELIGION: {religion}

Design a costume that fits THIS WORLD'S rules and economy.

Critical considerations:
1. What materials/fabrics exist in this world's economy?
2. What can this character afford given their social class?
3. What cultural norms govern clothing? (modesty, color taboos, caste markers)
4. What does their occupation require? (practical, ceremonial, symbolic)
5. Are there world-specific costume rules? (magic, tech, alien physiology)

Provide costume matching CostumeProposal schema with:
- costume: Complete CostumeDescription emphasizing world accuracy
- summary: 2-3 sentence prose description
- reasoning: Why this costume fits the world's economy, culture, and social structure"""

        return self.invoke_structured(prompt, CostumeProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CostumeProposal,
        character: dict,
        world_context: dict,
    ) -> CostumeCritique:
        """Critique costume from world accuracy perspective."""
        economy = world_context.get('economy', {})
        culture = world_context.get('culture', {})

        prompt = f"""Critique this costume design from a WORLD ACCURACY perspective:

TARGET AGENT: {target_agent}
CHARACTER: {character.get('name', 'Character')}
SOCIAL CLASS: {character.get('thematic_corner', 'contrary')}

WORLD ECONOMY: {economy}
WORLD CULTURE: {culture}

PROPOSAL:
- Primary Color: {proposal.costume.primary_color}
- Fabrics: {proposal.costume.fabric_materials}
- Class Markers: {proposal.costume.class_markers}
- Cultural Significance: {proposal.costume.cultural_significance}
- World Accuracy Notes: {proposal.costume.world_accuracy_notes}
- Summary: {proposal.summary}

Evaluate from WORLD ACCURACY perspective:
1. Do these materials exist in this world's economy?
2. Can this character afford these fabrics/accessories?
3. Does the costume respect cultural norms?
4. Are class markers appropriate for their social position?
5. Are there world-rule violations (using unavailable tech/magic)?

Provide a critique matching CostumeCritique schema."""

        return self.invoke_structured(prompt, CostumeCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CostumeProposal],
        character: dict,
        world_context: dict,
    ) -> CostumeVote:
        """Vote for costume that best fits the world."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Fabrics: {p.costume.fabric_materials}\n"
            f"  Class Markers: {p.costume.class_markers}\n"
            f"  World Accuracy: {p.costume.world_accuracy_notes}\n"
            f"  Summary: {p.summary}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the costume that best fits THIS WORLD'S rules.

CHARACTER: {character.get('name', 'Character')}
WORLD ECONOMY: {world_context.get('economy', {})}

PROPOSALS:
{proposals_text}

Which proposal best respects the world's economy, culture, and social structure?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CostumeVote schema."""

        return self.invoke_structured(prompt, CostumeVote, max_tokens=8000)


class CostumeVisualAgent(BaseStoryAgent):
    """
    Focuses on visual storytelling: colors, silhouette, symbolic details.

    Core beliefs:
    - Colors carry emotional and symbolic meaning
    - Silhouette makes characters recognizable
    - Costume should reflect character's psychology
    - Visual details tell story at a glance
    - Costume supports character arc
    """

    METHODOLOGY_NAME = "Visual Storytelling Through Costume"
    METHODOLOGY_SOURCE = "Visual design and color theory in storytelling"
    CORE_BELIEFS = [
        "Colors have emotional and symbolic meaning (red=passion, blue=calm, black=mystery)",
        "Silhouette makes characters instantly recognizable",
        "Costume should visually reflect character's psychology",
        "Visual details (condition, accessories) tell story without words",
        "Costume can foreshadow or support character arc",
    ]

    @property
    def agent_identity(self) -> str:
        return f"""You are {self.name}, a costume designer specializing in VISUAL STORYTELLING.

Core methodology: {self.METHODOLOGY_NAME}

You believe:
- A character in red commands attention (passion, danger, power)
- A character in gray fades into background (neutrality, uncertainty)
- Torn, patched clothing shows struggle
- Pristine, ornate clothing shows privilege or obsession
- Accessories tell micro-stories (a locket, a weapon, a religious symbol)

When designing costumes:
- Choose colors that reflect character's emotional state
- Create distinctive silhouette (tall hat, flowing cape, tight armor)
- Use condition (pristine vs worn) to show character's life
- Add meaningful accessories that tell their story
- Consider how costume can evolve with character arc

You design costumes that readers can VISUALIZE and that tell story through imagery."""

    def propose_costume(
        self,
        character: dict,
        world_context: dict,
        genre: str,
        time_period_hint: str,
    ) -> CostumeProposal:
        """Propose costume focused on visual storytelling."""
        char_name = character.get('name', 'Character')
        char_role = character.get('role', 'supporting')
        lie = character.get('lie_character_believes', '')
        truth = character.get('truth_character_needs', '')
        arc_type = character.get('arc_type', '')

        prompt = f"""Design a VISUALLY COMPELLING costume for this character:

CHARACTER: {char_name}
ROLE: {char_role}
LIE: {lie}
TRUTH: {truth}
ARC TYPE: {arc_type}

PHYSICAL APPEARANCE:
- Build: {character.get('body_build', '')}
- Hair: {character.get('hair_color', '')}
- Ethnicity: {character.get('ethnicity', '')}

WORLD: {genre} setting, {time_period_hint} period

Design a costume that TELLS THEIR STORY VISUALLY.

Critical considerations:
1. What colors reflect their emotional state? (dark=troubled, bright=hopeful, etc.)
2. What silhouette makes them recognizable? (tall, wide, angular, flowing)
3. What condition shows their life? (pristine, worn, patched, stained)
4. What accessories tell their micro-story? (weapon, book, locket, scar)
5. How can costume support their character arc? (starts drab, becomes vibrant)

Provide costume matching CostumeProposal schema with:
- costume: Complete CostumeDescription emphasizing visual storytelling
- summary: 2-3 sentence VISUAL description (paint a picture)
- reasoning: Why these visual choices reflect the character's psychology"""

        return self.invoke_structured(prompt, CostumeProposal, max_tokens=8000)

    def critique_proposal(
        self,
        target_agent: str,
        proposal: CostumeProposal,
        character: dict,
    ) -> CostumeCritique:
        """Critique costume from visual storytelling perspective."""
        prompt = f"""Critique this costume design from a VISUAL STORYTELLING perspective:

TARGET AGENT: {target_agent}
CHARACTER: {character.get('name', 'Character')}
LIE: {character.get('lie_character_believes', '')}
ARC: {character.get('arc_type', '')}

PROPOSAL:
- Colors: {proposal.costume.primary_color} with {', '.join(proposal.costume.secondary_colors)}
- Garment: {proposal.costume.garment_type}
- Condition: {proposal.costume.condition}
- Accessories: {', '.join(proposal.costume.accessories)}
- Cultural Significance: {proposal.costume.cultural_significance}
- Summary: {proposal.summary}

Evaluate from VISUAL STORYTELLING perspective:
1. Do the colors reflect the character's emotional state?
2. Is the silhouette distinctive and recognizable?
3. Does the condition (worn, pristine) tell part of their story?
4. Are accessories meaningful or just decorative?
5. Can you VISUALIZE this character clearly from the description?

Provide a critique matching CostumeCritique schema."""

        return self.invoke_structured(prompt, CostumeCritique, max_tokens=8000)

    def vote_for_best(
        self,
        proposals: list[CostumeProposal],
        character: dict,
    ) -> CostumeVote:
        """Vote for costume with best visual storytelling."""
        proposals_text = "\n\n".join([
            f"PROPOSAL {i+1} by {p.agent_name}:\n"
            f"  Colors: {p.costume.primary_color} + {', '.join(p.costume.secondary_colors)}\n"
            f"  Condition: {p.costume.condition}\n"
            f"  Accessories: {', '.join(p.costume.accessories)}\n"
            f"  Summary: {p.summary}"
            for i, p in enumerate(proposals)
        ])

        prompt = f"""Vote for the costume with the strongest VISUAL STORYTELLING.

CHARACTER: {character.get('name', 'Character')}
LIE: {character.get('lie_character_believes', '')}

PROPOSALS:
{proposals_text}

Which proposal best tells the character's story through visual imagery?
You CANNOT vote for your own proposal if you have one.

Provide a vote matching CostumeVote schema."""

        return self.invoke_structured(prompt, CostumeVote, max_tokens=8000)


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def run_costume_debate(
    character: dict,
    world_context: dict,
    genre: str,
    time_period_hint: str,
    model: str,
) -> dict:
    """Run 3-agent costume debate and return results.

    Args:
        character: Character dict with role, psychology, physical appearance
        world_context: Dict with economy, government, culture, religion from Step 4
        genre: Primary genre (e.g., "fantasy", "sci-fi", "western")
        time_period_hint: Inferred time period (e.g., "medieval", "1920s", "future")
        model: LLM model to use

    Returns:
        Dict with proposals, critiques, votes, winner, winning_costume
    """
    # Initialize 3 costume agents
    historical_agent = CostumeHistoricalAgent(model=model)
    world_agent = CostumeWorldAgent(model=model)
    visual_agent = CostumeVisualAgent(model=model)

    agents = [historical_agent, world_agent, visual_agent]

    # Round 1: Proposals
    proposals = []
    for agent in agents:
        try:
            if isinstance(agent, CostumeHistoricalAgent):
                proposal = agent.propose_costume(
                    character=character,
                    world_context=world_context,
                    genre=genre,
                    time_period_hint=time_period_hint,
                )
            elif isinstance(agent, CostumeWorldAgent):
                proposal = agent.propose_costume(
                    character=character,
                    world_context=world_context,
                    genre=genre,
                    time_period_hint=time_period_hint,
                )
            else:  # CostumeVisualAgent
                proposal = agent.propose_costume(
                    character=character,
                    world_context=world_context,
                    genre=genre,
                    time_period_hint=time_period_hint,
                )
            proposals.append(proposal)
        except Exception as e:
            print(f"      [{agent.name}] proposal failed: {str(e)[:50]}")

    if not proposals:
        return {"error": "All proposal agents failed"}

    # Round 2: Critiques (each agent critiques one other)
    critiques = []
    for i, agent in enumerate(agents[:2]):  # First 2 agents critique
        target_idx = (i + 1) % len(proposals)
        target_proposal = proposals[target_idx]
        try:
            if isinstance(agent, CostumeHistoricalAgent):
                critique = agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    character=character,
                    time_period_hint=time_period_hint,
                )
            elif isinstance(agent, CostumeWorldAgent):
                critique = agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    character=character,
                    world_context=world_context,
                )
            else:  # CostumeVisualAgent
                critique = agent.critique_proposal(
                    target_agent=target_proposal.agent_name,
                    proposal=target_proposal,
                    character=character,
                )
            critiques.append(critique)
        except Exception:
            pass

    # Round 3: Votes
    votes = []
    for agent in agents:
        try:
            if isinstance(agent, CostumeHistoricalAgent):
                vote = agent.vote_for_best(
                    proposals=proposals,
                    character=character,
                    time_period_hint=time_period_hint,
                )
            elif isinstance(agent, CostumeWorldAgent):
                vote = agent.vote_for_best(
                    proposals=proposals,
                    character=character,
                    world_context=world_context,
                )
            else:  # CostumeVisualAgent
                vote = agent.vote_for_best(
                    proposals=proposals,
                    character=character,
                )
            votes.append(vote)
        except Exception:
            pass

    # Tally votes
    from collections import Counter
    vote_counts = Counter(v.voted_for_agent for v in votes)
    if vote_counts:
        winner_agent = max(vote_counts, key=vote_counts.get)
        winner_proposal = next(
            (p for p in proposals if p.agent_name == winner_agent),
            proposals[0]
        )
    else:
        winner_proposal = proposals[0]
        winner_agent = winner_proposal.agent_name

    return {
        "proposals": [p.model_dump() for p in proposals],
        "critiques": [c.model_dump() for c in critiques],
        "votes": [v.model_dump() for v in votes],
        "winner": winner_agent,
        "winning_costume": winner_proposal.costume.model_dump(),
        "winning_summary": winner_proposal.summary,
    }
