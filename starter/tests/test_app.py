import app as app_module
import pytest


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    app_module.CURRENT.update(puzzle=None, solution=None)

    with app_module.app.test_client() as client:
        yield client


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200


@pytest.mark.parametrize("clues", [35, 45, 55, 81])
def test_new_game_returns_puzzle_with_requested_clue_count(client, clues):
    response = client.get("/new", query_string={"clues": clues})

    assert response.status_code == 200
    puzzle = response.json["puzzle"]
    assert len(puzzle) == 9
    assert all(len(row) == 9 for row in puzzle)
    assert sum(cell != 0 for row in puzzle for cell in row) == clues


@pytest.mark.parametrize("clues", ["easy", "16", "82"])
def test_new_game_rejects_invalid_clue_count(client, clues):
    response = client.get("/new", query_string={"clues": clues})

    assert response.status_code == 400
    assert "error" in response.json


def test_check_without_game_returns_error(client):
    response = client.post("/check", json={"board": []})

    assert response.status_code == 400
    assert response.json == {"error": "No game in progress"}


def test_check_returns_no_incorrect_cells_for_solution(client):
    client.get("/new")
    solution = app_module.CURRENT["solution"]

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.json == {"incorrect": []}


def test_check_reports_incorrect_cell(client):
    client.get("/new")
    board = [row.copy() for row in app_module.CURRENT["solution"]]
    board[0][0] = board[0][0] % 9 + 1

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.json == {"incorrect": [[0, 0]]}


def test_easy_fill_propagates_across_rows_columns_and_boxes(client):
    client.get("/new", query_string={"clues": 81})
    solution = app_module.CURRENT["solution"]
    app_module.CURRENT["puzzle"] = [row.copy() for row in solution]
    for row, col in [(0, 0), (0, 1), (4, 1), (4, 2)]:
        app_module.CURRENT["puzzle"][row][col] = 0
    board = [row.copy() for row in app_module.CURRENT["puzzle"]]
    board[0][0] = solution[0][0]

    response = client.post(
        "/check",
        json={"board": board, "easy_fill": {"row": 0, "col": 0}},
    )

    assert response.status_code == 200
    assert response.json["fills"] == [
        {"row": 0, "col": 1, "value": solution[0][1]},
        {"row": 4, "col": 1, "value": solution[4][1]},
        {"row": 4, "col": 2, "value": solution[4][2]},
    ]


def test_easy_fill_finds_single_cell_in_unrelated_box(client):
    client.get("/new", query_string={"clues": 81})
    solution = app_module.CURRENT["solution"]
    app_module.CURRENT["puzzle"] = [row.copy() for row in solution]
    for row, col in [(0, 0), (0, 1), (6, 0)]:
        app_module.CURRENT["puzzle"][row][col] = 0
    board = [row.copy() for row in app_module.CURRENT["puzzle"]]
    board[0][0] = solution[0][0]

    response = client.post(
        "/check",
        json={"board": board, "easy_fill": {"row": 0, "col": 0}},
    )

    assert response.status_code == 200
    assert response.json["fills"] == [
        {"row": 0, "col": 1, "value": solution[0][1]},
        {"row": 6, "col": 0, "value": solution[6][0]},
    ]


def test_easy_fill_does_not_run_when_triggering_value_is_wrong(client):
    client.get("/new", query_string={"clues": 81})
    solution = app_module.CURRENT["solution"]
    app_module.CURRENT["puzzle"] = [row.copy() for row in solution]
    app_module.CURRENT["puzzle"][0][0] = 0
    app_module.CURRENT["puzzle"][0][1] = 0
    board = [row.copy() for row in app_module.CURRENT["puzzle"]]
    board[0][0] = solution[0][0] % 9 + 1

    response = client.post(
        "/check",
        json={"board": board, "easy_fill": {"row": 0, "col": 0}},
    )

    assert response.status_code == 200
    assert response.json["fills"] == []


def test_hint_without_game_returns_error(client):
    response = client.post("/hint", json={"board": [[0] * 9 for _ in range(9)]})

    assert response.status_code == 400
    assert response.json == {"error": "No game in progress"}


def test_hint_returns_correct_value_for_unfilled_puzzle_cell(client):
    client.get("/new", query_string={"clues": 81})
    app_module.CURRENT["puzzle"][0][0] = 0
    board = [row.copy() for row in app_module.CURRENT["puzzle"]]
    board[0][0] = 0

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 200
    hint = response.json
    assert (hint["row"], hint["col"]) == (0, 0)
    assert hint["value"] == app_module.CURRENT["solution"][0][0]


def test_hint_does_not_overwrite_a_filled_cell(client):
    client.get("/new", query_string={"clues": 81})
    board = [row.copy() for row in app_module.CURRENT["puzzle"]]

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 400
    assert response.json == {"error": "No empty cells available for a hint"}


@pytest.mark.parametrize(
    "board",
    [
        None,
        [],
        [[0] * 9 for _ in range(8)],
        [[0] * 8 for _ in range(9)],
        [[0] * 8 + [10] for _ in range(9)],
    ],
)
def test_hint_rejects_invalid_board(client, board):
    client.get("/new")

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 400
    assert response.json == {
        "error": "Board must be a 9x9 grid of numbers from 0 to 9"
    }
