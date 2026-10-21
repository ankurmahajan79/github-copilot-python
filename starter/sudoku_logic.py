import copy
import random

SIZE = 9
EMPTY = 0
MIN_UNIQUE_CLUES = 17
MAX_GENERATION_ATTEMPTS = 100

def deep_copy(board):
    return copy.deepcopy(board)

def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True

def remove_cells(board, clues):
    attempts = SIZE * SIZE - clues
    while attempts > 0:
        row = random.randrange(SIZE)
        col = random.randrange(SIZE)
        if board[row][col] != EMPTY:
            board[row][col] = EMPTY
            attempts -= 1

def count_solutions(board, limit=2):
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if len(board) != SIZE or any(len(row) != SIZE for row in board):
        return 0
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value > SIZE
        for row in board
        for value in row
    ):
        return 0

    working_board = deep_copy(board)
    for row in range(SIZE):
        for col in range(SIZE):
            value = working_board[row][col]
            if value != EMPTY:
                working_board[row][col] = EMPTY
                safe = is_safe(working_board, row, col, value)
                working_board[row][col] = value
                if not safe:
                    return 0

    def search():
        best_cell = None
        best_candidates = None

        for row in range(SIZE):
            for col in range(SIZE):
                if working_board[row][col] != EMPTY:
                    continue

                candidates = [
                    number
                    for number in range(1, SIZE + 1)
                    if is_safe(working_board, row, col, number)
                ]
                if not candidates:
                    return 0
                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_cell = (row, col)
                    best_candidates = candidates
                    if len(best_candidates) == 1:
                        break
            if best_candidates is not None and len(best_candidates) == 1:
                break

        if best_cell is None:
            return 1

        row, col = best_cell
        solutions = 0
        for candidate in best_candidates:
            working_board[row][col] = candidate
            solutions += search()
            working_board[row][col] = EMPTY
            if solutions >= limit:
                return limit
        return solutions

    return search()

def generate_puzzle(clues=35):
    if (
        not isinstance(clues, int)
        or isinstance(clues, bool)
        or clues < MIN_UNIQUE_CLUES
        or clues > SIZE * SIZE
    ):
        raise ValueError(
            f"clues must be between {MIN_UNIQUE_CLUES} and {SIZE * SIZE}"
        )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        solution = create_empty_board()
        fill_board(solution)
        puzzle = deep_copy(solution)
        remove_cells(puzzle, clues)
        if count_solutions(puzzle) == 1:
            return puzzle, solution

    raise RuntimeError(
        f"could not generate a unique puzzle with {clues} clues "
        f"after {MAX_GENERATION_ATTEMPTS} attempts"
    )
