"""
Terminal-based Ludo game (Python)
Drop this file into VS Code as `ludo_game.py` and run with:
    python ludo_game.py

Features:
- 2 to 4 players (human or CPU)
- Standard Ludo rules (simplified but accurate): roll a 6 to bring a token out, move tokens around a 52-square outer track, then up a 6-step home column to finish
- Capturing opponent tokens (sends them back to yard) except on safe squares
- Safe squares (8 standard fixed indices + each player's starting square)
- Simple AI for CPU players
- Clear terminal prompts and board/status printing

Notes/limitations:
- This is a terminal (text) version — no GUI
- Rules are implemented to be friendly for casual play; tournament variants may differ

Have fun! — Aditya, enjoy modifying the rules or UI as you like.
"""

import random
import time
from typing import List, Optional

# Constants
OUTER_TRACK = 52      # number of squares around the board
HOME_STRETCH = 6      # number of squares from entry to finish (including finish)
TOKENS_PER_PLAYER = 4
SAFE_SQUARES = {0, 8, 13, 21, 26, 34, 39, 47}  # common safe squares on many Ludo boards

COLORS = ["Red", "Green", "Yellow", "Blue"]

# Map each player index to their start square on the outer track (0..51)
START_SQUARE = {
    0: 0,    # Red
    1: 13,   # Green
    2: 26,   # Yellow
    3: 39    # Blue
}

# Each player's home entry square is the square they must reach to enter their home stretch.
# For player p, the home entry index is (START_SQUARE[p] - 1) % OUTER_TRACK
HOME_ENTRY = {p: (START_SQUARE[p] - 1) % OUTER_TRACK for p in START_SQUARE}


def debug_print(*args, **kwargs):
    # Set to True to see debug traces
    if False:
        print(*args, **kwargs)


class Token:
    def __init__(self, player_idx: int, token_idx: int):
        self.player_idx = player_idx
        self.token_idx = token_idx
        self.position = -1  # -1 = in yard; 0..51 = outer track; 52..(52+HOME_STRETCH-1) = home stretch per-player offset
        self.finished = False

    def is_in_yard(self):
        return self.position == -1

    def is_on_board(self):
        return self.position >= 0 and not self.finished

    def __repr__(self):
        if self.finished:
            return "F"
        if self.position == -1:
            return "Y"
        return str(self.position)


class Player:
    def __init__(self, idx: int, name: str, is_cpu: bool = False):
        self.idx = idx
        self.name = name
        self.color = COLORS[idx]
        self.tokens = [Token(idx, i) for i in range(TOKENS_PER_PLAYER)]
        self.is_cpu = is_cpu

    def tokens_in_play(self):
        return [t for t in self.tokens if not t.is_in_yard() and not t.finished]

    def tokens_in_yard(self):
        return [t for t in self.tokens if t.is_in_yard()]

    def tokens_finished(self):
        return [t for t in self.tokens if t.finished]

    def all_finished(self):
        return len(self.tokens_finished()) == TOKENS_PER_PLAYER

    def __repr__(self):
        return f"{self.name}({self.color})"


