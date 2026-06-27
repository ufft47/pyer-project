"""Tests for the CLI greet command."""

from pyer.cli import greet


def test_greet_default_name():
    """greet() with no name should say Hello, World."""
    result = greet()
    assert result == "Hello, World!"


def test_greet_custom_name():
    """greet() with a name should say Hello, <name>."""
    result = greet("Hermes")
    assert result == "Hello, Hermes!"


def test_greet_empty_string():
    """greet() with empty string should fall back to World."""
    result = greet("")
    assert result == "Hello, World!"
