import argparse
from src.matrix import run_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Time Machine - Commit matrix visualizer and editor")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year for the commit matrix (default: interactive settings)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="JSON file name or path for saving marked dates (default: interactive settings)"
    )
    parser.add_argument(
        "--no-settings",
        action="store_true",
        help="Skip settings screen and use defaults"
    )
    args = parser.parse_args()
    
    # Use provided args or show settings screen
    if args.year is not None and args.file is not None:
        year = args.year
        filename = args.file
    elif args.no_settings:
        year = 2015
        filename = "data.json"
    else:
        # Use defaults; settings screen will be shown by run_app
        year = args.year if args.year is not None else 2015
        filename = args.file if args.file is not None else "data.json"
    
    run_app(year, filename)