"""Tests for the Swiss-bracket ranker."""

import pytest
import tempfile
from pathlib import Path
from ranker import SwissRanker, Competitor, read_items_from_file, write_rankings_to_file


class TestCompetitor:
    """Tests for Competitor class."""

    def test_competitor_creation(self):
        """Test creating a competitor."""
        comp = Competitor("Item A")
        assert comp.name == "Item A"
        assert comp.wins == 0
        assert comp.losses == 0
        assert comp.score == 0.0

    def test_competitor_score_calculation(self):
        """Test score calculation."""
        comp = Competitor("Item A")
        comp.wins = 3
        comp.losses = 2
        comp.rounds_played = 5
        assert comp.score == 0.6  # 3/5


class TestSwissRanker:
    """Tests for SwissRanker class."""

    def test_ranker_initialization(self):
        """Test initializing ranker with items."""
        items = ["A", "B", "C", "D"]
        ranker = SwissRanker(items)
        assert len(ranker.competitors) == 4
        assert all(c.wins == 0 for c in ranker.competitors)

    def test_get_pairings(self):
        """Test that pairings are generated correctly."""
        items = ["A", "B", "C", "D"]
        ranker = SwissRanker(items)
        pairings = ranker.get_pairings()
        
        assert len(pairings) == 2  # 4 items = 2 matches
        assert all(len(pair) == 2 for pair in pairings)

    def test_record_match(self):
        """Test recording a match result."""
        ranker = SwissRanker(["A", "B"])
        c1, c2 = ranker.competitors
        
        ranker.record_match(c1, c2, round_num=1)
        
        assert c1.wins == 1
        assert c1.rounds_played == 1
        assert c2.losses == 1
        assert c2.rounds_played == 1

    def test_get_rankings(self):
        """Test getting rankings."""
        ranker = SwissRanker(["A", "B", "C"])
        
        # Manually set up a scenario
        ranker.competitors[0].wins = 2
        ranker.competitors[0].rounds_played = 2
        
        ranker.competitors[1].wins = 1
        ranker.competitors[1].rounds_played = 2
        
        ranker.competitors[2].wins = 0
        ranker.competitors[2].rounds_played = 2
        
        rankings = ranker.get_rankings()
        
        assert rankings[0].name == "A"
        assert rankings[1].name == "B"
        assert rankings[2].name == "C"

    def test_odd_number_of_competitors(self):
        """Test handling odd number of competitors (bye round)."""
        ranker = SwissRanker(["A", "B", "C"])
        pairings = ranker.get_pairings()
        
        # With 3 items, one gets a bye
        assert len(pairings) == 1  # Only 1 match
        # One competitor should have a bye (win auto-recorded)
        assert any(c.wins == 1 for c in ranker.competitors)


class TestFileIO:
    """Tests for file I/O functions."""

    def test_read_items_from_file(self):
        """Test reading items from a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Item A\n")
            f.write("Item B\n")
            f.write("Item C\n")
            temp_path = f.name
        
        try:
            items = read_items_from_file(temp_path)
            assert items == ["Item A", "Item B", "Item C"]
        finally:
            Path(temp_path).unlink()

    def test_read_items_with_empty_lines(self):
        """Test that empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Item A\n")
            f.write("\n")
            f.write("Item B\n")
            f.write("   \n")
            f.write("Item C\n")
            temp_path = f.name
        
        try:
            items = read_items_from_file(temp_path)
            assert items == ["Item A", "Item B", "Item C"]
        finally:
            Path(temp_path).unlink()

    def test_read_items_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            read_items_from_file("nonexistent_file.txt")

    def test_read_items_insufficient_items(self):
        """Test error when file has fewer than 2 items."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Only One Item\n")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                read_items_from_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_write_rankings_to_file(self):
        """Test writing rankings to a file."""
        rankings = [("Item A", 1.0), ("Item B", 0.5), ("Item C", 0.0)]
        
        with tempfile.NamedTemporaryFile(mode='r', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            write_rankings_to_file(rankings, temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            assert "1. Item A (100.0%)" in content
            assert "2. Item B (50.0%)" in content
            assert "3. Item C (0.0%)" in content
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
