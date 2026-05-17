"""Flask web application for Swiss-bracket ranking."""

import json
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from ranker.ranker import SwissRanker, Competitor
from ranker.file_io import write_detailed_rankings


class RankerWebApp:
    """Web interface for the Swiss-bracket ranker."""

    def __init__(self, items: list[str], rounds: int = 5):
        """Initialize the web app.
        
        Args:
            items: List of items to rank
            rounds: Number of rounds to run
        """
        self.ranker = SwissRanker(items)
        self.total_rounds = rounds
        self.current_round = 1
        self.current_pairings = []
        self.current_match_idx = 0
        self.completed = False
        
    def app(self) -> Flask:
        """Create and configure Flask app."""
        app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static")
        )
        
        # Store reference to self for route handlers
        app.ranker_app = self
        
        @app.route("/")
        def index():
            return render_template("index.html")
        
        @app.route("/api/start", methods=["POST"])
        def start_ranking():
            """Start the ranking process."""
            self.current_round = 1
            self.current_match_idx = 0
            self.completed = False
            self.current_pairings = self.ranker.get_pairings()
            
            return jsonify({
                "status": "started",
                "total_rounds": self.total_rounds,
                "items_count": len(self.ranker.competitors)
            })
        
        @app.route("/api/next-match", methods=["GET"])
        def next_match():
            """Get next match or show results if complete."""
            if self.completed:
                return jsonify({
                    "status": "complete",
                    "message": "All rounds complete!"
                })
            
            if self.current_match_idx >= len(self.current_pairings):
                # Move to next round or finish
                if self.current_round < self.total_rounds:
                    self.current_round += 1
                    self.current_pairings = self.ranker.get_pairings()
                    self.current_match_idx = 0
                    
                    if not self.current_pairings:
                        self.completed = True
                        return self.get_results()
                else:
                    self.completed = True
                    return self.get_results()
            
            if self.current_match_idx >= len(self.current_pairings):
                self.completed = True
                return self.get_results()
            
            p1, p2 = self.current_pairings[self.current_match_idx]
            total_matches = len(self.current_pairings)
            
            return jsonify({
                "status": "match",
                "round": self.current_round,
                "match": self.current_match_idx + 1,
                "total_matches": total_matches,
                "option1": {
                    "name": p1.name,
                    "id": id(p1)
                },
                "option2": {
                    "name": p2.name,
                    "id": id(p2)
                }
            })
        
        @app.route("/api/vote", methods=["POST"])
        def vote():
            """Record a vote for the current matchup."""
            data = request.get_json()
            choice = data.get("choice")  # 1 or 2
            
            if self.current_match_idx >= len(self.current_pairings):
                return jsonify({"error": "No current match"}), 400
            
            p1, p2 = self.current_pairings[self.current_match_idx]
            
            if choice == 1:
                self.ranker.record_match(p1, p2, self.current_round)
            elif choice == 2:
                self.ranker.record_match(p2, p1, self.current_round)
            else:
                return jsonify({"error": "Invalid choice"}), 400
            
            self.current_match_idx += 1
            
            return jsonify({
                "status": "recorded",
                "winner": "option1" if choice == 1 else "option2"
            })
        
        def get_results():
            """Get final results."""
            rankings = self.ranker.get_rankings()
            return jsonify({
                "status": "complete",
                "rankings": [
                    {
                        "rank": rank,
                        "name": c.name,
                        "score": c.score,
                        "wins": c.wins,
                        "losses": c.losses,
                        "score_percent": f"{c.score:.1%}"
                    }
                    for rank, c in enumerate(rankings, 1)
                ]
            })
        
        @app.route("/api/results", methods=["GET"])
        def results():
            """Get current results."""
            return get_results()
        
        @app.route("/api/export", methods=["POST"])
        def export():
            """Export rankings to file."""
            data = request.get_json()
            output_path = data.get("path", "rankings.txt")
            
            rankings = self.ranker.get_rankings()
            rankings_tuples = [(c.name, c.score) for c in rankings]
            
            write_detailed_rankings(
                rankings_tuples,
                output_path,
                {
                    "Items": len(self.ranker.competitors),
                    "Rounds": self.total_rounds
                }
            )
            
            return jsonify({
                "status": "exported",
                "path": output_path
            })
        
        @app.route("/static/<path:path>")
        def send_static(path):
            return send_from_directory(app.static_folder, path)
        
        return app


def create_app(items: list[str], rounds: int = 5) -> Flask:
    """Factory function to create Flask app."""
    ranker_app = RankerWebApp(items, rounds)
    return ranker_app.app()