class Game:
    def __init__(self, num_players: int = 4, cpu_players: Optional[List[bool]] = None):
        assert 2 <= num_players <= 4, "Ludo needs 2-4 players"
        if cpu_players is None:
            cpu_players = [False] * num_players
        self.num_players = num_players
        self.players = [Player(i, f"Player-{i+1}", is_cpu=cpu_players[i]) for i in range(num_players)]
        self.turn = 0
        self.winner_order: List[Player] = []

    def roll_dice(self) -> int:
        v = random.randint(1, 6)
        debug_print(f"Dice rolled: {v}")
        return v

    def get_absolute_position(self, player_idx: int, token_pos: int) -> int:
        """
        For positions on the outer track, tokens store 0..51 meaning absolute index on board.
        For home stretch we store positions as OUTER_TRACK + steps (0..HOME_STRETCH-1) but they are relative per player.
        negative is yard.
        """
        return token_pos

    def position_is_safe(self, pos: int, player_idx: Optional[int] = None) -> bool:
        # Safe squares are fixed on outer track, and also player's own start square
        if pos < 0 or pos >= OUTER_TRACK:
            return False
        if pos in SAFE_SQUARES:
            return True
        if player_idx is not None and pos == START_SQUARE[player_idx]:
            return True
        return False

    def local_distance_to_home_entry(self, player_idx: int, pos: int) -> int:
        # Given pos on outer track, how many steps to reach home entry of player
        if pos < 0 or pos >= OUTER_TRACK:
            return 0
        entry = HOME_ENTRY[player_idx]
        if pos <= entry:
            return entry - pos
        return OUTER_TRACK - (pos - entry)

    def can_move_token(self, player: Player, token: Token, roll: int) -> bool:
        # If token in yard -> only a 6 can bring it out
        if token.finished:
            return False
        if token.is_in_yard():
            return roll == 6
        # If on outer track
        if 0 <= token.position < OUTER_TRACK:
            steps_to_entry = self.local_distance_to_home_entry(player.idx, token.position)
            if roll <= steps_to_entry:
                return True
            # roll goes beyond entry; ensure it does not overshoot final stretch
            over = roll - steps_to_entry - 1
            return over < HOME_STRETCH
        # If on home stretch
        if token.position >= OUTER_TRACK:
            rel = token.position - OUTER_TRACK
            return rel + roll < HOME_STRETCH
        return False

    def move_token(self, player: Player, token: Token, roll: int):
        debug_print(f"Moving token {token.token_idx} of {player.name} with roll {roll}")
        if token.is_in_yard():
            # Bring out
            token.position = START_SQUARE[player.idx]
            debug_print(f"Token brought out to {token.position}")
            self.handle_capture(player, token)
            return

        if 0 <= token.position < OUTER_TRACK:
            steps_to_entry = self.local_distance_to_home_entry(player.idx, token.position)
            if roll <= steps_to_entry:
                # Move on outer track
                new_pos = (token.position + roll) % OUTER_TRACK
                token.position = new_pos
                debug_print(f"Token moved on track to {new_pos}")
                self.handle_capture(player, token)
                return
            else:
                # Move into home stretch
                over = roll - steps_to_entry - 1
                token.position = OUTER_TRACK + over
                debug_print(f"Token moved into home stretch to {token.position}")
                if token.position - OUTER_TRACK == HOME_STRETCH - 1:
                    token.finished = True
                    debug_print(f"Token finished!")
                return

        # If token is in home stretch
        if token.position >= OUTER_TRACK:
            rel = token.position - OUTER_TRACK
            new_rel = rel + roll
            if new_rel == HOME_STRETCH - 1:
                token.position = OUTER_TRACK + new_rel
                token.finished = True
                debug_print("Token reached finish")
            elif new_rel < HOME_STRETCH - 1:
                token.position = OUTER_TRACK + new_rel
                debug_print(f"Token moved in home stretch to {token.position}")
            else:
                # overshoot: not allowed in many Ludo variants; here we disallow the move
                debug_print("Move overshoots finish: not allowed")

    def handle_capture(self, player: Player, moved_token: Token):
        # If token lands on an opponent on outer track and not a safe square, capture them
        pos = moved_token.position
        if pos < 0 or pos >= OUTER_TRACK:
            return
        if self.position_is_safe(pos, player.idx):
            debug_print("Landed on safe square; no capture")
            return
        for pl in self.players:
            if pl.idx == player.idx:
                continue
            for tok in pl.tokens:
                if tok.is_on_board() and tok.position == pos:
                    # capture
                    tok.position = -1
                    debug_print(f"Captured token of {pl.name} at {pos}")

    def any_moves_available(self, player: Player, roll: int) -> bool:
        for tok in player.tokens:
            if self.can_move_token(player, tok, roll):
                return True
        return False

    def select_token_for_move(self, player: Player, roll: int) -> Optional[Token]:
        movable = [t for t in player.tokens if self.can_move_token(player, t, roll)]
        if not movable:
            return None
        if player.is_cpu:
            # Simple CPU heuristics: prefer finishing moves, then captures, then bring out, then move furthest token
            # 1) finishing
            for t in movable:
                if t.position >= OUTER_TRACK and (t.position - OUTER_TRACK) + roll == HOME_STRETCH - 1:
                    return t
            # 2) move that captures
            for t in movable:
                if t.is_in_yard():
                    dest = START_SQUARE[player.idx]
                elif 0 <= t.position < OUTER_TRACK:
                    steps_to_entry = self.local_distance_to_home_entry(player.idx, t.position)
                    if roll <= steps_to_entry:
                        dest = (t.position + roll) % OUTER_TRACK
                    else:
                        dest = OUTER_TRACK + (roll - steps_to_entry - 1)
                else:
                    dest = t.position + roll
                if dest < OUTER_TRACK and not self.position_is_safe(dest, player.idx):
                    for pl in self.players:
                        if pl.idx == player.idx:
                            continue
                        for tok in pl.tokens:
                            if tok.is_on_board() and tok.position == dest:
                                return t
            # 3) bring out
            for t in movable:
                if t.is_in_yard():
                    return t
            # 4) move the token with highest board position (progress)
            movable.sort(key=lambda x: (x.position if x.position >= 0 else -1), reverse=True)
            return movable[0]
        else:
            # human: prompt
            print(f"Choose token to move for {player.name} (roll={roll}):")
            for t in player.tokens:
                idx = t.token_idx
                status = "Yard" if t.is_in_yard() else ("Finished" if t.finished else f"Pos:{t.position}")
                allowed = self.can_move_token(player, t, roll)
                print(f"  [{idx}] {status} {'(can move)' if allowed else ''}")
            while True:
                choice = input("Enter token index to move (or 'p' to pass): ")
                if choice.strip().lower() == 'p':
                    return None
                if not choice.isdigit():
                    print("Invalid input. Type a number.")
                    continue
                ci = int(choice)
                if ci < 0 or ci >= TOKENS_PER_PLAYER:
                    print("Invalid index.")
                    continue
                tok = player.tokens[ci]
                if not self.can_move_token(player, tok, roll):
                    print("That token cannot be moved with this roll.")
                    continue
                return tok

    def print_board_state(self):
        print("\n===== BOARD STATE =====")
        for p in self.players:
            tokens = []
            for t in p.tokens:
                if t.finished:
                    s = 'F'
                elif t.position == -1:
                    s = 'Y'
                elif t.position < OUTER_TRACK:
                    s = str(t.position)
                else:
                    s = f"H{t.position - OUTER_TRACK}"
                tokens.append(s)
            print(f"{p.name} ({p.color}): " + ", ".join(tokens) + f"  | Finished: {len(p.tokens_finished())}")
        print("=======================\n")

    def play(self):
        print("Welcome to Terminal Ludo!")
        print("Rules: Roll a 6 to bring a token out. Capture by landing on opponent's token (not on safe squares). Finish when all your tokens reach home.)\n")
        while len(self.winner_order) < self.num_players - 1:
            player = self.players[self.turn]
            if player.all_finished():
                if player not in self.winner_order:
                    self.winner_order.append(player)
                self.turn = (self.turn + 1) % self.num_players
                continue

            print(f"-- {player.name} ({player.color})'s turn --")
            self.print_board_state()

            extra_turn = False
            roll = self.roll_dice()
            print(f"{player.name} rolled a {roll}")

            if not self.any_moves_available(player, roll):
                print("No moves available.")
                if roll == 6:
                    print("But you rolled a 6, you get another turn.")
                    extra_turn = True
                else:
                    extra_turn = False
            else:
                tok = self.select_token_for_move(player, roll)
                if tok is None:
                    print("Player chose not to move any token.")
                else:
                    # move chosen token
                    self.move_token(player, tok, roll)
                    # check if finished player
                    if player.all_finished() and player not in self.winner_order:
                        print(f"{player.name} has finished all tokens!" )
                        self.winner_order.append(player)
                    # If rolled a 6, player gets another turn
                    if roll == 6:
                        print("Rolled a 6: extra turn granted.")
                        extra_turn = True

            if not extra_turn:
                self.turn = (self.turn + 1) % self.num_players

        # Append remaining player as last
        for p in self.players:
            if p not in self.winner_order:
                self.winner_order.append(p)
        print("\n=== GAME OVER ===")
        print("Final standings:")
        for i, p in enumerate(self.winner_order, 1):
            print(f" {i}. {p.name} ({p.color})")


