"""CLI interface for pyer."""

import argparse
import sys


def greet(name=""):
    """Return a greeting message."""
    target = name if name else "World"
    return f"Hello, {target}!"


def main(argv=None):
    """Parse CLI arguments and run the greet command."""
    parser = argparse.ArgumentParser(description="pyer CLI tools")
    parser.add_argument("command", nargs="?", default="greet",
                        help="Command to run (default: greet)")
    parser.add_argument("--name", default="",
                        help="Name to greet")

    args = parser.parse_args(argv)

    if args.command == "greet":
        print(greet(args.name))
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
