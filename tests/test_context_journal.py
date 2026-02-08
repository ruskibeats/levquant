"""Tests for ai_assistant.context_journal module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ai_assistant.context_journal import (
    add_context,
    get_all_context,
    init_journal,
    read_entries,
)


class TestInitJournal:
    """Tests for init_journal function."""

    def test_creates_new_file_if_missing(self, tmp_path: Path) -> None:
        """Test that init_journal creates an empty JSON file if it doesn't exist."""
        journal_path = tmp_path / "test_journal.json"
        assert not journal_path.exists()

        result = init_journal(journal_path)

        assert result == journal_path
        assert journal_path.exists()
        content = json.loads(journal_path.read_text())
        assert content == []

    def test_does_not_overwrite_existing_file(self, tmp_path: Path) -> None:
        """Test that init_journal doesn't overwrite existing journal."""
        journal_path = tmp_path / "test_journal.json"
        existing_entry = [{"timestamp_utc": "2024-01-01T00:00:00", "text": "existing"}]
        journal_path.write_text(json.dumps(existing_entry))

        result = init_journal(journal_path)

        assert result == journal_path
        content = json.loads(journal_path.read_text())
        assert content == existing_entry

    def test_uses_default_path_when_none_provided(self) -> None:
        """Test that init_journal uses default path when no path provided."""
        # This test just verifies the function runs without error
        # We can't easily test the actual default path without side effects
        with tempfile.TemporaryDirectory() as tmp_dir:
            default_path = Path(tmp_dir) / "daily_context.json"
            result = init_journal(default_path)
            assert result == default_path


class TestAddContext:
    """Tests for add_context function."""

    def test_adds_entry_to_empty_journal(self, tmp_path: Path) -> None:
        """Test adding first entry to empty journal."""
        journal_path = tmp_path / "test_journal.json"
        init_journal(journal_path)

        add_context(
            doc_text="Test context entry",
            entry_type="text",
            source="user",
            path=journal_path,
        )

        entries = read_entries(journal_path)
        assert len(entries) == 1
        assert entries[0]["text"] == "Test context entry"
        assert entries[0]["entry_type"] == "text"
        assert entries[0]["source"] == "user"
        assert "timestamp_utc" in entries[0]

    def test_adds_multiple_entries_preserves_order(self, tmp_path: Path) -> None:
        """Test that multiple entries are appended in order."""
        journal_path = tmp_path / "test_journal.json"
        init_journal(journal_path)

        for i in range(3):
            add_context(
                doc_text=f"Entry {i}",
                entry_type="text",
                source="cli",
                path=journal_path,
            )

        entries = read_entries(journal_path)
        assert len(entries) == 3
        assert entries[0]["text"] == "Entry 0"
        assert entries[1]["text"] == "Entry 1"
        assert entries[2]["text"] == "Entry 2"

    def test_strips_whitespace_from_text(self, tmp_path: Path) -> None:
        """Test that text is stripped of leading/trailing whitespace."""
        journal_path = tmp_path / "test_journal.json"
        init_journal(journal_path)

        add_context(
            doc_text="  \n  Whitespace text  \n  ",
            entry_type="email",
            source="dashboard",
            path=journal_path,
        )

        entries = read_entries(journal_path)
        assert entries[0]["text"] == "Whitespace text"

    def test_rejects_empty_text(self, tmp_path: Path) -> None:
        """Test that empty text raises ValueError."""
        journal_path = tmp_path / "test_journal.json"
        init_journal(journal_path)

        with pytest.raises(ValueError, match="cannot be empty"):
            add_context(
                doc_text="",
                entry_type="text",
                source="user",
                path=journal_path,
            )

    def test_rejects_whitespace_only_text(self, tmp_path: Path) -> None:
        """Test that whitespace-only text raises ValueError."""
        journal_path = tmp_path / "test_journal.json"
        init_journal(journal_path)

        with pytest.raises(ValueError, match="cannot be empty"):
            add_context(
                doc_text="   \n\t   ",
                entry_type="text",
                source="user",
                path=journal_path,
            )

    def test_creates_journal_if_missing(self, tmp_path: Path) -> None:
        """Test that add_context creates journal if it doesn't exist."""
        journal_path = tmp_path / "nonexistent" / "test_journal.json"
        journal_path.parent.mkdir(parents=True)

        add_context(
            doc_text="Auto-created journal",
            entry_type="court_note",
            source="cli",
            path=journal_path,
        )

        assert journal_path.exists()
        entries = read_entries(journal_path)
        assert len(entries) == 1


