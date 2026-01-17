"""
Supervisor agent that orchestrates debates and makes final card selections.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL, DEBATE_ROUNDS
from src.agents.card_agents import PlacerAgent, RotatorAgent, CriticAgent, SynthesizerAgent


class Supervisor:
    """
    Orchestrates the multi-agent debate process for card selection.

    The Supervisor:
    1. Manages the 4 debate agents
    2. Runs debate rounds (initial opinions + rebuttals)
    3. Collects votes and determines final selection
    4. Acts as tiebreaker when needed
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model

        # Initialize the 4 debate agents
        self.agents = [
            PlacerAgent(model),
            RotatorAgent(model),
            CriticAgent(model),
            SynthesizerAgent(model),
        ]

        # Supervisor's own LLM for tiebreaking
        self.llm = ChatOpenAI(
            model=model,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.5,
        )

    def run_debate(self, context: str, cards: list[str], card_type: str) -> tuple[str, dict]:
        """
        Run a full debate cycle for selecting one card.

        Args:
            context: Current story context (previously selected cards)
            cards: List of 4 card options
            card_type: Type of card being debated

        Returns:
            Tuple of (selected_card, structured_metadata)
        """
        # Structured data to return
        selection_data = {
            "card_type": card_type,
            "candidates": cards.copy(),
            "debates": [],
            "voting": None,
        }

        all_messages = []

        # Run debate rounds
        for round_num in range(DEBATE_ROUNDS):
            round_data = {
                "round": round_num + 1,
                "opinions": [],
            }

            for agent in self.agents:
                response = agent.respond(
                    context=context,
                    cards=cards,
                    card_type=card_type,
                    previous_messages=all_messages if round_num > 0 else None,
                )
                # Extract just the opinion text (remove the **AGENT**: prefix)
                opinion_text = response.split("**: ", 1)[-1] if "**: " in response else response

                round_data["opinions"].append({
                    "agent": agent.name,
                    "opinion": opinion_text,
                })
                all_messages.append(response)

            selection_data["debates"].append(round_data)

        # Voting phase
        debate_transcript = "\n".join(all_messages)
        votes_data = []

        for agent in self.agents:
            vote_idx = agent.vote(
                context=context,
                cards=cards,
                card_type=card_type,
                debate_transcript=debate_transcript,
            )
            votes_data.append({
                "agent": agent.name,
                "voted_for": vote_idx,
                "voted_card": cards[vote_idx],
            })

        # Count votes
        vote_counts = {}
        for v in votes_data:
            idx = v["voted_for"]
            vote_counts[idx] = vote_counts.get(idx, 0) + 1

        # Find winner(s)
        max_votes = max(vote_counts.values())
        winners = [idx for idx, count in vote_counts.items() if count == max_votes]

        is_tie = len(winners) > 1
        if is_tie:
            selected_idx = self._break_tie(context, cards, card_type, winners, debate_transcript)
        else:
            selected_idx = winners[0]

        # Build voting result
        selection_data["voting"] = {
            "votes": votes_data,
            "vote_counts": {str(k): v for k, v in vote_counts.items()},
            "winner_index": selected_idx,
            "winner_card": cards[selected_idx],
            "winner_votes": vote_counts.get(selected_idx, 0),
            "tie": is_tie,
            "tied_candidates": [cards[i] for i in winners] if is_tie else None,
        }

        # Console output for user feedback
        print(f"  [{card_type.upper()}] Options: {', '.join(cards)}")
        for v in votes_data:
            print(f"    {v['agent']} -> {v['voted_card']}")
        print(f"    >>> Winner: {cards[selected_idx]} ({vote_counts.get(selected_idx, 0)} votes)")

        return cards[selected_idx], selection_data

    def _break_tie(self, context: str, cards: list[str], card_type: str,
                   tied_indices: list[int], debate_transcript: str) -> int:
        """
        Break a tie by having the supervisor make the final call.
        """
        tied_cards = [f"{i+1}. {cards[i]}" for i in tied_indices]
        tied_options = "\n".join(tied_cards)

        prompt = f"""As the debate supervisor, you must break a tie for the {card_type.upper()} card.

Current story context:
{context if context else "(Starting fresh)"}

Tied options:
{tied_options}

Debate summary:
{debate_transcript[-2000:]}

Consider the arguments made and select the option that best serves the story.
Reply with ONLY the number of your chosen option."""

        messages = [
            SystemMessage(content="You are the supervisor of a story prompt debate. Break ties wisely."),
            HumanMessage(content=prompt),
        ]

        response = self.llm.invoke(messages)

        # Parse response for the first valid tied option
        for char in response.content:
            if char.isdigit():
                idx = int(char) - 1
                if idx in tied_indices:
                    return idx

        # Default to first tied option
        return tied_indices[0]
