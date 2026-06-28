import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyer_config import format_python_version_summary

def test_format_returns_string():
    result = format_python_version_summary()
    assert isinstance(result, str)

def test_format_contains_python():
    result = format_python_version_summary()
    assert "Python" in result

def test_format_contains_version():
    result = format_python_version_summary()
    assert "3." in result

def test_format_contains_bracket():
    result = format_python_version_summary()
    assert "[" in result and "]" in result
