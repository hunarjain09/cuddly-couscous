"""
Voyager keyboard simulator
Simulates typing on Voyager with 52 keys and multiple layers
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class VoyagerKey:
    """Represents a key on the Voyager"""
    position: Tuple[int, int]  # (row, col)
    layer: int
    key_value: str
    hand: str  # 'left' or 'right'
    finger: str
    reach_difficulty: float


class VoyagerLayout:
    """Represents a Voyager keyboard layout with multiple layers"""

    def __init__(self):
        """Initialize with a default QWERTY-based layout"""
        # Base layer (Layer 0)
        self.layers: Dict[int, Dict[str, VoyagerKey]] = {
            0: self._create_base_layer(),
            1: self._create_codepunc_layer(),
            2: self._create_num_layer(),
            3: self._create_nav_layer(),
            4: self._create_app_layer(),
            5: self._create_function_layer(),
        }

        self.layer_names = {
            0: 'Base',
            1: 'CodePunc',
            2: 'Num',
            3: 'TxtNav',
            4: 'App/Lay',
            5: 'Function',
        }

    def _create_base_layer(self) -> Dict[str, VoyagerKey]:
        """Create base QWERTY layer"""
        # Simplified Voyager base layout
        # Left hand: 6 columns x 4 rows + thumb cluster
        # Right hand: 6 columns x 4 rows + thumb cluster

        base = {}

        # Left hand main keys
        left_keys = [
            # Row 0 (top)
            ['esc', '[', '(', '-', ')', ']'],
            # Row 1
            ['`', 'q', 'w', 'f', 'p', 'g'],
            # Row 2 (home)
            ['+', 'a', 'r', 's', 't', 'd'],
            # Row 3 (bottom)
            ['~', 'z', 'x', 'c', 'v', 'b'],
        ]

        # Right hand main keys
        right_keys = [
            # Row 0 (top)
            ['<', '/', '?', '\\', '=', 'del'],
            # Row 1
            ['j', 'l', 'u', 'y', ';', '|'],
            # Row 2 (home)
            ['h', 'n', 'e', 'i', 'o', "'"],
            # Row 3 (bottom)
            ['k', 'm', ',', '.', '/', '!'],
        ]

        # Add left hand keys
        for row_idx, row in enumerate(left_keys):
            for col_idx, key in enumerate(row):
                base[key] = VoyagerKey(
                    position=(row_idx, col_idx),
                    layer=0,
                    key_value=key,
                    hand='left',
                    finger=self._get_finger_for_position('left', col_idx),
                    reach_difficulty=self._calculate_reach_difficulty(row_idx, col_idx)
                )

        # Add right hand keys
        for row_idx, row in enumerate(right_keys):
            for col_idx, key in enumerate(row):
                base[key] = VoyagerKey(
                    position=(row_idx, col_idx + 6),
                    layer=0,
                    key_value=key,
                    hand='right',
                    finger=self._get_finger_for_position('right', col_idx),
                    reach_difficulty=self._calculate_reach_difficulty(row_idx, col_idx)
                )

        # Thumb cluster keys
        thumb_keys = {
            'layer1': VoyagerKey((4, 0), 0, 'layer1', 'left', 'thumb', 0.3),
            'layer2': VoyagerKey((4, 1), 0, 'layer2', 'left', 'thumb', 0.2),
            'space': VoyagerKey((4, 2), 0, 'space', 'left', 'thumb', 0.1),
            'enter': VoyagerKey((4, 3), 0, 'enter', 'left', 'thumb', 0.2),
            'shift': VoyagerKey((4, 4), 0, 'shift', 'left', 'thumb', 0.3),
            'ctrl': VoyagerKey((4, 8), 0, 'ctrl', 'right', 'thumb', 0.3),
            'cmd': VoyagerKey((4, 9), 0, 'cmd', 'right', 'thumb', 0.2),
            'layer3': VoyagerKey((4, 10), 0, 'layer3', 'right', 'thumb', 0.2),
            'alt': VoyagerKey((4, 11), 0, 'alt', 'right', 'thumb', 0.3),
        }

        base.update(thumb_keys)
        return base

    def _create_codepunc_layer(self) -> Dict[str, VoyagerKey]:
        """Create CodePunc layer (Layer 1)"""
        # This would contain programming symbols
        return {}

    def _create_num_layer(self) -> Dict[str, VoyagerKey]:
        """Create number layer (Layer 2)"""
        return {}

    def _create_nav_layer(self) -> Dict[str, VoyagerKey]:
        """Create navigation layer (Layer 3)"""
        return {}

    def _create_app_layer(self) -> Dict[str, VoyagerKey]:
        """Create app switching layer (Layer 4)"""
        return {}

    def _create_function_layer(self) -> Dict[str, VoyagerKey]:
        """Create function key layer (Layer 5)"""
        return {}

    def _get_finger_for_position(self, hand: str, col: int) -> str:
        """Map column position to finger"""
        if hand == 'left':
            if col == 0:
                return 'pinky'
            elif col == 1:
                return 'ring'
            elif col == 2:
                return 'middle'
            elif col in [3, 4, 5]:
                return 'index'
        else:  # right hand
            if col in [0, 1, 2]:
                return 'index'
            elif col == 3:
                return 'middle'
            elif col == 4:
                return 'ring'
            elif col == 5:
                return 'pinky'
        return 'unknown'

    def _calculate_reach_difficulty(self, row: int, col: int) -> float:
        """Calculate reach difficulty for a position"""
        # Home row (row 2) is easiest
        base_difficulty = {
            0: 0.8,  # Top row
            1: 0.5,  # Upper row
            2: 0.0,  # Home row
            3: 0.7,  # Bottom row
        }.get(row, 1.0)

        # Add penalty for extreme columns
        if col == 0 or col == 5:
            base_difficulty += 0.2

        return min(1.0, base_difficulty)

    def find_key_layer(self, key: str) -> Optional[int]:
        """Find which layer contains a key"""
        for layer_num, layer_keys in self.layers.items():
            if key.lower() in layer_keys:
                return layer_num
        return None

    def get_key(self, key: str, layer: int = 0) -> Optional[VoyagerKey]:
        """Get VoyagerKey object for a key"""
        return self.layers.get(layer, {}).get(key.lower())


class VoyagerSimulator:
    """
    Simulates typing on Voyager keyboard
    Tracks layer switches and calculates overhead
    """

    def __init__(self, layout: VoyagerLayout = None):
        """
        Initialize simulator

        Args:
            layout: VoyagerLayout to use (default: create new)
        """
        self.layout = layout or VoyagerLayout()
        self.current_layer = 0
        self.layer_switch_cost_ms = 150  # Average time to switch layers

    def simulate_typing(self, text: str) -> Dict:
        """
        Simulate typing text on Voyager

        Args:
            text: Text to type

        Returns:
            Dict with simulation results
        """
        layer_switches = 0
        keys_per_layer = defaultdict(int)
        missing_keys = []
        total_time_estimate = 0
        current_layer = 0

        for char in text:
            # Find which layer has this key
            target_layer = self.layout.find_key_layer(char)

            if target_layer is None:
                missing_keys.append(char)
                continue

            # Count layer switch if needed
            if target_layer != current_layer:
                layer_switches += 1
                total_time_estimate += self.layer_switch_cost_ms
                current_layer = target_layer

            keys_per_layer[current_layer] += 1

        chars_typed = len(text) - len(missing_keys)

        return {
            'text_length': len(text),
            'chars_typed': chars_typed,
            'layer_switches': layer_switches,
            'switches_per_100_chars': (layer_switches / chars_typed * 100) if chars_typed > 0 else 0,
            'overhead_ms': total_time_estimate,
            'overhead_per_char_ms': total_time_estimate / chars_typed if chars_typed > 0 else 0,
            'keys_per_layer': dict(keys_per_layer),
            'missing_keys': list(set(missing_keys)),
            'layer_distribution': {
                layer: (count / chars_typed * 100) if chars_typed > 0 else 0
                for layer, count in keys_per_layer.items()
            }
        }

    def simulate_from_keystroke_data(self, keystroke_data: Dict) -> Dict:
        """
        Simulate Voyager typing based on recorded keystroke data

        Args:
            keystroke_data: Dict with 'keys' list from tracker

        Returns:
            Comprehensive simulation results
        """
        if 'keys' not in keystroke_data:
            return {'error': 'No keys data found'}

        # Extract keys as string
        keys = keystroke_data['keys']
        if isinstance(keys, dict):
            # If it's a dict of key: count, create a representative sample
            text = ''
            for key, count in keys.items():
                text += key * min(count, 100)  # Limit to avoid huge strings
        else:
            text = ''.join(keys)

        return self.simulate_typing(text)

    def analyze_layer_efficiency(self, keystroke_data: Dict) -> Dict:
        """
        Analyze how efficiently the current layout handles the typing data

        Args:
            keystroke_data: Dict with keystroke statistics

        Returns:
            Layer efficiency analysis
        """
        simulation = self.simulate_from_keystroke_data(keystroke_data)

        # Calculate efficiency metrics
        total_chars = simulation.get('chars_typed', 0)
        switches = simulation.get('layer_switches', 0)

        if total_chars == 0:
            return {'error': 'No data to analyze'}

        # Efficiency score: lower switches = higher efficiency
        # Target: < 5 switches per 100 chars = 100% efficiency
        target_switches_per_100 = 5
        actual_switches_per_100 = simulation['switches_per_100_chars']

        efficiency_score = max(0, min(100, (1 - actual_switches_per_100 / target_switches_per_100) * 100))

        return {
            **simulation,
            'efficiency_score': efficiency_score,
            'meets_target': actual_switches_per_100 <= target_switches_per_100,
            'target_switches_per_100': target_switches_per_100,
            'recommendations': self._generate_recommendations(simulation)
        }

    def _generate_recommendations(self, simulation: Dict) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []

        switches_per_100 = simulation.get('switches_per_100_chars', 0)

        if switches_per_100 > 10:
            recommendations.append("High layer switching detected. Consider moving frequently used symbols to base layer.")

        if switches_per_100 > 5:
            recommendations.append("Layer switches exceed target. Review symbol placement and consider thumb key optimization.")

        if simulation.get('missing_keys'):
            recommendations.append(f"Missing keys detected: {', '.join(simulation['missing_keys'][:5])}. Ensure all necessary keys are mapped.")

        layer_dist = simulation.get('layer_distribution', {})
        if layer_dist.get(0, 0) < 80:
            recommendations.append("Less than 80% of typing is on base layer. Consider consolidating frequently used keys.")

        return recommendations

    def compare_layouts(self, layout1: VoyagerLayout, layout2: VoyagerLayout, keystroke_data: Dict) -> Dict:
        """
        Compare two different layouts

        Args:
            layout1: First layout
            layout2: Second layout
            keystroke_data: Keystroke data to test with

        Returns:
            Comparison results
        """
        sim1 = VoyagerSimulator(layout1).simulate_from_keystroke_data(keystroke_data)
        sim2 = VoyagerSimulator(layout2).simulate_from_keystroke_data(keystroke_data)

        return {
            'layout1': sim1,
            'layout2': sim2,
            'improvement': {
                'layer_switches': sim1['layer_switches'] - sim2['layer_switches'],
                'overhead_ms': sim1['overhead_ms'] - sim2['overhead_ms'],
                'switches_per_100': sim1['switches_per_100_chars'] - sim2['switches_per_100_chars'],
            }
        }


class ThumbKeyAnalyzer:
    """Analyzes optimal thumb key assignments"""

    @staticmethod
    def analyze_thumb_candidates(keystroke_data: Dict, top_n: int = 10) -> List[Dict]:
        """
        Identify best candidates for thumb keys

        Args:
            keystroke_data: Keystroke data with key counts
            top_n: Number of candidates to return

        Returns:
            List of thumb key candidates sorted by suitability
        """
        # High-frequency, non-letter keys are best
        key_counts = keystroke_data.get('keys', {})

        candidates = {}

        # Special keys that are good for thumbs
        special_keys = {
            'space': 'High frequency, essential',
            'enter': 'High frequency, essential',
            'backspace': 'High frequency, error correction',
            'shift': 'Modifier, frequent',
            'tab': 'Frequent for navigation',
            'escape': 'Common in vim/coding',
        }

        for key, reason in special_keys.items():
            count = key_counts.get(f'[{key}]', 0) + key_counts.get(key, 0)
            if count > 0:
                candidates[key] = {
                    'key': key,
                    'frequency': count,
                    'reason': reason,
                    'score': count,
                }

        # Context-specific keys (for Python)
        context_keys = {
            '(': 'Very frequent in Python',
            '_': 'Common in snake_case',
            ':': 'Frequent in Python',
        }

        for key, reason in context_keys.items():
            count = key_counts.get(key, 0)
            if count > 100:  # Only if frequently used
                candidates[key] = {
                    'key': key,
                    'frequency': count,
                    'reason': reason,
                    'score': count * 0.8,  # Slightly lower priority than special keys
                }

        # Sort by score
        sorted_candidates = sorted(
            candidates.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        return sorted_candidates[:top_n]
