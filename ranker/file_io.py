"""File I/O utilities for reading and writing ranking data."""

from pathlib import Path
from typing import List, Tuple


def read_items_from_file(filepath: str) -> List[str]:
    """Read items from a text file (one item per line).
    
    Args:
        filepath: Path to the input text file
        
    Returns:
        List of items (non-empty lines, stripped of whitespace)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file has fewer than 2 items
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        items = [line.strip() for line in f if line.strip()]
    
    if len(items) < 2:
        raise ValueError(f"File must contain at least 2 items, found {len(items)}")
    
    return items


def write_rankings_to_file(rankings: List[Tuple[str, float]], filepath: str) -> None:
    """Write rankings to a text file.
    
    Args:
        rankings: List of (name, score) tuples in ranked order
        filepath: Path to the output file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        for rank, (name, score) in enumerate(rankings, 1):
            f.write(f"{rank}. {name} ({score:.1%})\n")


def write_detailed_rankings(
    rankings: List[Tuple[str, float]],
    filepath: str,
    additional_info: dict = None
) -> None:
    """Write detailed ranking information including metadata.
    
    Args:
        rankings: List of (name, score) tuples in ranked order
        filepath: Path to the output file
        additional_info: Optional dictionary with extra information to include
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        if additional_info:
            for key, value in additional_info.items():
                f.write(f"# {key}: {value}\n")
            f.write("\n")
        
        for rank, (name, score) in enumerate(rankings, 1):
            f.write(f"{rank}. {name} ({score:.1%})\n")
