"""
Finger mapping system for QWERTY layout
Maps keys to fingers and calculates ergonomic scores
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Finger(Enum):
    """Enum for finger identification"""
    LEFT_PINKY = "left_pinky"
    LEFT_RING = "left_ring"
    LEFT_MIDDLE = "left_middle"
    LEFT_INDEX = "left_index"
    LEFT_THUMB = "left_thumb"
    RIGHT_THUMB = "right_thumb"
    RIGHT_INDEX = "right_index"
    RIGHT_MIDDLE = "right_middle"
    RIGHT_RING = "right_ring"
    RIGHT_PINKY = "right_pinky"


class Hand(Enum):
    """Enum for hand identification"""
    LEFT = "left"
    RIGHT = "right"


@dataclass
class KeyPosition:
    """Represents the physical position of a key"""
    row: int  # 0=number row, 1=top, 2=home, 3=bottom
    col: int  # Column position
    hand: Hand
    finger: Finger
    reach_difficulty: float  # 0.0=home row, 1.0=hardest reach


class FingerMap:
    """Maps keyboard keys to fingers and calculates ergonomic metrics"""

    # QWERTY layout finger mapping
    FINGER_MAP: Dict[str, Finger] = {
        # Left hand
        'q': Finger.LEFT_PINKY, 'a': Finger.LEFT_PINKY, 'z': Finger.LEFT_PINKY,
        '1': Finger.LEFT_PINKY, '`': Finger.LEFT_PINKY, '~': Finger.LEFT_PINKY,
        'tab': Finger.LEFT_PINKY, 'caps lock': Finger.LEFT_PINKY,
        'shift': Finger.LEFT_PINKY, 'ctrl': Finger.LEFT_PINKY,
        'esc': Finger.LEFT_PINKY,

        'w': Finger.LEFT_RING, 's': Finger.LEFT_RING, 'x': Finger.LEFT_RING,
        '2': Finger.LEFT_RING,

        'e': Finger.LEFT_MIDDLE, 'd': Finger.LEFT_MIDDLE, 'c': Finger.LEFT_MIDDLE,
        '3': Finger.LEFT_MIDDLE,

        'r': Finger.LEFT_INDEX, 't': Finger.LEFT_INDEX,
        'f': Finger.LEFT_INDEX, 'g': Finger.LEFT_INDEX,
        'v': Finger.LEFT_INDEX, 'b': Finger.LEFT_INDEX,
        '4': Finger.LEFT_INDEX, '5': Finger.LEFT_INDEX,

        # Right hand
        'y': Finger.RIGHT_INDEX, 'u': Finger.RIGHT_INDEX,
        'h': Finger.RIGHT_INDEX, 'j': Finger.RIGHT_INDEX,
        'n': Finger.RIGHT_INDEX, 'm': Finger.RIGHT_INDEX,
        '6': Finger.RIGHT_INDEX, '7': Finger.RIGHT_INDEX,

        'i': Finger.RIGHT_MIDDLE, 'k': Finger.RIGHT_MIDDLE,
        ',': Finger.RIGHT_MIDDLE, '8': Finger.RIGHT_MIDDLE,

        'o': Finger.RIGHT_RING, 'l': Finger.RIGHT_RING,
        '.': Finger.RIGHT_RING, '9': Finger.RIGHT_RING,

        'p': Finger.RIGHT_PINKY, ';': Finger.RIGHT_PINKY,
        ':': Finger.RIGHT_PINKY, '/': Finger.RIGHT_PINKY,
        '?': Finger.RIGHT_PINKY, "'": Finger.RIGHT_PINKY,
        '"': Finger.RIGHT_PINKY, '[': Finger.RIGHT_PINKY,
        ']': Finger.RIGHT_PINKY, '{': Finger.RIGHT_PINKY,
        '}': Finger.RIGHT_PINKY, '\\': Finger.RIGHT_PINKY,
        '|': Finger.RIGHT_PINKY, '0': Finger.RIGHT_PINKY,
        '-': Finger.RIGHT_PINKY, '_': Finger.RIGHT_PINKY,
        '=': Finger.RIGHT_PINKY, '+': Finger.RIGHT_PINKY,
        'backspace': Finger.RIGHT_PINKY, 'enter': Finger.RIGHT_PINKY,

        # Thumbs
        'space': Finger.LEFT_THUMB,  # Default to left, can be either
    }

    # Key positions for reach difficulty calculation
    KEY_POSITIONS: Dict[str, KeyPosition] = {}

    @classmethod
    def initialize_positions(cls):
        """Initialize key position data"""
        # Home row (lowest difficulty)
        home_keys = {
            'a': (2, 0, Hand.LEFT, Finger.LEFT_PINKY, 0.0),
            's': (2, 1, Hand.LEFT, Finger.LEFT_RING, 0.0),
            'd': (2, 2, Hand.LEFT, Finger.LEFT_MIDDLE, 0.0),
            'f': (2, 3, Hand.LEFT, Finger.LEFT_INDEX, 0.0),
            'j': (2, 6, Hand.RIGHT, Finger.RIGHT_INDEX, 0.0),
            'k': (2, 7, Hand.RIGHT, Finger.RIGHT_MIDDLE, 0.0),
            'l': (2, 8, Hand.RIGHT, Finger.RIGHT_RING, 0.0),
            ';': (2, 9, Hand.RIGHT, Finger.RIGHT_PINKY, 0.0),
        }

        # Top row (medium difficulty)
        top_keys = {
            'q': (1, 0, Hand.LEFT, Finger.LEFT_PINKY, 0.5),
            'w': (1, 1, Hand.LEFT, Finger.LEFT_RING, 0.5),
            'e': (1, 2, Hand.LEFT, Finger.LEFT_MIDDLE, 0.5),
            'r': (1, 3, Hand.LEFT, Finger.LEFT_INDEX, 0.5),
            't': (1, 4, Hand.LEFT, Finger.LEFT_INDEX, 0.6),
            'y': (1, 5, Hand.RIGHT, Finger.RIGHT_INDEX, 0.6),
            'u': (1, 6, Hand.RIGHT, Finger.RIGHT_INDEX, 0.5),
            'i': (1, 7, Hand.RIGHT, Finger.RIGHT_MIDDLE, 0.5),
            'o': (1, 8, Hand.RIGHT, Finger.RIGHT_RING, 0.5),
            'p': (1, 9, Hand.RIGHT, Finger.RIGHT_PINKY, 0.5),
        }

        # Bottom row (higher difficulty)
        bottom_keys = {
            'z': (3, 0, Hand.LEFT, Finger.LEFT_PINKY, 0.7),
            'x': (3, 1, Hand.LEFT, Finger.LEFT_RING, 0.7),
            'c': (3, 2, Hand.LEFT, Finger.LEFT_MIDDLE, 0.7),
            'v': (3, 3, Hand.LEFT, Finger.LEFT_INDEX, 0.7),
            'b': (3, 4, Hand.LEFT, Finger.LEFT_INDEX, 0.8),
            'n': (3, 5, Hand.RIGHT, Finger.RIGHT_INDEX, 0.8),
            'm': (3, 6, Hand.RIGHT, Finger.RIGHT_INDEX, 0.7),
            ',': (3, 7, Hand.RIGHT, Finger.RIGHT_MIDDLE, 0.7),
            '.': (3, 8, Hand.RIGHT, Finger.RIGHT_RING, 0.7),
            '/': (3, 9, Hand.RIGHT, Finger.RIGHT_PINKY, 0.7),
        }

        for key, (row, col, hand, finger, difficulty) in {**home_keys, **top_keys, **bottom_keys}.items():
            cls.KEY_POSITIONS[key] = KeyPosition(row, col, hand, finger, difficulty)

    @classmethod
    def get_finger(cls, key: str) -> Optional[Finger]:
        """Get the finger used for a specific key"""
        return cls.FINGER_MAP.get(key.lower())

    @classmethod
    def get_hand(cls, key: str) -> Optional[Hand]:
        """Get the hand used for a specific key"""
        finger = cls.get_finger(key)
        if not finger:
            return None
        return Hand.LEFT if 'LEFT' in finger.value.upper() else Hand.RIGHT

    @classmethod
    def is_same_finger_bigram(cls, key1: str, key2: str) -> bool:
        """Check if two consecutive keys use the same finger"""
        f1 = cls.get_finger(key1)
        f2 = cls.get_finger(key2)
        if not f1 or not f2:
            return False
        return f1 == f2 and key1.lower() != key2.lower()

    @classmethod
    def is_hand_alternation(cls, key1: str, key2: str) -> bool:
        """Check if two consecutive keys alternate hands"""
        h1 = cls.get_hand(key1)
        h2 = cls.get_hand(key2)
        if not h1 or not h2:
            return False
        return h1 != h2

    @classmethod
    def calculate_row_jump(cls, key1: str, key2: str) -> int:
        """Calculate the number of rows jumped between two keys"""
        pos1 = cls.KEY_POSITIONS.get(key1.lower())
        pos2 = cls.KEY_POSITIONS.get(key2.lower())
        if not pos1 or not pos2:
            return 0
        return abs(pos1.row - pos2.row)

    @classmethod
    def get_reach_difficulty(cls, key: str) -> float:
        """Get the reach difficulty for a key (0.0=easy, 1.0=hard)"""
        pos = cls.KEY_POSITIONS.get(key.lower())
        return pos.reach_difficulty if pos else 0.5

    @classmethod
    def calculate_finger_load(cls, key_counts: Dict[str, int]) -> Dict[Finger, float]:
        """
        Calculate the load percentage for each finger
        Returns dict of Finger -> percentage of total keystrokes
        """
        finger_counts = {finger: 0 for finger in Finger}
        total = 0

        for key, count in key_counts.items():
            finger = cls.get_finger(key)
            if finger:
                finger_counts[finger] += count
                total += count

        if total == 0:
            return {finger: 0.0 for finger in Finger}

        return {finger: (count / total) * 100 for finger, count in finger_counts.items()}

    @classmethod
    def calculate_sfb_rate(cls, bigrams: Dict[str, int]) -> float:
        """
        Calculate Same Finger Bigram rate
        Returns percentage of bigrams that use the same finger
        """
        sfb_count = 0
        total_count = 0

        for bigram, count in bigrams.items():
            if len(bigram) >= 2:
                if cls.is_same_finger_bigram(bigram[0], bigram[1]):
                    sfb_count += count
                total_count += count

        return (sfb_count / total_count * 100) if total_count > 0 else 0.0

    @classmethod
    def calculate_hand_alternation_rate(cls, bigrams: Dict[str, int]) -> float:
        """
        Calculate hand alternation rate
        Returns percentage of bigrams that alternate hands
        """
        alternation_count = 0
        total_count = 0

        for bigram, count in bigrams.items():
            if len(bigram) >= 2:
                if cls.is_hand_alternation(bigram[0], bigram[1]):
                    alternation_count += count
                total_count += count

        return (alternation_count / total_count * 100) if total_count > 0 else 0.0


# Initialize positions when module is loaded
FingerMap.initialize_positions()
