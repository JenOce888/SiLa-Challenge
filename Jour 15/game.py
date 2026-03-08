"""
game.py — Core game logic
Word bank (local fallback) + dictionaryapi.dev fetching + state machine.
"""

import random
import time
import urllib.request
import urllib.error
import json
import threading

# Local word bank (fallback when API is unavailable) 

WORD_BANK: dict[str, dict[str, list[str]]] = {
    "programming": {
        "easy":   ["loop", "class", "array", "object", "method", "module", "variable"],
        "medium": ["recursion", "polymorphism", "abstraction", "compilation", "callback"],
        "hard":   ["asynchronous", "microservices", "refactoring", "virtualization", "containerization"],
    },
    "animals": {
        "easy":   ["cat", "dog", "rabbit", "tiger", "horse", "shark", "eagle"],
        "medium": ["crocodile", "platypus", "chameleon", "wolverine", "axolotl"],
        "hard":   ["archaeopteryx", "bioluminescence", "cephalopod", "ichthyosaur"],
    },
    "geography": {
        "easy":   ["france", "ocean", "desert", "mountain", "island", "river"],
        "medium": ["himalayas", "amazonia", "sahara", "patagonia", "melanesia"],
        "hard":   ["mesopotamia", "transcaucasia", "micronesia", "laurasia"],
    },
    "science": {
        "easy":   ["atom", "cell", "energy", "gravity", "light", "magnet"],
        "medium": ["chromosome", "photosynthesis", "electromagnetism", "supernova"],
        "hard":   ["bioluminescence", "thermodynamics", "superconductivity", "nanotechnology"],
    },
}

CATEGORIES = list(WORD_BANK.keys())
DIFFICULTIES = ["easy", "medium", "hard"]

# Dictionary API 
_DICT_API = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
_definition_cache: dict[str, str] = {}


def fetch_definition(word: str) -> str | None:
    """
    Fetch the first definition of *word* from dictionaryapi.dev.
    Returns None on network failure. Cached after first successful call.
    """
    word = word.lower()
    if word in _definition_cache:
        return _definition_cache[word]

    url = _DICT_API.format(word=word)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HangmanELO/2.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read())
            definition = (
                data[0]["meanings"][0]["definitions"][0]["definition"]
            )
            _definition_cache[word] = definition
            return definition
    except Exception:
        return None


def fetch_definition_async(word: str, callback) -> None:
    """Fetch definition in a background thread; call callback(definition|None)."""
    def _run():
        callback(fetch_definition(word))
    threading.Thread(target=_run, daemon=True).start()


#  Game state

MAX_ERRORS = 10


class GameState:
    """Immutable-ish game state. Call .guess() to progress."""

    def __init__(self, word: str, category: str, difficulty: str):
        self.word        = word.upper()
        self.category    = category
        self.difficulty  = difficulty
        self.guessed     : set[str] = set()
        self.errors      : int = 0
        self.hint_used   : bool = False
        self.start_time  : float = time.time()
        self.end_time    : float | None = None
        self.definition  : str | None = None   # filled async

    #  Mutators 

    def guess(self, letter: str) -> bool:
        """Register a guess. Returns True if letter is in the word."""
        letter = letter.upper()
        if letter in self.guessed or self.is_over:
            return False
        self.guessed.add(letter)
        hit = letter in self.word
        if not hit:
            self.errors += 1
        if self.is_over:
            self.end_time = time.time()
        return hit

    def use_hint(self) -> str | None:
        """
        Mark hint as used. Returns a letter to reveal (random hidden letter),
        or None if definition hint was shown instead.
        """
        if self.hint_used:
            return None
        self.hint_used = True

        if self.definition:
            return None  # UI will display the definition

        hidden = [c for c in self.word if c not in self.guessed and c.isalpha()]
        if not hidden:
            return None
        reveal = random.choice(hidden)
        self.guessed.add(reveal)
        return reveal

    # Read-only properties 

    @property
    def display(self) -> str:
        """Word with unguessed letters replaced by underscores."""
        return " ".join(c if c in self.guessed else "_" for c in self.word)

    @property
    def won(self) -> bool:
        return all(c in self.guessed for c in self.word if c.isalpha())

    @property
    def lost(self) -> bool:
        return self.errors >= MAX_ERRORS

    @property
    def is_over(self) -> bool:
        return self.won or self.lost

    @property
    def duration(self) -> int:
        end = self.end_time or time.time()
        return int(end - self.start_time)

    @property
    def wrong_letters(self) -> list[str]:
        return sorted(c for c in self.guessed if c not in self.word)


#  Factory 

def new_game(category: str, difficulty: str) -> GameState:
    words = WORD_BANK.get(category, {}).get(difficulty, ["python"])
    word = random.choice(words)
    state = GameState(word, category, difficulty)
    fetch_definition_async(word, lambda d: setattr(state, "definition", d))
    return state
