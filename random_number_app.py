#!/usr/bin/env python3
"""
random_number_app.py: A simple Python application to generate random integers between bounds.
"""
import random
import argparse

def main():
    """CLI to generate random integers between given bounds."""
    parser = argparse.ArgumentParser(
        description="Generate random integers between given bounds."
    )
    parser.add_argument(
        "--min", "-m", dest="min_value", type=int, default=1,
        help="Minimum integer value (inclusive). Default: 1."
    )
    parser.add_argument(
        "--max", "-M", dest="max_value", type=int, default=100,
        help="Maximum integer value (inclusive). Default: 100."
    )
    parser.add_argument(
        "--count", "-c", type=int, default=1,
        help="Number of random numbers to generate. Default: 1."
    )
    args = parser.parse_args()
    if args.min_value > args.max_value:
        parser.error(
            "Minimum value (--min) cannot be greater than maximum (--max)."
        )
    for _ in range(args.count):
        number = random.randint(args.min_value, args.max_value)
        print(number)

if __name__ == "__main__":
    main()