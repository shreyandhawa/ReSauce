import sys

from resauce import __version__


def main() -> int:
    print(f"ReSauce {__version__}")
    print(f"Python {sys.version.split()[0]}")
    print("Environment is set up. No analysis is performed yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
