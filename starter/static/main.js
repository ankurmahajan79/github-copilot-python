// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const SCORE_STORAGE_KEY = 'sudokuTopScores';
const THEME_STORAGE_KEY = 'sudokuTheme';
let puzzle = [];
let timerStartedAt = null;
let timerInterval = null;
let hintsUsed = 0;
let gameCompleted = false;
let checkRequestId = 0;

function formatTime(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const formattedMinutes = String(minutes).padStart(2, '0');
  const formattedSeconds = String(seconds).padStart(2, '0');

  return hours > 0
    ? `${String(hours).padStart(2, '0')}:${formattedMinutes}:${formattedSeconds}`
    : `${formattedMinutes}:${formattedSeconds}`;
}

function updateTimer() {
  if (timerStartedAt === null) return;

  document.getElementById('timer').innerText = formatTime(getElapsedSeconds());
}

function getElapsedSeconds() {
  if (timerStartedAt === null) return 0;

  return Math.floor((performance.now() - timerStartedAt) / 1000);
}

function startTimer() {
  if (timerInterval !== null) clearInterval(timerInterval);
  timerStartedAt = performance.now();
  document.getElementById('timer').innerText = '00:00';
  timerInterval = setInterval(updateTimer, 1000);
}

function stopTimer() {
  updateTimer();
  const elapsedSeconds = getElapsedSeconds();
  if (timerInterval !== null) clearInterval(timerInterval);
  timerInterval = null;
  timerStartedAt = null;
  return elapsedSeconds;
}

function setDarkMode(enabled) {
  document.body.classList.toggle('dark-mode', enabled);
  const button = document.getElementById('theme-toggle');
  button.textContent = enabled ? 'Light mode' : 'Dark mode';
  button.setAttribute('aria-pressed', String(enabled));
}

function initializeTheme() {
  let darkMode = false;
  try {
    darkMode = localStorage.getItem(THEME_STORAGE_KEY) === 'dark';
  } catch (error) {
    console.error('Unable to load the saved Sudoku theme:', error);
  }
  setDarkMode(darkMode);

  document.getElementById('theme-toggle').addEventListener('click', () => {
    darkMode = !document.body.classList.contains('dark-mode');
    setDarkMode(darkMode);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, darkMode ? 'dark' : 'light');
    } catch (error) {
      console.error('Unable to save the Sudoku theme:', error);
    }
  });
}

function readScores() {
  const storedScores = localStorage.getItem(SCORE_STORAGE_KEY);
  if (storedScores === null) return [];

  const scores = JSON.parse(storedScores);
  if (!Array.isArray(scores)) {
    throw new Error('Saved scores are not in the expected format.');
  }
  if (!scores.every(score =>
    score
    && typeof score.name === 'string'
    && score.name.trim()
    && Number.isInteger(score.timeSeconds)
    && score.timeSeconds >= 0
    && Number.isInteger(score.hintsUsed)
    && score.hintsUsed >= 0
    && ['Easy', 'Medium', 'Hard'].includes(score.difficulty)
  )) {
    throw new Error('Saved scores contain invalid entries.');
  }

  return scores;
}

function renderLeaderboard() {
  const scoresElement = document.getElementById('leaderboard-scores');
  const messageElement = document.getElementById('leaderboard-message');
  scoresElement.replaceChildren();

  try {
    const scores = readScores()
      .sort((first, second) =>
        first.timeSeconds - second.timeSeconds
        || first.hintsUsed - second.hintsUsed
      )
      .slice(0, 10);
    if (scores.length === 0) {
      const row = scoresElement.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 5;
      cell.textContent = 'No scores yet.';
      messageElement.textContent = '';
      return;
    }

    scores.forEach((score, index) => {
      const row = scoresElement.insertRow();
      for (const value of [
        index + 1,
        score.name,
        formatTime(score.timeSeconds),
        score.difficulty,
        score.hintsUsed
      ]) {
        row.insertCell().textContent = value;
      }
    });
    messageElement.textContent = '';
  } catch (error) {
    console.error('Unable to load saved Sudoku scores:', error);
    messageElement.textContent = 'Saved scores could not be loaded from this browser.';
  }
}

function saveScore(score) {
  try {
    const scores = readScores();
    scores.push(score);
    scores.sort((first, second) =>
      first.timeSeconds - second.timeSeconds
      || first.hintsUsed - second.hintsUsed
    );
    localStorage.setItem(SCORE_STORAGE_KEY, JSON.stringify(scores.slice(0, 10)));
    renderLeaderboard();
    return true;
  } catch (error) {
    console.error('Unable to save Sudoku score:', error);
    document.getElementById('leaderboard-message').textContent =
      'Your score could not be saved in this browser.';
    return false;
  }
}

function isValidUnit(values) {
  return values.length === SIZE
    && values.every(value =>
      Number.isInteger(value) && value >= 1 && value <= SIZE
    )
    && new Set(values).size === SIZE;
}

