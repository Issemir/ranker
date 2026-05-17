"""Flask web application for Swiss-bracket ranking."""

import json
import os
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from ranker.ranker import SwissRanker, Competitor
from ranker.file_io import write_detailed_rankings
from ranker.database import Database


class RankerWebApp:
    """Web interface for the Swiss-bracket ranker."""

    def __init__(self, default_rounds: int = 5, db: Database = None):
        """Initialize the web app.
        
        Args:
            default_rounds: Default number of rounds to run
            db: Database instance for user management
        """
        self.default_rounds = default_rounds
        self.db = db or Database()
        # Dictionary to store active ranking sessions per user
        # Key: user_id, Value: {"ranker": RankerWebApp, "items": list, "rounds": int}
        self.user_sessions = {}
        
    def _get_user_ranker(self, user_id: int):
        """Get the active ranker for a user."""
        return self.user_sessions.get(user_id, {}).get("ranker")
    
    def _set_user_ranker(self, user_id: int, ranker: SwissRanker, items: list, rounds: int):
        """Store a ranker session for a user."""
        self.user_sessions[user_id] = {
            "ranker": ranker,
            "items": items,
            "rounds": rounds
        }
        
    def app(self) -> Flask:
        """Create and configure Flask app."""
        app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static")
        )
        
        # Configure session
        app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
        app.config["SESSION_COOKIE_SECURE"] = False
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 30
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
        
        # File upload configuration
        UPLOAD_FOLDER = Path("temp_uploads")
        UPLOAD_FOLDER.mkdir(exist_ok=True)
        app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
        ALLOWED_EXTENSIONS = {"txt"}
        
        def allowed_file(filename):
            return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        
        # Store reference to self for route handlers
        app.ranker_app = self
        
        # Authentication middleware
        def login_required(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if "user_id" not in session:
                    return jsonify({"error": "Not authenticated", "redirect": "/login"}), 401
                return f(*args, **kwargs)
            return decorated_function
        
        # Routes
        @app.route("/")
        def index():
            if "user_id" in session:
                return redirect(url_for("dashboard"))
            return redirect(url_for("login_page"))
        
        @app.route("/login", methods=["GET"])
        def login_page():
            if "user_id" in session:
                return redirect(url_for("dashboard"))
            return render_template("login.html")
        
        @app.route("/register", methods=["GET"])
        def register_page():
            if "user_id" in session:
                return redirect(url_for("dashboard"))
            return render_template("register.html")
        
        @app.route("/dashboard", methods=["GET"])
        def dashboard():
            if "user_id" not in session:
                return redirect(url_for("login_page"))
            
            user = self.db.get_user_by_id(session["user_id"])
            if not user:
                session.clear()
                return redirect(url_for("login_page"))
            
            return render_template("dashboard.html", user=user)
        
        @app.route("/ranker", methods=["GET"])
        def ranker_page():
            if "user_id" not in session:
                return redirect(url_for("login_page"))
            return render_template("index.html")
        
        @app.route("/history/<int:ranking_id>", methods=["GET"])
        def view_ranking(ranking_id):
            if "user_id" not in session:
                return redirect(url_for("login_page"))
            
            ranking = self.db.get_ranking_by_id(ranking_id, session["user_id"])
            if not ranking:
                return render_template("error.html", message="Ranking not found"), 404
            
            return render_template("ranking_detail.html", ranking=ranking)
        
        # API Routes
        @app.route("/api/register", methods=["POST"])
        def register():
            """Register a new user."""
            data = request.get_json()
            email = data.get("email", "").strip()
            password = data.get("password", "")
            password_confirm = data.get("password_confirm", "")
            
            if not email or "@" not in email:
                return jsonify({"error": "Invalid email"}), 400
            
            if password != password_confirm:
                return jsonify({"error": "Passwords don't match"}), 400
            
            success, message = self.db.create_user(email, password)
            
            if success:
                return jsonify({"status": "success", "message": message})
            return jsonify({"error": message}), 400
        
        @app.route("/api/login", methods=["POST"])
        def login():
            """Login a user."""
            data = request.get_json()
            email = data.get("email", "").strip()
            password = data.get("password", "")
            
            authenticated, user_id = self.db.authenticate_user(email, password)
            
            if authenticated:
                session.permanent = True
                session["user_id"] = user_id
                user = self.db.get_user_by_id(user_id)
                return jsonify({
                    "status": "success",
                    "message": f"Welcome, {user['email']}!",
                    "redirect": "/dashboard"
                })
            
            return jsonify({"error": "Invalid email or password"}), 401
        
        @app.route("/api/logout", methods=["POST"])
        def logout():
            """Logout user."""
            session.clear()
            return jsonify({"status": "success", "message": "Logged out"})

        @app.route("/api/user", methods=["GET"])
        @login_required
        def current_user():
            """Get the authenticated user's info."""
            user = self.db.get_user_by_id(session["user_id"])
            return jsonify({
                "status": "success",
                "user": {
                    "id": session["user_id"],
                    "email": user["email"] if user else None
                }
            })

        @app.route("/api/rankings-history", methods=["GET"])
        @login_required
        def rankings_history():
            """Get user's ranking history."""
            rankings = self.db.get_user_rankings(session["user_id"])
            return jsonify({
                "status": "success",
                "rankings": [
                    {
                        "id": r["id"],
                        "session_name": r["session_name"] or "Unnamed",
                        "items_count": len(r["items"]),
                        "rounds": r["rounds"],
                        "created_at": r["created_at"],
                        "top_item": r["results"][0][0] if r["results"] else "N/A"
                    }
                    for r in rankings
                ]
            })
        
        @app.route("/api/upload-file", methods=["POST"])
        @login_required
        def upload_file():
            """Handle file upload for ranking."""
            user_id = session["user_id"]
            
            if "file" not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            
            if not allowed_file(file.filename):
                return jsonify({"error": "Only .txt files are allowed"}), 400
            
            try:
                # Read file content
                content = file.read().decode("utf-8")
                items = [line.strip() for line in content.split("\n") if line.strip()]
                
                if len(items) < 2:
                    return jsonify({"error": "File must contain at least 2 items (one per line)"}), 400
                
                if len(items) > 1000:
                    return jsonify({"error": "File cannot contain more than 1000 items"}), 400
                
                # Get rounds from request (default to app default)
                rounds = request.form.get("rounds", self.default_rounds, type=int)
                rounds = max(1, min(rounds, 20))  # Clamp between 1 and 20
                
                # Create new ranker for this user
                ranker = SwissRanker(items)
                self._set_user_ranker(user_id, ranker, items, rounds)
                
                return jsonify({
                    "status": "success",
                    "message": f"Uploaded {len(items)} items",
                    "items_count": len(items),
                    "redirect": "/ranker"
                })
            
            except Exception as e:
                return jsonify({"error": f"Error processing file: {str(e)}"}), 500
        
        @app.route("/api/start", methods=["POST"])
        @login_required
        def start_ranking():
            """Start the ranking process."""
            user_id = session["user_id"]
            ranker = self._get_user_ranker(user_id)
            
            if not ranker:
                return jsonify({"error": "No file uploaded. Please upload a file first."}), 400
            
            session_data = self.user_sessions[user_id]
            current_pairings = ranker.get_pairings()
            
            # Store current state in session
            session["current_round"] = 1
            session["current_match_idx"] = 0
            session["completed"] = False
            session["total_rounds"] = session_data["rounds"]
            session["current_pairings_count"] = len(current_pairings)
            session.modified = True
            
            return jsonify({
                "status": "started",
                "total_rounds": session_data["rounds"],
                "items_count": len(session_data["items"])
            })
        
        @app.route("/api/next-match", methods=["GET"])
        @login_required
        def next_match():
            """Get next match or show results if complete."""
            user_id = session["user_id"]
            ranker = self._get_user_ranker(user_id)
            
            if not ranker:
                return jsonify({"error": "No active ranking session"}), 400
            
            session_data = self.user_sessions[user_id]
            current_round = session.get("current_round", 1)
            current_match_idx = session.get("current_match_idx", 0)
            total_rounds = session_data["rounds"]
            completed = session.get("completed", False)
            
            if completed:
                return jsonify({
                    "status": "complete",
                    "message": "All rounds complete!"
                })
            
            # Get current pairings for this round
            if current_match_idx >= session.get("current_pairings_count", 0):
                # Move to next round or finish
                if current_round < total_rounds:
                    current_round += 1
                    current_pairings = ranker.get_pairings()
                    current_match_idx = 0
                    
                    session["current_round"] = current_round
                    session["current_match_idx"] = current_match_idx
                    session["current_pairings_count"] = len(current_pairings)
                    session.modified = True
                    
                    if not current_pairings:
                        session["completed"] = True
                        session.modified = True
                        rankings = ranker.get_rankings()
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
                else:
                    session["completed"] = True
                    session.modified = True
                    rankings = ranker.get_rankings()
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
            
            if current_match_idx >= session.get("current_pairings_count", 0):
                session["completed"] = True
                session.modified = True
                rankings = ranker.get_rankings()
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
            
            # Get pairings for current round (recreate them since we store by index)
            pairings = ranker.get_pairings()
            if current_match_idx >= len(pairings):
                rankings = ranker.get_rankings()
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
            
            p1, p2 = pairings[current_match_idx]
            total_matches = len(pairings)
            
            return jsonify({
                "status": "match",
                "round": current_round,
                "match": current_match_idx + 1,
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
        @login_required
        def vote():
            """Record a vote for the current matchup."""
            user_id = session["user_id"]
            ranker = self._get_user_ranker(user_id)
            
            if not ranker:
                return jsonify({"error": "No active ranking session"}), 400
            
            data = request.get_json()
            choice = data.get("choice")
            
            current_round = session.get("current_round", 1)
            current_match_idx = session.get("current_match_idx", 0)
            
            # Get current pairings
            #pairings = ranker.get_pairings()
            pairings = ranker.pairings
            if current_match_idx >= len(pairings):
                return jsonify({"error": "No current match"}), 400
            
            p1, p2 = pairings[current_match_idx]
            
            if choice == 1:
                ranker.record_match(p1, p2, current_round)
            elif choice == 2:
                ranker.record_match(p2, p1, current_round)
            else:
                return jsonify({"error": "Invalid choice"}), 400
            
            # Update session
            session["current_match_idx"] = current_match_idx + 1
            session.modified = True
            
            return jsonify({
                "status": "recorded",
                "winner": "option1" if choice == 1 else "option2"
            })
        
        def get_results(ranker, original_items):
            """Get final results."""
            rankings = ranker.get_rankings()
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
        @login_required
        def results():
            """Get current results."""
            user_id = session["user_id"]
            ranker = self._get_user_ranker(user_id)
            session_data = self.user_sessions.get(user_id, {})
            
            if not ranker:
                return jsonify({"error": "No active ranking session"}), 400
            
            return get_results(ranker, session_data.get("items", []))
        
        @app.route("/api/save-ranking", methods=["POST"])
        @login_required
        def save_ranking():
            """Save the completed ranking to user's history."""
            user_id = session["user_id"]
            ranker = self._get_user_ranker(user_id)
            session_data = self.user_sessions.get(user_id, {})
            
            if not ranker:
                return jsonify({"error": "No active ranking session"}), 400
            
            data = request.get_json()
            session_name = data.get("session_name")
            
            rankings = ranker.get_rankings()
            results_data = [(c.name, c.score) for c in rankings]
            
            success = self.db.save_ranking(
                user_id,
                session_data.get("items", []),
                session_data.get("rounds", self.default_rounds),
                results_data,
                session_name
            )
            
            if success:
                return jsonify({"status": "saved", "message": "Ranking saved to history"})
            return jsonify({"error": "Failed to save ranking"}), 500
        
        @app.route("/api/export", methods=["POST"])
        @login_required
        def export():
            """Export rankings to file."""
            user_id = session["user_id"]
            ranker = self._get_user_ranker(user_id)
            session_data = self.user_sessions.get(user_id, {})
            
            if not ranker:
                return jsonify({"error": "No active ranking session"}), 400
            
            data = request.get_json()
            output_path = data.get("path", "rankings.txt")
            
            rankings = ranker.get_rankings()
            rankings_tuples = [(c.name, c.score) for c in rankings]
            
            write_detailed_rankings(
                rankings_tuples,
                output_path,
                {
                    "Items": len(session_data.get("items", [])),
                    "Rounds": session_data.get("rounds", self.default_rounds)
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


def create_app(items: list[str] = None, rounds: int = 5, db: Database = None) -> Flask:
    """Factory function to create Flask app.
    
    Args:
        items: Optional list of items (for backward compatibility, typically empty)
        rounds: Default number of rounds
        db: Database instance
    """
    ranker_app = RankerWebApp(rounds, db)
    return ranker_app.app()
