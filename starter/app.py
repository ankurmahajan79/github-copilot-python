from flask import Flask, render_template, jsonify, request
import random
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_game():
    raw_clues = request.args.get('clues')
    try:
        clues = 35 if raw_clues is None else int(raw_clues)
    except ValueError:
        return jsonify({'error': 'Clues must be an integer between 17 and 81'}), 400
    try:
        puzzle, solution = sudoku_logic.generate_puzzle(clues)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    return jsonify({'puzzle': puzzle})

@app.route('/hint', methods=['POST'])
def get_hint():
    puzzle = CURRENT.get('puzzle')
    solution = CURRENT.get('solution')
    if puzzle is None or solution is None:
        return jsonify({'error': 'No game in progress'}), 400

    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(not isinstance(row, list) or len(row) != sudoku_logic.SIZE for row in board)
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < sudoku_logic.EMPTY
            or value > sudoku_logic.SIZE
            for row in board
            for value in row
        )
    ):
        return jsonify({'error': 'Board must be a 9x9 grid of numbers from 0 to 9'}), 400

    empty_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY and board[row][col] == sudoku_logic.EMPTY
    ]
    if not empty_cells:
        return jsonify({'error': 'No empty cells available for a hint'}), 400

    row, col = random.choice(empty_cells)
    return jsonify({'row': row, 'col': col, 'value': solution[row][col]})

@app.route('/check', methods=['POST'])
def check_solution():
    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    solution = CURRENT.get('solution')
    if solution is None or CURRENT.get('puzzle') is None:
        return jsonify({'error': 'No game in progress'}), 400
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(not isinstance(row, list) or len(row) != sudoku_logic.SIZE for row in board)
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < sudoku_logic.EMPTY
            or value > sudoku_logic.SIZE
            for row in board
            for value in row
        )
    ):
        return jsonify({'error': 'Board must be a 9x9 grid of numbers from 0 to 9'}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])

    fills = []
    trigger = data.get('easy_fill')
    if trigger is not None:
        if (
            not isinstance(trigger, dict)
            or not isinstance(trigger.get('row'), int)
            or isinstance(trigger.get('row'), bool)
            or not isinstance(trigger.get('col'), int)
            or isinstance(trigger.get('col'), bool)
            or not 0 <= trigger['row'] < sudoku_logic.SIZE
            or not 0 <= trigger['col'] < sudoku_logic.SIZE
        ):
            return jsonify({'error': 'Easy-fill location must contain a valid row and column'}), 400

        trigger_row = trigger['row']
        trigger_col = trigger['col']
        if (
            board[trigger_row][trigger_col] != sudoku_logic.EMPTY
            and [trigger_row, trigger_col] not in incorrect
        ):
            working_board = [row.copy() for row in board]
            pending_units = [
                ('row', trigger_row, None),
                ('column', trigger_col, None),
                ('box', trigger_row // 3, trigger_col // 3),
            ]
            pending_units.extend(
                [('row', row, None) for row in range(sudoku_logic.SIZE)]
                + [('column', col, None) for col in range(sudoku_logic.SIZE)]
                + [
                    ('box', box_row, box_col)
                    for box_row in range(3)
                    for box_col in range(3)
                ]
            )
            next_unit = 0

            while next_unit < len(pending_units):
                unit_type, unit_row, unit_col = pending_units[next_unit]
                next_unit += 1
                if unit_type == 'row':
                    cells = [(unit_row, col) for col in range(sudoku_logic.SIZE)]
                elif unit_type == 'column':
                    cells = [(row, unit_row) for row in range(sudoku_logic.SIZE)]
                else:
                    cells = [
                        (row, col)
                        for row in range(unit_row * 3, unit_row * 3 + 3)
                        for col in range(unit_col * 3, unit_col * 3 + 3)
                    ]

                if any(
                    working_board[row][col] != sudoku_logic.EMPTY
                    and working_board[row][col] != solution[row][col]
                    for row, col in cells
                ):
                    continue

                empty_cells = [
                    (row, col)
                    for row, col in cells
                    if working_board[row][col] == sudoku_logic.EMPTY
                    and CURRENT['puzzle'][row][col] == sudoku_logic.EMPTY
                ]
                if len(empty_cells) != 1:
                    continue

                row, col = empty_cells[0]
                value = solution[row][col]
                working_board[row][col] = value
                fills.append({'row': row, 'col': col, 'value': value})
                pending_units.extend([
                    ('row', row, None),
                    ('column', col, None),
                    ('box', row // 3, col // 3),
                ])

    result = {'incorrect': incorrect}
    if trigger is not None:
        result['fills'] = fills
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)