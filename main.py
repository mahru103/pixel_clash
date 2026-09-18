"""Rock Paper Scissors: Pixel Clash — entry point.

Run from the project root:

    python main.py
"""
from assets import preregister_fonts

# Fonts must be registered with the OS *before* Tk starts, otherwise Tk will
# not see the new families.
preregister_fonts()

from app import main  # noqa: E402  (import after font registration on purpose)

if __name__ == "__main__":
    main()