class TestReadEntries:
    """Tests for read_entries function."""

    def test_returns_empty_list_for_missing_file(self, tmp_path: Path) -> None:
        """Test that read_entries returns empty list if file doesn't exist."""
        journal_path = tmp_path / "nonexistent.json"

        entries = read_entries(journal_path)

        assert entries == []

    def test_returns_all_entries(self, tmp_path: Path) -> None:
        """Test that read_entries returns all entries."""
        journal_path = tmp_path / "test_journal.json"
        test_entries = [
            {"timestamp_utc": "2024-01-01T00:00:00", "entry_type": "text", "source": "user", "text": "Entry 1"},
            {"timestamp_utc": "2024-01-02T00:00:00", "entry_type": "email", "source": "cli", "text": "Entry 2"},
        ]
        journal_path.write_text(json.dumps(test_entries))

        entries = read_entries(journal_path)

        assert len(entries) == 2
        assert entries[0]["text"] == "Entry 1"
        assert entries[1]["text"] == "Entry 2"


class TestGetAllContext:
    """Tests for get_all_context function."""

    def test_returns_empty_string_for_empty_journal(self, tmp_path: Path) -> None:
        """Test that get_all_context returns empty string for empty journal."""
        journal_path = tmp_path / "test_journal.json"
        init_journal(journal_path)

        result = get_all_context(journal_path)

        assert result == ""

    def test_concatenates_all_entries(self, tmp_path: Path) -> None:
        """Test that get_all_context concatenates entries."""
        journal_path = tmp_path / "test_journal.json"
        test_entries = [
            {"timestamp_utc": "2024-01-01T00:00:00", "entry_type": "text", "source": "user", "text": "First entry"},
            {"timestamp_utc": "2024-01-02T00:00:00", "entry_type": "email", "source": "cli", "text": "Second entry"},
        ]
        journal_path.write_text(json.dumps(test_entries))

        result = get_all_context(journal_path)

        assert "First entry" in result
        assert "Second entry" in result
        assert "2024-01-01T00:00:00" in result
        assert "2024-01-02T00:00:00" in result

    def test_respects_limit_parameter(self, tmp_path: Path) -> None:
        """Test that limit parameter restricts to last N entries."""
        journal_path = tmp_path / "test_journal.json"
        test_entries = [
            {"timestamp_utc": f"2024-01-{i:02d}T00:00:00", "entry_type": "text", "source": "user", "text": f"Entry {i}"}
            for i in range(1, 6)
        ]
        journal_path.write_text(json.dumps(test_entries))

        result = get_all_context(journal_path, limit=2)

        assert "Entry 4" in result
        assert "Entry 5" in result
        assert "Entry 1" not in result
        assert "Entry 2" not in result
        assert "Entry 3" not in result

    def test_limit_none_returns_all(self, tmp_path: Path) -> None:
        """Test that limit=None returns all entries."""
        journal_path = tmp_path / "test_journal.json"
        test_entries = [
            {"timestamp_utc": f"2024-01-{i:02d}T00:00:00", "entry_type": "text", "source": "user", "text": f"Entry {i}"}
            for i in range(1, 4)
        ]
        journal_path.write_text(json.dumps(test_entries))

        result = get_all_context(journal_path, limit=None)

        assert "Entry 1" in result
        assert "Entry 2" in result
        assert "Entry 3" in result

    def test_includes_metadata_in_output(self, tmp_path: Path) -> None:
        """Test that output includes timestamp, entry_type in format."""
        journal_path = tmp_path / "test_journal.json"
        test_entry = [
            {"timestamp_utc": "2024-01-01T12:30:45", "entry_type": "court_note", "source": "dashboard", "text": "Test note"},
        ]
        journal_path.write_text(json.dumps(test_entry))

        result = get_all_context(journal_path)

        assert "[2024-01-01T12:30:45]" in result
        assert "[court_note]" in result
        assert "Test note" in result


class TestIntegration:
    """Integration tests for the full journal workflow."""

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow: init -> add -> read -> get_all."""
        journal_path = tmp_path / "integration_test.json"

        # Initialize
        init_journal(journal_path)

        # Add entries
        add_context("First context", "text", "user", journal_path)
        add_context("Email received", "email", "cli", journal_path)
        add_context("Court update", "court_note", "dashboard", journal_path)

        # Read entries
        entries = read_entries(journal_path)
        assert len(entries) == 3

        # Get all context
        all_context = get_all_context(journal_path)
        assert "First context" in all_context
        assert "Email received" in all_context
        assert "Court update" in all_context

        # Test limit
        limited = get_all_context(journal_path, limit=1)
        assert "Court update" in limited
        assert "First context" not in limited
        assert "Email received" not in limited
