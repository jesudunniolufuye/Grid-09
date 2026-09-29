#!/usr/bin/env python3

import random
import select
import time

COLOR = {
    "red":    "\033[31m",
    "yellow": "\033[33m",
    "green":  "\033[32m",
    "blue":   "\033[34m",
    "bold":   "\033[1m",
    "off":    "\033[0m",
}

FUSE_WIDTH = 24   # characters in the bar, not counting the brackets
FUSE_TICK = 0.1   # seconds between redraws of the fuse bar

# ANSI cursor moves, used only by timed_input() to redraw the fuse line
# without disturbing whatever the player has already typed below it.
CURSOR_SAVE = "\033[s"
CURSOR_RESTORE = "\033[u"
CURSOR_UP = "\033[1A"
CLEAR_LINE = "\033[2K"

board = ["1", "2", "3",
         "4", "5", "6",
         "7", "8", "9"]


def colored_cell(value, highlight=False):
    """Return the cell's text. Played cells (X or O) get a colour; `highlight`
    also bolds them -- used to mark the winning line."""
    if value not in ("X", "O"):
        return value
    color = COLOR["red"] if value == "X" else COLOR["blue"]
    if highlight:
        color += COLOR["bold"]
    return f"{color}{value}{COLOR['off']}"


def display_board(line=None):
    """Print the running score, then the grid. `line` is an optional triple
    of indexes (the winning line) shown in bold."""
    line = line or ()
    cells = [colored_cell(board[i], highlight=(i in line)) for i in range(9)]

    print()
    print(f"[ {player1}: {player1_score} ]  [ {player2}: {player2_score} ]")
    print("┌─────┬─────┬─────┐")
    print(f"│  {cells[0]}  │  {cells[1]}  │  {cells[2]}  │")
    print("├─────┼─────┼─────┤")
    print(f"│  {cells[3]}  │  {cells[4]}  │  {cells[5]}  │")
    print("├─────┼─────┼─────┤")
    print(f"│  {cells[6]}  │  {cells[7]}  │  {cells[8]}  │")
    print("└─────┴─────┴─────┘")
    print()


def winning_line(symbol):
    """The three indexes that give `symbol` a line, or None if it has none."""
    winning_combinations = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]

    for combination in winning_combinations:
        if all(board[i] == symbol for i in combination):
            return combination

    return None


def check_winner(symbol):
    """True if `symbol` ("X" or "O") fills any row, column or diagonal."""
    return winning_line(symbol) is not None


def reset_board():
    global board
    board = ["1", "2", "3",
             "4", "5", "6",
             "7", "8", "9"]


def choose_difficulty():
    print()
    print("╔══════════════════════════════════╗")
    print("║       SELECT DIFFICULTY          ║")
    print("╠══════════════════════════════════╣")
    print("║  1. EASY      - 15 SECONDS       ║")
    print("║  2. MEDIUM    - 10 SECONDS       ║")
    print("║  3. HARD      -  5 SECONDS       ║")
    print("╚══════════════════════════════════╝")
    print()

    while True:
        choice = input("SELECT LEVEL (1-3): ")

        if choice == "1":
            print()
            print("        EASY SELECTED")
            print("        TIME LIMIT: 15 SEC")
            print()
            return "EASY", 15

        elif choice == "2":
            print()
            print("        MEDIUM SELECTED")
            print("        TIME LIMIT: 10 SEC")
            print()
            return "MEDIUM", 10

        elif choice == "3":
            print()
            print("        HARD SELECTED")
            print("        TIME LIMIT: 5 SEC")
            print()
            return "HARD", 5
        else:
            print("INVALID SELECTION. CHOOSE 1, 2, OR 3.")


def start_round():
    reset_board()

    starting_player = random.choice([player1, player2])

    if starting_player == player1:
        player1_symbol = "X"
        player2_symbol = "O"
    else:
        player1_symbol = "O"
        player2_symbol = "X"

    return starting_player, player1_symbol, player2_symbol


def fuse_bar(remaining, total, width=FUSE_WIDTH):
    """One line of fuse-bar text for `remaining` seconds out of `total`.
    A block-character bar empties left to right as time runs out, with a
    bright spark at the burning tip, and colour shifts green -> yellow ->
    red as the fuse gets short. Pure text, so it fits on one terminal line
    and is easy to reason about: filled length is just a percentage."""
    remaining = max(0.0, remaining)
    fraction = remaining / total if total else 0.0
    filled = round(fraction * width)
    filled = max(0, min(width, filled))

    if filled == 0:
        bar = "\u2591" * width
    else:
        bar = "\u2588" * (filled - 1) + "\u25CF" + "\u2591" * (width - filled)

    if remaining <= total * 0.25:
        color = COLOR["red"]
    elif remaining <= total * 0.5:
        color = COLOR["yellow"]
    else:
        color = COLOR["green"]

    return f"{color}FUSE [{bar}] {remaining:4.1f}s{COLOR['off']}"


