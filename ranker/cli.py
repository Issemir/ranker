"""Command-line interface for the Swiss bracket ranker."""

from typing import List, Tuple
from ranker.ranker import SwissRanker, Competitor


class RankerCLI:
    """Interactive CLI for ranking items using pairwise comparisons."""

    def __init__(self, items: List[str], rounds: int = 5):
        """Initialize the CLI.
        
        Args:
            items: List of items to rank
            rounds: Number of rounds to run (more rounds = more accurate ranking)
        """
        self.ranker = SwissRanker(items)
        self.total_rounds = rounds
        self.current_round = 0

    def display_matchup(self, p1: Competitor, p2: Competitor, match_num: int, total_matches: int) -> None:
        """Display a matchup to the user."""
        print(f"\n--- Match {match_num}/{total_matches} (Round {self.current_round}) ---")
        print(f"[1] {p1.name}")
        print(f"[2] {p2.name}")

    def get_vote(self) -> int:
        """Get user's vote for winner (1 or 2)."""
        while True:
            try:
                choice = input("Choose winner (1 or 2): ").strip()
                if choice in ["1", "2"]:
                    return int(choice)
                print("Invalid choice. Please enter 1 or 2.")
            except KeyboardInterrupt:
                print("\nRanking cancelled.")
                exit(0)

    def run_round(self) -> None:
        """Run one complete round of matches."""
        pairings = self.ranker.get_pairings()
        
        if not pairings:
            print("No matches to play this round.")
            return

        print(f"\n{'='*50}")
        print(f"ROUND {self.current_round} - {len(pairings)} matches")
        print(f"{'='*50}")

        for idx, (p1, p2) in enumerate(pairings, 1):
            self.display_matchup(p1, p2, idx, len(pairings))
            vote = self.get_vote()
            
            if vote == 1:
                self.ranker.record_match(p1, p2, self.current_round)
                print(f"✓ {p1.name} wins!")
            else:
                self.ranker.record_match(p2, p1, self.current_round)
                print(f"✓ {p2.name} wins!")

    def run_ranking(self) -> List[Tuple[str, float]]:
        """Run the complete ranking process.
        
        Returns:
            List of (name, score) tuples in ranked order
        """
        print(f"\n{'='*50}")
        print(f"Starting Swiss-bracket ranking")
        print(f"Items to rank: {len(self.ranker.competitors)}")
        print(f"Rounds: {self.total_rounds}")
        print(f"{'='*50}")

        for round_num in range(1, self.total_rounds + 1):
            self.current_round = round_num
            self.run_round()
            self.print_standings()

        return self.get_final_rankings()

    def print_standings(self) -> None:
        """Print current standings."""
        print(f"\n--- Standings after Round {self.current_round} ---")
        rankings = self.ranker.get_rankings()
        for rank, competitor in enumerate(rankings, 1):
            print(f"{rank}. {competitor.name} - {competitor.wins}W-{competitor.losses}L ({competitor.score:.1%})")

    def get_final_rankings(self) -> List[Tuple[str, float]]:
        """Get final ranked list."""
        rankings = self.ranker.get_rankings()
        return [(c.name, c.score) for c in rankings]

    def print_final_results(self, rankings: List[Tuple[str, float]]) -> None:
        """Print final rankings in a formatted way."""
        print(f"\n{'='*50}")
        print("FINAL RANKINGS")
        print(f"{'='*50}")
        for rank, (name, score) in enumerate(rankings, 1):
            print(f"{rank}. {name} ({score:.1%})")
