# Project Guidelines

## Architecture

- The Flask app and Sudoku rules live in `starter/app.py` and `starter/sudoku_logic.py`.
- Browser UI and game behavior live in `starter/templates/index.html` and `starter/static/`.
- Keep puzzle generation and solution validation authoritative on the server; do not expose the solution to the browser.
- Preserve the existing API and UI behavior when changing game features.

## Code and UX Conventions

- Keep changes focused and follow the existing Python, JavaScript, HTML, and CSS style.
- Validate client input at the Flask route boundary and return clear error responses for invalid requests.
- Keep generated puzzles valid and uniquely solvable; cover solver and generator changes with tests.
- Preserve responsive layout, accessible labels/status, and visible feedback for incorrect values, hints, and completed games.
- Keep browser-only preferences and leaderboard data in local storage; do not move them to server state without a requirement.

## Testing

- Install development dependencies from `starter/` with `pip install -r requirements-dev.txt`.
- Run tests from `starter/` with `python -m pytest -v`.
- Add or update focused tests for changed routes, Sudoku logic, and user-visible behavior.