def timed_input(prompt, time_remaining, total_time):
    """Prompt for a line of input while a fuse bar burns down above the
    prompt. The bar redraws in place every FUSE_TICK seconds.
    Returns the typed line (or None) and the elapsed time."""
    start = time.monotonic()

    print()  # reserved line: the fuse bar lives here
    print(prompt, end="", flush=True)

    while True:
        elapsed = time.monotonic() - start
        remaining = time_remaining - elapsed

        if remaining <= 0:
            print(
                f"{CURSOR_SAVE}{CURSOR_UP}\r{CLEAR_LINE}"
                f"{fuse_bar(0, total_time)}{CURSOR_RESTORE}",
                end="", flush=True,
            )
            print()
            print("TIME'S UP!")
            return None, elapsed

        print(
            f"{CURSOR_SAVE}{CURSOR_UP}\r{CLEAR_LINE}"
            f"{fuse_bar(remaining, total_time)}{CURSOR_RESTORE}",
            end="", flush=True,
        )

        ready, _, _ = select.select([0], [], [], FUSE_TICK)
        if ready:
            return input(), elapsed


def play_timeout(name):
    """Fuse hit zero: one ASCII-art print, no loop, no screen clear (the
    board stays visible so the player can see how it ended)."""
    print(f"""{COLOR['red']}{COLOR['bold']}
      *   BOOM!   *
   -- FUSE HIT ZERO --
      *          *{COLOR['off']}
""")
    print(f"{name}'s BOMB WENT OFF.")


def play_win(name):
    """Bomb defused: one ASCII-art print, no loop, no screen clear."""
    print(f"""{COLOR['green']}{COLOR['bold']}
   \u2726  SYSTEM SECURED -- BOMB DEFUSED  \u2726{COLOR['off']}
""")
    print(f"{COLOR['yellow']}{COLOR['bold']}{name} WINS!{COLOR['off']}")


def play_draw():
    """Board full, nobody defused it in time: one line, no screen clear."""
    print(f"""{COLOR['yellow']}{COLOR['bold']}
   STALEMATE -- BOARD FULL, BOTH WIRES STILL LIVE{COLOR['off']}
""")
    print("DRAW!")


def play_round(starting_player, player1_symbol, player2_symbol, time_limit):
    global player1_score, player2_score
    fuses = {player1: float(time_limit), player2: float(time_limit)}
    current_player = starting_player

    while True:
        print()
        print("════════════════════════════════════")
        print("             GRID//09")
        print("════════════════════════════════════")

        display_board()
        print(f"CURRENT TURN: {current_player}")

        move, time_used = timed_input(
            f"{current_player}, choose a space (1-9) or type 'STOP': ",
            fuses[current_player],
            time_limit
        )
        
        fuses[current_player] -= time_used
        
        if move is None:
            if current_player == player1:
                winner = player2
                player2_score += 1
            else:
                winner = player1
                player1_score += 1
                
            print()
            print("-----------------------")
            print("       TIME's UP!")
            print("-----------------------")
            display_board()
            play_timeout(current_player)
            return winner
            
        if move.upper() == "STOP":
            print("GAME TERMINATED.")
            return "STOP"
            
        try:
            position = int(move) - 1
        except ValueError:
            print("INVALID MOVE. ENTER A NUMBER FROM 1-9.")
            continue
            
        if position < 0 or position > 8:
            print("INVALID MOVE. ENTER A NUMBER FROM 1-9.")
            continue
            
        if board[position] in ("X", "O"):
            print("SPACE ALREADY OCCUPIED!")
            continue

        if current_player == player1:
            board[position] = player1_symbol
            symbol = player1_symbol
        else:
            board[position] = player2_symbol
            symbol = player2_symbol

        line = winning_line(symbol)
        if line:
            display_board(line)
            play_win(current_player)

            if current_player == player1:
                player1_score += 1
            else:
                player2_score += 1

            return current_player

        if all(space in ("X", "O") for space in board):
            display_board()
            play_draw()
            return "DRAW"

        if current_player == player1:
            current_player = player2
        else:
            current_player = player1


def show_intro():
    """Boot-sequence intro: clear the screen, print the title once, pause
    a beat, then wait for Enter. One print, one sleep -- no per-line delays."""
    print("\033[2J\033[H", end="")
    print(f"""{COLOR['bold']}{COLOR['yellow']}
  ╔══════════════════════════════════════╗
  ║        TIC TAC TOE: BOMB DEFUSAL       ║
  ╚══════════════════════════════════════╝
{COLOR['off']}
  GRID//09 ONLINE -- SYSTEM INITIALIZED
""")
    time.sleep(0.5)
    input("  ARE YOU READY? PRESS ENTER TO BEGIN...")


show_intro()

player1 = input("PLAYER 01 - ENTER CODENAME: ")
player2 = input("PLAYER 02 - ENTER CODENAME: ")

difficulty, time_limit = choose_difficulty()

player1_score = 0
player2_score = 0
round_number = 1

while True:
    print()
    print(f"ROUND {round_number}  ·  DIFFICULTY: {difficulty}")

    starting_player, player1_symbol, player2_symbol = start_round()

    print()
    print(f"{player1}: {player1_symbol}")
    print(f"{player2}: {player2_symbol}")
    print(f"{starting_player} GOES FIRST!")

    result = play_round(starting_player, player1_symbol, player2_symbol, time_limit)

    if result == "STOP":
        break

    print()
    print(f"SCORE: {player1} {player1_score} - {player2} {player2_score}")

    while True:
        again = input("PLAY ANOTHER ROUND? (Y/N): ").strip().upper()
        if again in ("Y", "N"):
            break
        print("PLEASE ENTER Y OR N.")

    if again == "N":
        print("GAME ENDED.")
        break

    round_number += 1
