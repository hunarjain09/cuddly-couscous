"""
Oryx layout exporter
Generates JSON files compatible with ZSA Oryx configurator
"""

import json
from typing import Dict, List, Optional
from datetime import datetime


class OryxExporter:
    """
    Exports optimized layouts to Oryx-compatible JSON format
    Compatible with ZSA Voyager keyboard
    """

    # Voyager has 52 keys (26 per side)
    VOYAGER_KEYS = 52

    # QMK keycodes commonly used
    KEYCODES = {
        # Letters
        'a': 'KC_A', 'b': 'KC_B', 'c': 'KC_C', 'd': 'KC_D', 'e': 'KC_E',
        'f': 'KC_F', 'g': 'KC_G', 'h': 'KC_H', 'i': 'KC_I', 'j': 'KC_J',
        'k': 'KC_K', 'l': 'KC_L', 'm': 'KC_M', 'n': 'KC_N', 'o': 'KC_O',
        'p': 'KC_P', 'q': 'KC_Q', 'r': 'KC_R', 's': 'KC_S', 't': 'KC_T',
        'u': 'KC_U', 'v': 'KC_V', 'w': 'KC_W', 'x': 'KC_X', 'y': 'KC_Y',
        'z': 'KC_Z',

        # Numbers
        '0': 'KC_0', '1': 'KC_1', '2': 'KC_2', '3': 'KC_3', '4': 'KC_4',
        '5': 'KC_5', '6': 'KC_6', '7': 'KC_7', '8': 'KC_8', '9': 'KC_9',

        # Symbols
        '`': 'KC_GRV', '~': 'KC_TILD', '!': 'KC_EXLM', '@': 'KC_AT',
        '#': 'KC_HASH', '$': 'KC_DLR', '%': 'KC_PERC', '^': 'KC_CIRC',
        '&': 'KC_AMPR', '*': 'KC_ASTR', '(': 'KC_LPRN', ')': 'KC_RPRN',
        '-': 'KC_MINS', '_': 'KC_UNDS', '=': 'KC_EQL', '+': 'KC_PLUS',
        '[': 'KC_LBRC', ']': 'KC_RBRC', '{': 'KC_LCBR', '}': 'KC_RCBR',
        '\\': 'KC_BSLS', '|': 'KC_PIPE', ';': 'KC_SCLN', ':': 'KC_COLN',
        "'": 'KC_QUOT', '"': 'KC_DQUO', ',': 'KC_COMM', '<': 'KC_LT',
        '.': 'KC_DOT', '>': 'KC_GT', '/': 'KC_SLSH', '?': 'KC_QUES',

        # Special keys
        'space': 'KC_SPC', 'enter': 'KC_ENT', 'escape': 'KC_ESC',
        'esc': 'KC_ESC', 'backspace': 'KC_BSPC', 'tab': 'KC_TAB',
        'delete': 'KC_DEL', 'del': 'KC_DEL',

        # Modifiers
        'shift': 'KC_LSFT', 'ctrl': 'KC_LCTL', 'alt': 'KC_LALT',
        'cmd': 'KC_LGUI', 'super': 'KC_LGUI',

        # Navigation
        'up': 'KC_UP', 'down': 'KC_DOWN', 'left': 'KC_LEFT', 'right': 'KC_RGHT',
        'home': 'KC_HOME', 'end': 'KC_END', 'pgup': 'KC_PGUP', 'pgdn': 'KC_PGDN',

        # Function keys
        'f1': 'KC_F1', 'f2': 'KC_F2', 'f3': 'KC_F3', 'f4': 'KC_F4',
        'f5': 'KC_F5', 'f6': 'KC_F6', 'f7': 'KC_F7', 'f8': 'KC_F8',
        'f9': 'KC_F9', 'f10': 'KC_F10', 'f11': 'KC_F11', 'f12': 'KC_F12',

        # Layer keys
        'layer1': 'MO(1)', 'layer2': 'MO(2)', 'layer3': 'MO(3)',
        'layer4': 'MO(4)', 'layer5': 'MO(5)',

        # Transparent (pass through to lower layer)
        'trans': 'KC_TRNS',

        # No operation
        'none': 'KC_NO',
    }

    # Oryx layout template
    ORYX_TEMPLATE = {
        "version": 1,
        "uid": None,
        "layout": [],
        "layers": []
    }

    def __init__(self, layout_name: str = "Optimized Layout"):
        """
        Initialize exporter

        Args:
            layout_name: Name for the layout
        """
        self.layout_name = layout_name

    def key_to_qmk(self, key: str) -> str:
        """
        Convert a key character to QMK keycode

        Args:
            key: Key character or name

        Returns:
            QMK keycode string
        """
        key_lower = key.lower().strip('[]')

        # Direct mapping
        if key_lower in self.KEYCODES:
            return self.KEYCODES[key_lower]

        # Handle uppercase letters (shift modifier)
        if len(key) == 1 and key.isupper():
            return f"LSFT({self.KEYCODES[key.lower()]})"

        # Default to transparent
        return 'KC_TRNS'

    def position_to_oryx_index(self, row: int, col: int) -> int:
        """
        Convert (row, col) position to Oryx key index

        Voyager layout (52 keys):
        - Left hand: 26 keys (6 cols × 4 rows + 2 thumb keys)
        - Right hand: 26 keys (6 cols × 4 rows + 2 thumb keys)

        Args:
            row: Row number (0-4)
            col: Column number (0-11, where 0-5 is left, 6-11 is right)

        Returns:
            Oryx key index (0-51)
        """
        if row == 4:  # Thumb row
            # Thumb keys are at the end
            if col < 6:  # Left thumb
                return 24 + col
            else:  # Right thumb
                return 46 + (col - 6)

        # Regular keys
        if col < 6:  # Left hand
            return row * 6 + col
        else:  # Right hand
            return 26 + row * 6 + (col - 6)

    def create_layer(self, layer_num: int, layer_name: str, key_assignments: Dict[int, str]) -> Dict:
        """
        Create a layer definition

        Args:
            layer_num: Layer number (0-5)
            layer_name: Human-readable layer name
            key_assignments: Dict mapping key index -> QMK keycode

        Returns:
            Layer dict for Oryx format
        """
        # Initialize all keys to transparent
        keys = ['KC_TRNS'] * self.VOYAGER_KEYS

        # Apply assignments
        for index, keycode in key_assignments.items():
            if 0 <= index < self.VOYAGER_KEYS:
                keys[index] = keycode

        return {
            "id": layer_num,
            "name": layer_name,
            "keys": keys
        }

    def export_layout(
        self,
        assignments: List,
        base_layer_name: str = "Base",
        output_file: str = None
    ) -> Dict:
        """
        Export optimized layout to Oryx JSON format

        Args:
            assignments: List of KeyAssignment objects from optimizer
            base_layer_name: Name for base layer
            output_file: Optional file path to save to

        Returns:
            Oryx-compatible dict
        """
        oryx_layout = self.ORYX_TEMPLATE.copy()
        oryx_layout['uid'] = self._generate_uid()

        # Group assignments by layer
        layers_data = {}
        for assignment in assignments:
            layer = assignment.layer
            if layer not in layers_data:
                layers_data[layer] = {}

            # Convert position to Oryx index
            index = self.position_to_oryx_index(
                assignment.position[0],
                assignment.position[1]
            )

            # Convert key to QMK keycode
            keycode = self.key_to_qmk(assignment.key)

            layers_data[layer][index] = keycode

        # Create base layer
        layer_names = {
            0: base_layer_name,
            1: 'CodePunc',
            2: 'Numbers',
            3: 'Navigation',
            4: 'App Switch',
            5: 'Function'
        }

        layers = []
        for layer_num in range(6):  # Voyager supports 6 layers
            layer_name = layer_names.get(layer_num, f"Layer {layer_num}")
            key_assignments = layers_data.get(layer_num, {})
            layer = self.create_layer(layer_num, layer_name, key_assignments)
            layers.append(layer)

        oryx_layout['layers'] = layers

        # Add metadata
        oryx_layout['metadata'] = {
            'name': self.layout_name,
            'generated': datetime.now().isoformat(),
            'generator': 'keystroke-tracker v2.0.0',
            'description': f'Optimized layout based on keystroke analysis'
        }

        # Save to file if specified
        if output_file:
            self.save_to_file(oryx_layout, output_file)

        return oryx_layout

    def save_to_file(self, layout: Dict, filename: str):
        """
        Save layout to JSON file

        Args:
            layout: Oryx layout dict
            filename: Output file path
        """
        with open(filename, 'w') as f:
            json.dump(layout, f, indent=2)

        print(f"Layout exported to: {filename}")

    def _generate_uid(self) -> str:
        """Generate a unique ID for the layout"""
        import random
        import string
        # Generate a random 5-character alphanumeric ID
        return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

    def create_default_layout(self) -> Dict:
        """
        Create a default Voyager layout (QWERTY-based)

        Returns:
            Oryx layout dict
        """
        # Default QWERTY layout for Voyager
        base_keys = {}

        # Left hand main keys (QWERTY)
        left_layout = [
            ['KC_ESC', 'KC_Q', 'KC_W', 'KC_E', 'KC_R', 'KC_T'],
            ['KC_TAB', 'KC_A', 'KC_S', 'KC_D', 'KC_F', 'KC_G'],
            ['KC_LSFT', 'KC_Z', 'KC_X', 'KC_C', 'KC_V', 'KC_B'],
            ['KC_LCTL', 'KC_LALT', 'KC_LGUI', 'MO(1)', 'KC_SPC', 'KC_ENT'],
        ]

        # Right hand main keys
        right_layout = [
            ['KC_Y', 'KC_U', 'KC_I', 'KC_O', 'KC_P', 'KC_BSPC'],
            ['KC_H', 'KC_J', 'KC_K', 'KC_L', 'KC_SCLN', 'KC_QUOT'],
            ['KC_N', 'KC_M', 'KC_COMM', 'KC_DOT', 'KC_SLSH', 'KC_ENT'],
            ['MO(2)', 'KC_LEFT', 'KC_DOWN', 'KC_UP', 'KC_RGHT', 'KC_LGUI'],
        ]

        # Convert to flat index mapping
        for row_idx, row in enumerate(left_layout):
            for col_idx, key in enumerate(row):
                index = self.position_to_oryx_index(row_idx, col_idx)
                base_keys[index] = key

        for row_idx, row in enumerate(right_layout):
            for col_idx, key in enumerate(row):
                index = self.position_to_oryx_index(row_idx, col_idx + 6)
                base_keys[index] = key

        # Create layout
        oryx_layout = self.ORYX_TEMPLATE.copy()
        oryx_layout['uid'] = self._generate_uid()

        layers = []
        layers.append(self.create_layer(0, "Base", base_keys))
        layers.append(self.create_layer(1, "CodePunc", {}))
        layers.append(self.create_layer(2, "Numbers", {}))
        layers.append(self.create_layer(3, "Navigation", {}))
        layers.append(self.create_layer(4, "App", {}))
        layers.append(self.create_layer(5, "Function", {}))

        oryx_layout['layers'] = layers

        return oryx_layout

    def generate_cheatsheet(
        self,
        assignments: List,
        output_format: str = 'markdown'
    ) -> str:
        """
        Generate a printable cheatsheet of the layout

        Args:
            assignments: List of KeyAssignment objects
            output_format: 'markdown' or 'text'

        Returns:
            Formatted cheatsheet string
        """
        if output_format == 'markdown':
            return self._generate_markdown_cheatsheet(assignments)
        else:
            return self._generate_text_cheatsheet(assignments)

    def _generate_markdown_cheatsheet(self, assignments: List) -> str:
        """Generate markdown cheatsheet"""
        md = f"# {self.layout_name} - Cheatsheet\n\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d')}*\n\n"

        # Group by layer
        by_layer = {}
        for assignment in assignments:
            layer = assignment.layer
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(assignment)

        # Visual representation for each layer
        for layer_num in sorted(by_layer.keys()):
            md += f"## Layer {layer_num}\n\n"

            keys = by_layer[layer_num]

            # Create a simple visual grid
            grid = [[' ' for _ in range(12)] for _ in range(5)]

            for assignment in keys:
                row, col = assignment.position
                if row < 5 and col < 12:
                    grid[row][col] = assignment.key[:1]  # First char only

            # Left hand
            md += "```\n"
            md += "LEFT HAND:\n"
            for row in grid[:4]:
                md += '  '.join(row[:6]) + '\n'
            md += "\nRIGHT HAND:\n"
            for row in grid[:4]:
                md += '  '.join(row[6:]) + '\n'
            md += "```\n\n"

            # Key list
            md += "### Keys\n\n"
            for assignment in sorted(keys, key=lambda x: x.frequency, reverse=True):
                md += f"- **{assignment.key}**: {assignment.reason} ({assignment.frequency} uses)\n"

            md += "\n"

        return md

    def _generate_text_cheatsheet(self, assignments: List) -> str:
        """Generate plain text cheatsheet"""
        text = f"{self.layout_name} - Cheatsheet\n"
        text += "=" * 50 + "\n\n"

        by_layer = {}
        for assignment in assignments:
            layer = assignment.layer
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(assignment)

        for layer_num in sorted(by_layer.keys()):
            text += f"Layer {layer_num}\n"
            text += "-" * 50 + "\n"

            for assignment in by_layer[layer_num]:
                text += f"{assignment.key:3s} | Pos({assignment.position[0]},{assignment.position[1]}) | "
                text += f"{assignment.finger:12s} | {assignment.frequency:5d} uses\n"

            text += "\n"

        return text