function isValidCompletedBoard(board) {
  const rows = board;
  const columns = Array.from({length: SIZE}, (_, col) =>
    board.map(row => row[col])
  );
  const boxes = [];
  for (let boxRow = 0; boxRow < SIZE; boxRow += 3) {
    for (let boxCol = 0; boxCol < SIZE; boxCol += 3) {
      const box = [];
      for (let row = boxRow; row < boxRow + 3; row++) {
        for (let col = boxCol; col < boxCol + 3; col++) {
          box.push(board[row][col]);
        }
      }
      boxes.push(box);
    }
  }

  return [...rows, ...columns, ...boxes].every(isValidUnit);
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

async function newGame() {
  checkRequestId += 1;
  const clues = document.getElementById('difficulty').value;
  const res = await fetch(`/new?clues=${clues}`);
  const data = await res.json();
  renderPuzzle(data.puzzle);
  document.getElementById('message').innerText = '';
  hintsUsed = 0;
  document.getElementById('hints-used').innerText = 'Hints used: 0';
  gameCompleted = false;
  startTimer();
}

async function getHint() {
  if (gameCompleted) return;

  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = Array.from({length: SIZE}, (_, row) =>
    Array.from({length: SIZE}, (_, col) =>
      Number(inputs[row * SIZE + col].value) || 0
    )
  );
  const button = document.getElementById('get-hint');
  const msg = document.getElementById('message');
  button.disabled = true;

  try {
    const response = await fetch('/hint', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({board})
    });
    const data = await response.json();
    if (!response.ok) {
      msg.style.color = '#d32f2f';
      msg.innerText = data.error || 'Unable to get a hint.';
      return;
    }

    const input = inputs[data.row * SIZE + data.col];
    input.value = data.value;
    input.disabled = true;
    input.classList.add('hinted');
    hintsUsed += 1;
    document.getElementById('hints-used').innerText = `Hints used: ${hintsUsed}`;
    msg.style.color = '#388e3c';
    msg.innerText = 'A correct value has been revealed and marked with a color.';
  } catch (error) {
    console.error('Unable to request a Sudoku hint:', error);
    msg.style.color = '#d32f2f';
    msg.innerText = 'Unable to get a hint. Please try again.';
  } finally {
    button.disabled = false;
  }
}

async function checkSolution(easyFillCell = null) {
  if (gameCompleted) return;

  const requestId = ++checkRequestId;
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = Array.from({length: SIZE}, (_, row) =>
    Array.from({length: SIZE}, (_, col) =>
      Number(inputs[row * SIZE + col].value) || 0
    )
  );
  const msg = document.getElementById('message');

  try {
    const requestBody = {board};
    if (easyFillCell !== null) requestBody.easy_fill = easyFillCell;

    const response = await fetch('/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(requestBody)
    });
    const data = await response.json();
    if (requestId !== checkRequestId) return;
    if (!response.ok || data.error) {
      msg.style.color = '#d32f2f';
      msg.innerText = data.error || 'Unable to check the solution.';
      return;
    }

    const incorrect = new Set(
      data.incorrect
        .filter(([row, col]) => board[row][col] !== 0)
        .map(([row, col]) => row * SIZE + col)
    );
    for (let index = 0; index < inputs.length; index++) {
      inputs[index].classList.toggle(
        'incorrect',
        board[Math.floor(index / SIZE)][index % SIZE] !== 0 && incorrect.has(index)
      );
    }

    for (const fill of data.fills || []) {
      const index = fill.row * SIZE + fill.col;
      board[fill.row][fill.col] = fill.value;
      inputs[index].value = fill.value;
      inputs[index].disabled = true;
      inputs[index].classList.add('auto-filled');
    }

    const hasEmptyCells = board.some(row => row.includes(0));
    if (incorrect.size > 0) {
      msg.style.color = '#d32f2f';
      msg.innerText = hasEmptyCells
        ? 'Incorrect values are highlighted. Complete the remaining cells when ready.'
        : 'Some values are incorrect and highlighted.';
      return;
    }
    if (hasEmptyCells) {
      msg.style.color = '#388e3c';
      msg.innerText = 'All entered values are correct so far.';
      return;
    }
    if (!isValidCompletedBoard(board)) {
      msg.style.color = '#d32f2f';
      msg.innerText = 'The completed board is not a valid Sudoku solution.';
      return;
    }

    const elapsedSeconds = stopTimer();
    gameCompleted = true;
    const name = window.prompt('Puzzle solved! Enter your name for the Top 10 fastest times:');
    msg.style.color = '#388e3c';
    if (name && name.trim()) {
      const scoreSaved = saveScore({
        name: name.trim(),
        timeSeconds: elapsedSeconds,
        hintsUsed,
        difficulty: document.getElementById('difficulty').selectedOptions[0].text
      });
      msg.innerText = scoreSaved
        ? `Congratulations! You solved it in ${formatTime(elapsedSeconds)}!`
        : `You solved it in ${formatTime(elapsedSeconds)}, but your score could not be saved.`;
    } else {
      msg.innerText = `You solved it in ${formatTime(elapsedSeconds)}. Your score was not saved.`;
    }
  } catch (error) {
    if (requestId !== checkRequestId) return;
    console.error('Unable to check the Sudoku solution:', error);
    msg.style.color = '#d32f2f';
    msg.innerText = 'Unable to check the solution. Please try again.';
  }
}

// Wire buttons
window.addEventListener('load', () => {
  initializeTheme();
  document.getElementById('sudoku-board').addEventListener('input', (event) => {
    if (!event.target.matches('.sudoku-cell') || event.target.disabled) return;

    event.target.value = event.target.value.replace(/[^1-9]/g, '');
    event.target.classList.remove('incorrect');
    if (event.target.value !== '') {
      checkSolution({
        row: Number(event.target.dataset.row),
        col: Number(event.target.dataset.col)
      });
    } else {
      checkSolution();
    }
  });
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('get-hint').addEventListener('click', getHint);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  renderLeaderboard();
  // initialize
  newGame();
});