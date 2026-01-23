#!/usr/bin/env python3
"""
Test script for base branch auto-detection.

Demonstrates the improved base branch detection and error handling.
"""

from pr_agent.git_operations import GitOperations
from pr_agent.exceptions import BranchNameError


def test_branch_detection():
    """Test base branch detection in the current repository."""
    print("Base Branch Detection Test")
    print("=" * 60)

    try:
        git_ops = GitOperations()
        print("\n✓ Initialized in git repository")

        # Test 1: Get default branch
        print("\n1. Auto-detecting default branch...")
        default_branch = git_ops.get_default_branch()
        if default_branch:
            print(f"   ✓ Detected: {default_branch}")
        else:
            print("   ✗ Could not auto-detect default branch")

        # Test 2: Check if common branches exist
        print("\n2. Checking common branches:")
        for branch in ['main', 'master', 'develop', 'development']:
            exists = git_ops.branch_exists(branch)
            status = "✓" if exists else "✗"
            print(f"   {status} {branch}: {'exists' if exists else 'not found'}")

        # Test 3: Get available branches
        print("\n3. Available branches in repository:")
        branches = git_ops.get_available_branches()
        if branches:
            for branch in branches[:10]:  # Show first 10
                print(f"   - {branch}")
            if len(branches) > 10:
                print(f"   ... and {len(branches) - 10} more")
        else:
            print("   No branches found")

        # Test 4: Try to get diff with non-existent branch
        print("\n4. Testing error message with non-existent branch:")
        try:
            git_ops.get_diff("nonexistent-branch")
        except BranchNameError as e:
            print(f"   Error message preview:")
            for line in str(e).split('\n'):
                print(f"   | {line}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nNote: This test needs to be run from within a git repository")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_branch_detection()
