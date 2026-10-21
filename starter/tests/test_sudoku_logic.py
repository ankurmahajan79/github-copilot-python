import pytest

import sudoku_logic


def test_create_empty_board_has_nine_rows_and_columns():
    board = sudoku_logic.create_empty_board()

    expected = [
        [sudoku_logic.EMPTY] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE)
    ]
    assert board == expected


def test_deep_copy_does_not_share_rows():
    board = sudoku_logic.create_empty_board()

    copied_board = sudoku_logic.deep_copy(board)
    copied_board[0][0] = 1

    assert board[0][0] == sudoku_logic.EMPTY


@pytest.mark.parametrize(
    ("row", "col", "existing_row", "existing_col"),
    [
        (0, 1, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
    ],
)
def test_is_safe_rejects_duplicates_in_row_column_or_box(
    row, col, existing_row, existing_col
):
    board = sudoku_logic.create_empty_board()
    board[existing_row][existing_col] = 5

    assert not sudoku_logic.is_safe(board, row, col, 5)


def test_is_safe_accepts_nonconflicting_number():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.is_safe(board, 0, 0, 5)


def test_count_solutions_counts_completed_board_once():
    board = sudoku_logic.create_empty_board()
    assert sudoku_logic.fill_board(board)

    assert sudoku_logic.count_solutions(board) == 1


def test_count_solutions_stops_at_limit_for_empty_board():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(board, limit=2) == 2


def _is_valid_solution(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))
    rows = [set(row) for row in board]
    columns = [
        {board[row][col] for row in range(sudoku_logic.SIZE)}
        for col in range(sudoku_logic.SIZE)
    ]
    boxes = [
        {
            board[row][col]
            for row in range(box_row, box_row + 3)
            for col in range(box_col, box_col + 3)
        }
        for box_row in (0, 3, 6)
        for box_col in (0, 3, 6)
    ]

    return all(group == expected for group in rows + columns + boxes)


@pytest.mark.parametrize("clues", [35, 45, 55, 81])
def test_generate_puzzle_preserves_solution_and_requested_clue_count(clues):
    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert _is_valid_solution(solution)
    assert sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row) == clues
    assert all(
        clue == sudoku_logic.EMPTY or clue == solution[row][col]
        for row, values in enumerate(puzzle)
        for col, clue in enumerate(values)
    )
    assert sudoku_logic.count_solutions(puzzle) == 1


@pytest.mark.parametrize("clues", [0, 16, 82])
def test_generate_puzzle_rejects_clue_counts_without_supported_unique_puzzles(clues):
    with pytest.raises(ValueError, match="clues must be between"):
        sudoku_logic.generate_puzzle(clues)
