"""Main entry point for the Swiss-bracket ranker."""

import argparse
import sys
import webbrowser
from pathlib import Path
from ranker.web_app import create_app
from ranker.database import Database


def main():
    """Main entry point - launches web interface."""
    parser = argparse.ArgumentParser(
        description="Rank items using Swiss-bracket style pairwise voting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ranker.main
  python -m ranker.main --rounds 10
  python -m ranker.main -r 7 --port 5001
        """
    )
    
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=5,
        help="Number of ranking rounds (default: 5)"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=5000,
        help="Port to run server on (default: 5000)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )
    parser.add_argument(
        "--db",
        default="data/ranker.db",
        help="Path to database file (default: data/ranker.db)"
    )
    
    args = parser.parse_args()
    
    # Initialize database
    db = Database(args.db)
    print(f"✓ Database initialized: {args.db}")
    
    # Create Flask app (no items needed - users will upload)
    app = create_app(items=[], rounds=args.rounds, db=db)
    
    # Print info
    url = f"http://{args.host}:{args.port}"
    print(f"\n🚀 Ranker server starting...")
    print(f"📱 Open your browser: {url}")
    print(f"⚙️  Default rounds: {args.rounds}")
    print(f"💾 Database: {args.db}")
    print(f"\n(Press Ctrl+C to stop)")
    
    # Open browser if not disabled
    if not args.no_browser:
        webbrowser.open(url)
    
    # Run server
    try:
        app.run(host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
