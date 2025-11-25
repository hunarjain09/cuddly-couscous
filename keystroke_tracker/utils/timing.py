"""
Timing analysis utilities for keystroke tracking
Detects hesitations and calculates inter-key timing
"""

import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Hesitation:
    """Represents a typing hesitation"""
    prev_key: str
    next_key: str
    delay_ms: float
    timestamp: float
    context_before: List[str]
    context_after: List[str]


class HesitationDetector:
    """Detects and analyzes typing hesitations"""

    # Timing thresholds in milliseconds
    NORMAL_INTER_KEY_TIME = 150  # Average time between keystrokes
    HESITATION_THRESHOLD = 500  # Consider it a hesitation above this
    PAUSE_THRESHOLD = 2000  # Long pause (thinking/reading)

    def __init__(self):
        self.hesitations: List[Hesitation] = []
        self.inter_key_times: List[float] = []

    def analyze_keystroke_timing(
        self,
        keys: List[str],
        timestamps: List[float],
        context_window: int = 5
    ) -> List[Hesitation]:
        """
        Identify keys that cause hesitation

        Args:
            keys: List of keys pressed
            timestamps: List of timestamps for each key
            context_window: Number of keys before/after to capture for context

        Returns:
            List of Hesitation objects
        """
        hesitations = []

        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i - 1]) * 1000  # Convert to ms

            # Store inter-key time for statistics
            if delta < self.PAUSE_THRESHOLD:
                self.inter_key_times.append(delta)

            # Detect hesitation
            if self.HESITATION_THRESHOLD < delta < self.PAUSE_THRESHOLD:
                context_before = keys[max(0, i - context_window):i]
                context_after = keys[i:min(len(keys), i + context_window)]

                hesitation = Hesitation(
                    prev_key=keys[i - 1],
                    next_key=keys[i],
                    delay_ms=delta,
                    timestamp=timestamps[i],
                    context_before=context_before,
                    context_after=context_after
                )
                hesitations.append(hesitation)

        self.hesitations.extend(hesitations)
        return hesitations

    def get_problematic_transitions(self, threshold_ms: float = 500) -> Dict[str, List[float]]:
        """
        Get key transitions that consistently cause delays

        Args:
            threshold_ms: Minimum delay to consider

        Returns:
            Dict mapping transition (key1→key2) to list of delay times
        """
        transitions = defaultdict(list)

        for hesitation in self.hesitations:
            if hesitation.delay_ms >= threshold_ms:
                transition = f"{hesitation.prev_key}→{hesitation.next_key}"
                transitions[transition].append(hesitation.delay_ms)

        # Sort by frequency and average delay
        sorted_transitions = {}
        for transition, delays in transitions.items():
            if len(delays) >= 3:  # At least 3 occurrences
                sorted_transitions[transition] = delays

        return dict(sorted(
            sorted_transitions.items(),
            key=lambda x: (len(x[1]), sum(x[1]) / len(x[1])),
            reverse=True
        ))

    def get_average_inter_key_time(self) -> float:
        """Calculate average time between keystrokes"""
        return sum(self.inter_key_times) / len(self.inter_key_times) if self.inter_key_times else 0

    def get_timing_stats(self) -> Dict[str, float]:
        """Get comprehensive timing statistics"""
        if not self.inter_key_times:
            return {
                'avg_ms': 0,
                'median_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'p95_ms': 0
            }

        sorted_times = sorted(self.inter_key_times)
        n = len(sorted_times)

        return {
            'avg_ms': sum(sorted_times) / n,
            'median_ms': sorted_times[n // 2],
            'min_ms': sorted_times[0],
            'max_ms': sorted_times[-1],
            'p95_ms': sorted_times[int(n * 0.95)] if n > 20 else sorted_times[-1]
        }


class TransitionTracker:
    """Tracks key-to-key transitions with timing and comfort scoring"""

    def __init__(self):
        self.transitions = defaultdict(lambda: {
            'count': 0,
            'total_timing': 0,
            'avg_timing': 0,
            'min_timing': float('inf'),
            'max_timing': 0,
            'finger_pair': None,
            'comfort_score': 0
        })

    def record_transition(
        self,
        key1: str,
        key2: str,
        timing_ms: float,
        finger1: Optional[str] = None,
        finger2: Optional[str] = None
    ):
        """
        Record a key-to-key transition with timing

        Args:
            key1: First key
            key2: Second key
            timing_ms: Time between keys in milliseconds
            finger1: Finger used for first key
            finger2: Finger used for second key
        """
        transition = f"{key1}→{key2}"
        data = self.transitions[transition]

        data['count'] += 1
        data['total_timing'] += timing_ms
        data['avg_timing'] = data['total_timing'] / data['count']
        data['min_timing'] = min(data['min_timing'], timing_ms)
        data['max_timing'] = max(data['max_timing'], timing_ms)

        if finger1 and finger2:
            data['finger_pair'] = (finger1, finger2)

    def calculate_comfort_score(self, key1: str, key2: str) -> float:
        """
        Calculate comfort score for a transition (0-100)
        Higher is better

        Factors:
        - Same finger: -40 points
        - Hand alternation: +20 points
        - Row jump distance: -10 per jump
        - Fast average timing: +10 points
        """
        from keystroke_tracker.utils.finger_map import FingerMap

        score = 50  # Base score

        # Penalize same finger bigrams
        if FingerMap.is_same_finger_bigram(key1, key2):
            score -= 40

        # Reward hand alternation
        if FingerMap.is_hand_alternation(key1, key2):
            score += 20

        # Penalize row jumps
        row_jump = FingerMap.calculate_row_jump(key1, key2)
        score -= row_jump * 10

        # Reward fast transitions (if we have data)
        transition = f"{key1}→{key2}"
        if transition in self.transitions:
            avg_timing = self.transitions[transition]['avg_timing']
            if avg_timing < 150:  # Fast typing
                score += 10
            elif avg_timing > 300:  # Slow typing
                score -= 10

        return max(0, min(100, score))  # Clamp to 0-100

    def get_top_transitions(self, n: int = 50) -> List[Tuple[str, Dict]]:
        """Get the N most common transitions"""
        return sorted(
            self.transitions.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:n]

    def get_slow_transitions(self, threshold_ms: float = 300, min_count: int = 10) -> List[Tuple[str, Dict]]:
        """
        Get transitions that are consistently slow

        Args:
            threshold_ms: Minimum average timing to consider slow
            min_count: Minimum occurrences to include
        """
        slow = [
            (transition, data)
            for transition, data in self.transitions.items()
            if data['count'] >= min_count and data['avg_timing'] >= threshold_ms
        ]

        return sorted(slow, key=lambda x: x[1]['avg_timing'], reverse=True)

    def get_awkward_transitions(self, min_count: int = 5) -> List[Tuple[str, Dict]]:
        """Get transitions with poor comfort scores"""
        awkward = []

        for transition, data in self.transitions.items():
            if data['count'] >= min_count:
                if '→' in transition:
                    key1, key2 = transition.split('→')
                    comfort = self.calculate_comfort_score(key1, key2)
                    if comfort < 30:  # Poor comfort
                        data['comfort_score'] = comfort
                        awkward.append((transition, data))

        return sorted(awkward, key=lambda x: (x[1]['comfort_score'], -x[1]['count']))
