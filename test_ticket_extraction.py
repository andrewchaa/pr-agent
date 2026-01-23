#!/usr/bin/env python3
"""
Test script for ticket number extraction (regex + AI).

This demonstrates the multi-method approach to extracting ticket numbers.
"""

import re


def extract_ticket_regex(branch_name: str, pattern: str = r"STAR-(\d+)") -> str:
    """Extract ticket using regex (fast but rigid)."""
    match = re.search(pattern, branch_name, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return None


def extract_ticket_ai_simulation(branch_name: str, ticket_prefix: str = "STAR") -> str:
    """
    Simulate AI extraction logic.

    In production, this would call the LLM.
    For testing, we'll use intelligent pattern matching.
    """
    # Look for common patterns that regex might miss
    patterns = [
        rf"{ticket_prefix.lower()}_(\d+)",  # star_123
        rf"{ticket_prefix.lower()}(\d+)",   # star123
        rf"{ticket_prefix.upper()}_(\d+)",  # STAR_123
        rf"{ticket_prefix.upper()}(\d+)",   # STAR123
        rf"{ticket_prefix}-(\d+)",          # STAR-123 (case-insensitive)
    ]

    for pattern in patterns:
        match = re.search(pattern, branch_name, re.IGNORECASE)
        if match:
            # Extract the number
            if match.groups():
                number = match.group(1)
            else:
                # Extract from full match
                number = re.search(r'\d+', match.group(0)).group(0)
            return f"{ticket_prefix.upper()}-{number}"

    return None


def test_extraction(branch_names: list):
    """Test ticket extraction on various branch names."""
    print("Testing Ticket Extraction\n" + "="*60)

    for branch in branch_names:
        print(f"\nBranch: {branch}")

        # Try regex first
        ticket_regex = extract_ticket_regex(branch)
        if ticket_regex:
            print(f"  ✓ Regex:  {ticket_regex}")
            continue
        else:
            print(f"  ✗ Regex:  No match")

        # Try AI extraction
        ticket_ai = extract_ticket_ai_simulation(branch)
        if ticket_ai:
            print(f"  ✓ AI:     {ticket_ai}")
        else:
            print(f"  ✗ AI:     No match")


if __name__ == "__main__":
    test_branches = [
        # Standard formats (regex should catch these)
        "feature/STAR-12345-add-feature",
        "STAR-999-bugfix",
        "star-422270-test",

        # Variations (AI should catch these)
        "bugfix_with_star_422270_somewhere",
        "feature_star_123_something",
        "my-work-STAR_789_feature",
        "star123feature",

        # No ticket
        "main",
        "develop",
        "feature-without-ticket",
    ]

    test_extraction(test_branches)

    print("\n" + "="*60)
    print("\nConclusion:")
    print("- Regex handles standard formats (fast)")
    print("- AI handles variations (flexible)")
    print("- Both methods complement each other!")
