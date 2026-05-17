"""Main entry point for the Swiss-bracket ranker."""

import argparse
import sys
import webbrowser
from pathlib import Path
from ranker.file_io import read_items_from_file
from ranker.web_app import create_app


def main():
    """Main entry point - launches web interface."""
    parser = argparse.ArgumentParser(
        description="Rank items using Swiss-bracket style pairwise voting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ranker.main items.txt
  python -m ranker.main items.txt --rounds 10
  python -m ranker.main items.txt -r 7 --port 5001
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Path to input file (one item per line)"
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
    
    args = parser.parse_args()
    
    # Read items from file
    try:
        items = read_items_from_file(args.input_file)
        print(f"✓ Loaded {len(items)} items from {args.input_file}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create Flask app
    app = create_app(items, rounds=args.rounds)
    
    # Print info
    url = f"http://{args.host}:{args.port}"
    print(f"\n🚀 Ranker server starting...")
    print(f"📱 Open your browser: {url}")
    print(f"⚙️  Rounds: {args.rounds}")
    print(f"📊 Items: {len(items)}")
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
