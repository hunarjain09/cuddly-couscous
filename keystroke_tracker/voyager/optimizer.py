"""
Symbol optimizer for Voyager layout
Uses frequency analysis to optimize key placement
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter
import json

from keystroke_tracker.utils.finger_map import FingerMap, Finger
from keystroke_tracker.utils.patterns import PythonAnalyzer


@dataclass
class KeyAssignment:
    """Represents an optimized key assignment"""
    key: str
    position: Tuple[int, int]
    layer: int
    finger: str
    reach_difficulty: float
    frequency: int
    score: float
    reason: str


class PositionScore:
    """Scoring system for key positions"""

    # Position quality scores (0-100, higher is better)
    POSITION_SCORES = {
        'home_row': 100,
        'home_index': 95,
        'top_row': 80,
        'bottom_row': 70,
        'number_row': 60,
        'pinky_edge': 40,
        'thumb_primary': 90,
        'thumb_secondary': 75,
    }

    # Finger strength multipliers
    FINGER_STRENGTH = {
        Finger.LEFT_INDEX: 1.0,
        Finger.RIGHT_INDEX: 1.0,
        Finger.LEFT_MIDDLE: 0.9,
        Finger.RIGHT_MIDDLE: 0.9,
        Finger.LEFT_RING: 0.7,
        Finger.RIGHT_RING: 0.7,
        Finger.LEFT_PINKY: 0.5,
        Finger.RIGHT_PINKY: 0.5,
        Finger.LEFT_THUMB: 1.1,
        Finger.RIGHT_THUMB: 1.1,
    }

    @classmethod
    def calculate_position_score(cls, row: int, col: int, finger: Finger) -> float:
        """
        Calculate quality score for a position

        Args:
            row: Row number (0=number, 1=top, 2=home, 3=bottom)
            col: Column number
            finger: Finger that presses this position

        Returns:
            Score from 0-100
        """
        # Base score from row
        row_scores = {
            0: cls.POSITION_SCORES['number_row'],
            1: cls.POSITION_SCORES['top_row'],
            2: cls.POSITION_SCORES['home_row'],
            3: cls.POSITION_SCORES['bottom_row'],
        }
        score = row_scores.get(row, 50)

        # Apply finger strength multiplier
        finger_mult = cls.FINGER_STRENGTH.get(finger, 0.7)
        score *= finger_mult

        # Penalize extreme columns (pinky edge)
        if col == 0 or col == 5:
            score *= 0.7

        return min(100, score)


class SymbolOptimizer:
    """
    Optimizes symbol placement on Voyager layout
    Based on frequency, finger strength, and pair relationships
    """

    def __init__(self, keystroke_data: Dict, context: str = 'python'):
        """
        Initialize optimizer

        Args:
            keystroke_data: Keystroke tracking data
            context: Programming context ('python', 'javascript', etc.)
        """
        self.data = keystroke_data
        self.context = context

        # Symbol categories from Python analyzer
        self.symbol_priority = PythonAnalyzer.SYMBOL_PRIORITY

        # Available positions on Voyager
        self.positions = self._define_positions()

        # Symbol pairs that should be together
        self.symbol_pairs = [
            ('(', ')'),
            ('[', ']'),
            ('{', '}'),
            ('<', '>'),
            ('"', '"'),
            ("'", "'"),
        ]

    def _define_positions(self) -> Dict[str, List[Dict]]:
        """Define available positions on Voyager by quality tier"""
        return {
            'prime': [  # Best positions - home row, strong fingers
                {'row': 2, 'col': 1, 'finger': 'left_ring', 'score': 90},
                {'row': 2, 'col': 2, 'finger': 'left_middle', 'score': 95},
                {'row': 2, 'col': 3, 'finger': 'left_index', 'score': 100},
                {'row': 2, 'col': 6, 'finger': 'right_index', 'score': 100},
                {'row': 2, 'col': 7, 'finger': 'right_middle', 'score': 95},
                {'row': 2, 'col': 8, 'finger': 'right_ring', 'score': 90},
            ],
            'good': [  # Good positions - top row, strong fingers
                {'row': 1, 'col': 1, 'finger': 'left_ring', 'score': 80},
                {'row': 1, 'col': 2, 'finger': 'left_middle', 'score': 85},
                {'row': 1, 'col': 3, 'finger': 'left_index', 'score': 90},
                {'row': 1, 'col': 6, 'finger': 'right_index', 'score': 90},
                {'row': 1, 'col': 7, 'finger': 'right_middle', 'score': 85},
                {'row': 1, 'col': 8, 'finger': 'right_ring', 'score': 80},
            ],
            'acceptable': [  # Acceptable - bottom row or weak fingers
                {'row': 3, 'col': 1, 'finger': 'left_ring', 'score': 70},
                {'row': 3, 'col': 2, 'finger': 'left_middle', 'score': 75},
                {'row': 3, 'col': 3, 'finger': 'left_index', 'score': 80},
                {'row': 3, 'col': 6, 'finger': 'right_index', 'score': 80},
                {'row': 3, 'col': 7, 'finger': 'right_middle', 'score': 75},
                {'row': 3, 'col': 8, 'finger': 'right_ring', 'score': 70},
            ],
            'edge': [  # Edge positions - pinky columns
                {'row': 2, 'col': 0, 'finger': 'left_pinky', 'score': 60},
                {'row': 2, 'col': 5, 'finger': 'left_index', 'score': 65},
                {'row': 2, 'col': 9, 'finger': 'right_pinky', 'score': 60},
            ],
            'thumb': [  # Thumb positions - very good for high-frequency
                {'row': 4, 'col': 2, 'finger': 'left_thumb', 'score': 95},
                {'row': 4, 'col': 3, 'finger': 'left_thumb', 'score': 90},
                {'row': 4, 'col': 9, 'finger': 'right_thumb', 'score': 95},
                {'row': 4, 'col': 10, 'finger': 'right_thumb', 'score': 90},
            ]
        }

    def optimize_symbols(self, layer: int = 0) -> List[KeyAssignment]:
        """
        Primary optimization algorithm

        Args:
            layer: Which layer to optimize (0=base)

        Returns:
            List of optimized key assignments
        """
        # Get symbol frequencies
        symbol_freq = self._get_symbol_frequencies()

        # Get symbol pairs and their combined frequencies
        pair_freq = self._analyze_symbol_pairs()

        # Create assignments
        assignments = []
        used_positions = set()

        # Priority 1: Assign symbol pairs to adjacent/mirrored positions
        for (sym1, sym2), combined_freq in pair_freq:
            if combined_freq > 50:  # Threshold for pair placement
                # Find two good adjacent positions
                pos1, pos2 = self._find_paired_positions(used_positions)
                if pos1 and pos2:
                    assignments.append(KeyAssignment(
                        key=sym1,
                        position=(pos1['row'], pos1['col']),
                        layer=layer,
                        finger=pos1['finger'],
                        reach_difficulty=pos1['score'] / 100,
                        frequency=symbol_freq.get(sym1, 0),
                        score=pos1['score'],
                        reason=f"Paired with {sym2}"
                    ))

                    assignments.append(KeyAssignment(
                        key=sym2,
                        position=(pos2['row'], pos2['col']),
                        layer=layer,
                        finger=pos2['finger'],
                        reach_difficulty=pos2['score'] / 100,
                        frequency=symbol_freq.get(sym2, 0),
                        score=pos2['score'],
                        reason=f"Paired with {sym1}"
                    ))

                    used_positions.add((pos1['row'], pos1['col']))
                    used_positions.add((pos2['row'], pos2['col']))

        # Priority 2: Assign high-frequency individual symbols
        assigned_symbols = {a.key for a in assignments}
        remaining_symbols = [
            (sym, freq) for sym, freq in symbol_freq.items()
            if sym not in assigned_symbols
        ]
        remaining_symbols.sort(key=lambda x: x[1], reverse=True)

        # Get available positions sorted by quality
        all_positions = []
        for tier in ['prime', 'good', 'acceptable', 'edge']:
            all_positions.extend(self.positions[tier])

        for symbol, freq in remaining_symbols[:30]:  # Top 30 symbols
            # Find best available position
            for pos in all_positions:
                pos_tuple = (pos['row'], pos['col'])
                if pos_tuple not in used_positions:
                    assignments.append(KeyAssignment(
                        key=symbol,
                        position=pos_tuple,
                        layer=layer,
                        finger=pos['finger'],
                        reach_difficulty=(100 - pos['score']) / 100,
                        frequency=freq,
                        score=pos['score'],
                        reason=f"High frequency: {freq} uses"
                    ))
                    used_positions.add(pos_tuple)
                    break

        # Sort by frequency for final output
        return sorted(assignments, key=lambda x: x.frequency, reverse=True)

    def _get_symbol_frequencies(self) -> Dict[str, int]:
        """Extract symbol frequencies from keystroke data"""
        key_counts = self.data.get('keys', {})

        # Filter to symbols only (non-alphanumeric, not special keys)
        symbols = {}
        for key, count in key_counts.items():
            if (len(key) == 1 and
                not key.isalnum() and
                key not in [' ', '\n', '\t']):
                symbols[key] = count

        return symbols

    def _analyze_symbol_pairs(self) -> List[Tuple[Tuple[str, str], int]]:
        """
        Analyze symbol pairs and their combined frequencies

        Returns:
            List of ((sym1, sym2), combined_frequency) sorted by frequency
        """
        bigrams = self.data.get('bigrams', {})
        symbol_freq = self._get_symbol_frequencies()

        pair_analysis = []

        for pair in self.symbol_pairs:
            sym1, sym2 = pair
            # Count how often they appear together
            together_count = (
                bigrams.get(sym1 + sym2, 0) +
                bigrams.get(sym2 + sym1, 0)
            )

            # Combined frequency
            combined = symbol_freq.get(sym1, 0) + symbol_freq.get(sym2, 0)

            if combined > 0:
                pair_analysis.append((pair, combined + together_count * 2))

        return sorted(pair_analysis, key=lambda x: x[1], reverse=True)

    def _find_paired_positions(self, used_positions: Set) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Find two good positions for a symbol pair
        Preferably mirrored (left/right hand) or adjacent

        Args:
            used_positions: Set of already used positions

        Returns:
            Tuple of (position1, position2) or (None, None)
        """
        all_positions = []
        for tier in ['prime', 'good']:
            all_positions.extend(self.positions[tier])

        # Try to find mirrored positions
        for pos1 in all_positions:
            pos1_tuple = (pos1['row'], pos1['col'])
            if pos1_tuple in used_positions:
                continue

            # Look for mirror position (same row, opposite hand)
            for pos2 in all_positions:
                pos2_tuple = (pos2['row'], pos2['col'])
                if pos2_tuple in used_positions:
                    continue

                # Check if they're mirrored
                if (pos1['row'] == pos2['row'] and
                    'left' in pos1['finger'] and 'right' in pos2['finger']):
                    return pos1, pos2

                # Or adjacent
                if (pos1['row'] == pos2['row'] and
                    abs(pos1['col'] - pos2['col']) == 1):
                    return pos1, pos2

        # If no perfect match, just return two good positions
        available = [
            pos for pos in all_positions
            if (pos['row'], pos['col']) not in used_positions
        ]

        if len(available) >= 2:
            return available[0], available[1]

        return None, None

    def generate_layout_rationale(self, assignments: List[KeyAssignment]) -> str:
        """
        Generate markdown documentation explaining the layout

        Args:
            assignments: List of key assignments

        Returns:
            Markdown-formatted rationale
        """
        md = "# Optimized Voyager Layout Rationale\n\n"
        md += f"**Context**: {self.context.capitalize()}\n"
        md += f"**Total keystrokes analyzed**: {self.data.get('total_keystrokes', 0):,}\n\n"

        md += "## Key Placement Decisions\n\n"

        # Group by layer
        by_layer = {}
        for assignment in assignments:
            layer = assignment.layer
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(assignment)

        for layer, keys in sorted(by_layer.items()):
            md += f"### Layer {layer}\n\n"
            md += "| Key | Position | Finger | Frequency | Reason |\n"
            md += "|-----|----------|--------|-----------|--------|\n"

            for key_assign in sorted(keys, key=lambda x: x.frequency, reverse=True):
                md += f"| `{key_assign.key}` | "
                md += f"({key_assign.position[0]},{key_assign.position[1]}) | "
                md += f"{key_assign.finger} | "
                md += f"{key_assign.frequency} | "
                md += f"{key_assign.reason} |\n"

            md += "\n"

        # Add statistics
        md += "## Statistics\n\n"

        symbol_freq = self._get_symbol_frequencies()
        total_symbols = sum(symbol_freq.values())

        md += f"- Total symbol keystrokes: {total_symbols:,}\n"
        md += f"- Unique symbols: {len(symbol_freq)}\n"
        md += f"- Top 5 symbols: {', '.join(f'`{s}` ({c})' for s, c in sorted(symbol_freq.items(), key=lambda x: x[1], reverse=True)[:5])}\n"

        # Finger load
        finger_stats = self.data.get('finger_stats', {})
        if 'sfb_rate' in finger_stats:
            md += f"- Same-finger bigram rate: {finger_stats['sfb_rate']:.2f}%\n"
        if 'hand_alternation_rate' in finger_stats:
            md += f"- Hand alternation rate: {finger_stats['hand_alternation_rate']:.2f}%\n"

        md += "\n## Recommendations\n\n"
        md += "1. Practice the new symbol positions in isolation before full-speed typing\n"
        md += "2. Print this layout and keep it visible during the adaptation period\n"
        md += "3. Track your progress weekly to measure improvement\n"
        md += "4. Consider adding macros for the highest frequency patterns\n"

        return md