def prompt_setup():
    print("Set up the Ludo game")
    while True:
        n = input("Enter number of players (2-4) [default 4]: ")
        if n.strip() == "":
            n = 4
            break
        if not n.isdigit():
            print("Enter a number 2-4.")
            continue
        n = int(n)
        if 2 <= n <= 4:
            break
        print("Enter 2, 3 or 4")

    num_players = int(n)
    cpu_players = []
    for i in range(num_players):
        while True:
            t = input(f"Is Player-{i+1} a CPU? (y/n) [n]: ")
            if t.strip() == "":
                cpu_players.append(False)
                break
            if t.lower() in ('y', 'yes'):
                cpu_players.append(True)
                break
            if t.lower() in ('n', 'no'):
                cpu_players.append(False)
                break
            print("Enter y or n")
    return num_players, cpu_players


if __name__ == '__main__':
    random.seed()
    num_players, cpu_players = prompt_setup()

    # Create players list for Game
    game = Game(num_players=num_players, cpu_players=cpu_players)

    # Optionally rename human players
    for p in game.players:
        if not p.is_cpu:
            name = input(f"Enter name for {p.name} (or press Enter to keep): ")
            if name.strip():
                p.name = name.strip()

    print("Starting game...\n")
    time.sleep(0.7)
    game.play()
