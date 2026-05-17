# Ranker

A Python utility to rank a list of items using Swiss-bracket style pairwise voting. Input items from a text file, vote on matchups using a beautiful web interface, and get a ranked list from best to worst.

## Features

- **Swiss-Bracket Ranking**: Items are paired up in each round based on their current score
- **Web Interface**: Modern, responsive UI with side-by-side voting buttons
- **Keyboard Shortcuts**: Press 1 or 2 to vote, or click the options
- **Beautiful Design**: Dark theme with smooth animations (2560x1440 optimized)
- **Configurable Rounds**: Adjust number of ranking rounds for accuracy
- **File I/O**: Read from text files, save rankings to output
- **Auto-Export**: Export final rankings to file

## Installation

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Create an input file

Create a text file with one item per line:

```
# flavors.txt
Chocolate
Vanilla
Strawberry
Mint Chip
Caramel Swirl
```

### 2. Run the ranker

```bash
python -m ranker.main flavors.txt
```

The web interface will automatically open in your browser at `http://localhost:5000`

### 3. Vote on matchups

- Click your preference, or press **1** or **2** on your keyboard
- Each round presents items that have similar records
- Progress bar shows how far through the ranking you are

### 4. Get results

After all rounds complete, rankings are displayed with:
- Final ranking and medals (🥇 🥈 🥉)
- Win/loss record
- Win percentage
- One-click export to file

## Usage

### Command-line Options

```bash
python -m ranker.main INPUT_FILE [OPTIONS]

Options:
  -r, --rounds ROUNDS      Number of ranking rounds (default: 5)
  -p, --port PORT          Port to run server on (default: 5000)
  --host HOST              Host to bind to (default: 127.0.0.1)
  --no-browser             Don't open browser automatically
  -h, --help               Show help message
```

### Examples

Run with default settings (opens browser at localhost:5000):
```bash
python -m ranker.main items.txt
```

Run with 10 rounds for more accurate results:
```bash
python -m ranker.main items.txt --rounds 10
```

Run on a different port:
```bash
python -m ranker.main items.txt --port 8080
```

Don't automatically open browser:
```bash
python -m ranker.main items.txt --no-browser
```

Combine options:
```bash
python -m ranker.main items.txt --rounds 7 --port 3000
```

## Using as a Library

### Web App

```python
from ranker import create_app, read_items_from_file

# Read items
items = read_items_from_file("items.txt")

# Create Flask app
app = create_app(items, rounds=5)

# Run the server
app.run(host="127.0.0.1", port=5000)
```

### Programmatic Ranking (without web UI)

```python
from ranker import SwissRanker, RankerCLI, read_items_from_file, write_rankings_to_file

# Read items
items = read_items_from_file("items.txt")

# Create ranker and run programmatically
ranker = SwissRanker(items)

# Manually conduct matches
p1, p2 = ranker.competitors[0], ranker.competitors[1]
ranker.record_match(p1, p2, round_num=1)

# Get rankings
rankings = ranker.get_rankings()
write_rankings_to_file([(c.name, c.score) for c in rankings], "output.txt")
```

## How Swiss Brackets Work

The Swiss-bracket system is designed to rank items accurately with minimal comparisons:

1. **Round 1**: Items are randomly paired
2. **Subsequent Rounds**: Items are paired with others having similar win/loss records
3. **Scoring**: Each item's score = wins / total rounds played
4. **Final Ranking**: Items ranked by win percentage

This is more efficient than a round-robin tournament (where every item must face every other item) while providing reasonable ranking accuracy.

## Testing

Run the test suite:

```bash
pytest tests/
```

With verbose output:

```bash
pytest tests/ -v
```

## Browser Compatibility

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

Optimized for 2560x1440 resolution but works on any modern display.

## Input File Format

- One item per line
- Empty lines are ignored
- Leading/trailing whitespace is stripped
- Minimum 2 items required

Example:

```
Python
JavaScript
Rust
Go
C++

Ruby
```

## Output Format

Rankings are saved with the format:

```
# Items: 5
# Rounds: 5
# Source: items.txt

1. Item A (100%)
2. Item B (80%)
3. Item C (60%)
4. Item D (40%)
5. Item E (20%)
```

## Requirements

- Python 3.10+
- Flask 3.0+ (installed automatically)
- pytest (for testing, optional)

## License

Apache 2.0
