"""Game rules and state. No UI in here, so it is easy to unit-test."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

MOVES = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

WIN, LOSE, TIE = "win", "lose", "tie"


def resolve(player: str, computer: str) -> str:
    if player == computer:
        return TIE
    return WIN if BEATS[player] == computer else LOSE


@dataclass
class GameState:
    rounds: int = 5
    round_no: int = 0
    player_score: int = 0
    computer_score: int = 0
    player_choice: str | None = None
    computer_choice: str | None = None
    history: list = field(default_factory=list)

    # -- lifecycle
    def reset(self, rounds: int | None = None):
        if rounds is not None:
            self.rounds = rounds
        self.round_no = 0
        self.player_score = 0
        self.computer_score = 0
        self.player_choice = None
        self.computer_choice = None
        self.history.clear()

    def start_round(self):
        self.round_no += 1
        self.player_choice = None
        self.computer_choice = None

    # -- play
    def play(self, player_choice: str) -> str:
        if player_choice not in MOVES:
            raise ValueError(f"unknown move: {player_choice!r}")
        self.player_choice = player_choice
        self.computer_choice = random.choice(MOVES)
        outcome = resolve(self.player_choice, self.computer_choice)
        if outcome == WIN:
            self.player_score += 1
        elif outcome == LOSE:
            self.computer_score += 1
        self.history.append((self.round_no, player_choice, self.computer_choice, outcome))
        return outcome

    # -- queries
    @property
    def finished(self) -> bool:
        return self.round_no >= self.rounds

    @property
    def player_won(self) -> bool:
        return self.player_score > self.computer_score

    @property
    def drawn(self) -> bool:
        return self.player_score == self.computer_score
