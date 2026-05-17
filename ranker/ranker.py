"""Core ranking logic using Swiss-bracket style tournaments."""

from dataclasses import dataclass, field
from typing import List, Tuple
import random


@dataclass
class Competitor:
    """Represents an item in the ranking."""
    name: str
    wins: int = 0
    losses: int = 0
    rounds_played: int = 0

    @property
    def score(self) -> float:
        """Calculate score based on wins and total rounds."""
        if self.rounds_played == 0:
            return 0.0
        return self.wins / self.rounds_played

    def __repr__(self) -> str:
        return f"{self.name} ({self.wins}W-{self.losses}L)"


class SwissRanker:
    """Implements Swiss-bracket style ranking system."""

    def __init__(self, items: List[str]):
        """Initialize ranker with list of items to rank.
        
        Args:
            items: List of item names/descriptions to rank
        """
        self.competitors = [Competitor(name=item) for item in items]
        self.matchups: List[Tuple[Competitor, Competitor]] = []
        self.history: List[Tuple[str, str, str]] = []  # (winner, loser, round)

    def get_pairings(self) -> List[Tuple[Competitor, Competitor]]:
        """Generate pairings for next round using Swiss-system algorithm.
        
        Swiss system: pair players with similar records.
        On first round, random pairings. Later rounds, pair by score.
        """
        unpaired = self.competitors.copy()
        random.shuffle(unpaired)

        pairings = []
        while len(unpaired) >= 2:
            # Sort by score (descending) to pair similar competitors
            unpaired.sort(key=lambda c: c.score, reverse=True)
            
            # Take first two and pair them
            p1 = unpaired.pop(0)
            p2 = unpaired.pop(0)
            pairings.append((p1, p2))

        # If odd number, one competitor gets bye (automatic win)
        if unpaired:
            competitor = unpaired[0]
            competitor.wins += 1
            competitor.rounds_played += 1
            self.history.append(
                (competitor.name, "BYE", f"Round {len(self.get_rounds()) + 1}")
            )

        return pairings

    def record_match(self, winner: Competitor, loser: Competitor, round_num: int) -> None:
        """Record result of a match.
        
        Args:
            winner: Competitor that won the match
            loser: Competitor that lost the match
            round_num: Which round this match is from
        """
        winner.wins += 1
        winner.rounds_played += 1
        loser.losses += 1
        loser.rounds_played += 1
        self.history.append((winner.name, loser.name, f"Round {round_num}"))

    def get_rankings(self) -> List[Competitor]:
        """Get current rankings sorted by score (best first).
        
        Returns:
            List of competitors sorted by win ratio, then by number of wins
        """
        return sorted(
            self.competitors,
            key=lambda c: (c.score, c.wins),
            reverse=True
        )

    def get_rounds(self) -> List[Tuple[Competitor, Competitor]]:
        """Return all historical matchups."""
        return self.matchups
