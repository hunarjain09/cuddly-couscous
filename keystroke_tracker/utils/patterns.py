"""
Pattern detection utilities for keystroke analysis
Identifies common sequences, constructs, and symbols
"""

import re
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class Pattern:
    """Represents a detected pattern in typing"""
    pattern: str
    frequency: int
    avg_typing_speed: float
    contexts: List[str]
    category: str  # 'symbol_pair', 'keyword', 'construct', etc.


class PatternDetector:
    """Detects common patterns in keystroke data"""

    # Common symbol pairs
    SYMBOL_PAIRS = [
        '()', '[]', '{}', '<>', '""', "''", '``',
        '->', '=>', '==', '!=', '<=', '>=', '&&', '||',
        '::', '//', '/*', '*/', '<!--', '-->',
    ]

    # Programming constructs by language
    PYTHON_CONSTRUCTS = {
        'control_flow': [
            r'for\s+\w+\s+in',
            r'while\s+',
            r'if\s+',
            r'elif\s+',
            r'else:',
        ],
        'functions': [
            r'def\s+\w+\(',
            r'return\s+',
            r'lambda\s+',
            r'yield\s+',
        ],
        'classes': [
            r'class\s+\w+',
            r'self\.',
            r'def\s+__init__',
            r'@\w+',  # Decorators
        ],
        'imports': [
            r'import\s+',
            r'from\s+\w+\s+import',
        ],
        'exceptions': [
            r'try:',
            r'except\s+',
            r'finally:',
            r'raise\s+',
        ],
        'comprehensions': [
            r'\[.+for\s+.+in\s+.+\]',  # List comprehension
            r'\{.+for\s+.+in\s+.+\}',  # Dict/set comprehension
        ]
    }

    JAVASCRIPT_CONSTRUCTS = {
        'variables': [
            r'const\s+\w+',
            r'let\s+\w+',
            r'var\s+\w+',
        ],
        'functions': [
            r'function\s+\w+',
            r'\w+\s*=>\s*',  # Arrow function
            r'async\s+',
            r'await\s+',
        ],
        'control_flow': [
            r'if\s*\(',
            r'for\s*\(',
            r'while\s*\(',
            r'switch\s*\(',
        ],
        'common': [
            r'console\.log',
            r'require\(',
            r'import\s+',
            r'export\s+',
        ]
    }

    def __init__(self):
        self.detected_patterns: List[Pattern] = []
        self.pattern_counts: Counter = Counter()

    def detect_symbol_pairs(self, text: str) -> Dict[str, int]:
        """
        Detect symbol pairs in text

        Returns:
            Dict mapping pair -> count
        """
        counts = {}
        for pair in self.SYMBOL_PAIRS:
            count = text.count(pair)
            if count > 0:
                counts[pair] = count

        return counts

    def detect_python_constructs(self, text: str) -> Dict[str, Dict[str, int]]:
        """
        Detect Python-specific constructs

        Returns:
            Dict mapping category -> {construct -> count}
        """
        results = defaultdict(dict)

        for category, patterns in self.PYTHON_CONSTRUCTS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                if matches:
                    results[category][pattern] = len(matches)

        return dict(results)

    def detect_javascript_constructs(self, text: str) -> Dict[str, Dict[str, int]]:
        """Detect JavaScript-specific constructs"""
        results = defaultdict(dict)

        for category, patterns in self.JAVASCRIPT_CONSTRUCTS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                if matches:
                    results[category][pattern] = len(matches)

        return dict(results)

    def find_repeated_sequences(
        self,
        keys: List[str],
        min_length: int = 3,
        min_frequency: int = 3
    ) -> List[Tuple[str, int]]:
        """
        Find repeated key sequences that might be good macro candidates

        Args:
            keys: List of keys pressed
            min_length: Minimum sequence length
            min_frequency: Minimum times sequence must appear

        Returns:
            List of (sequence, count) tuples, sorted by frequency
        """
        sequences = Counter()

        # Generate all possible sequences
        for length in range(min_length, min(20, len(keys))):
            for i in range(len(keys) - length + 1):
                sequence = ''.join(keys[i:i + length])
                # Filter out sequences that are just repeated single keys
                if len(set(sequence)) > 1:
                    sequences[sequence] += 1

        # Filter by minimum frequency
        frequent = [(seq, count) for seq, count in sequences.items() if count >= min_frequency]

        return sorted(frequent, key=lambda x: x[1], reverse=True)

    def analyze_symbol_usage(self, keys: List[str]) -> Dict[str, any]:
        """
        Analyze symbol usage patterns

        Returns:
            Dict with symbol statistics
        """
        # Filter to just symbols (non-alphanumeric)
        symbols = [k for k in keys if not k.isalnum() and k not in ['space', 'enter', 'tab']]

        symbol_counts = Counter(symbols)
        total_symbols = len(symbols)

        # Categorize symbols
        categories = {
            'brackets': ['(', ')', '[', ']', '{', '}', '<', '>'],
            'quotes': ['"', "'", '`'],
            'operators': ['+', '-', '*', '/', '=', '!', '&', '|', '^', '%', '~'],
            'punctuation': ['.', ',', ';', ':', '?', '!'],
            'special': ['@', '#', '$', '_', '\\', '/', '|'],
        }

        category_counts = {}
        for category, syms in categories.items():
            count = sum(symbol_counts.get(s, 0) for s in syms)
            category_counts[category] = count

        # Calculate symbol pairs (opening/closing)
        pairs = {
            '()': (symbol_counts.get('(', 0), symbol_counts.get(')', 0)),
            '[]': (symbol_counts.get('[', 0), symbol_counts.get(']', 0)),
            '{}': (symbol_counts.get('{', 0), symbol_counts.get('}', 0)),
            '<>': (symbol_counts.get('<', 0), symbol_counts.get('>', 0)),
        }

        return {
            'total_symbols': total_symbols,
            'unique_symbols': len(symbol_counts),
            'symbol_counts': dict(symbol_counts.most_common(20)),
            'category_counts': category_counts,
            'pairs': pairs,
            'most_common': symbol_counts.most_common(10),
        }

    def suggest_macros(
        self,
        keys: List[str],
        patterns: List[str] = None,
        threshold: int = 50
    ) -> List[Dict]:
        """
        Suggest macro candidates based on frequency

        Args:
            keys: List of keys pressed
            patterns: Optional list of specific patterns to check
            threshold: Minimum frequency to suggest as macro

        Returns:
            List of macro suggestions with metadata
        """
        suggestions = []

        # Check predefined patterns
        if patterns is None:
            patterns = self.SYMBOL_PAIRS + [
                'def ', 'class ', 'import ', 'from ',
                '__init__', '__main__', '__name__',
                '"""', "'''",
                '.com', '.org', 'https://', 'www.',
            ]

        text = ''.join(keys)

        for pattern in patterns:
            count = text.count(pattern)
            if count >= threshold:
                keystrokes_current = len(pattern)
                keystrokes_with_macro = 1  # Single key press or combo
                savings = (keystrokes_current - keystrokes_with_macro) * count

                suggestions.append({
                    'pattern': pattern,
                    'frequency': count,
                    'keystrokes_current': keystrokes_current,
                    'keystrokes_saved': savings,
                    'percentage': (count / len(keys)) * 100,
                    'recommended': savings > 100,  # Recommend if saves 100+ keystrokes
                })

        # Also check for repeated sequences
        repeated = self.find_repeated_sequences(keys, min_length=3, min_frequency=threshold)
        for sequence, count in repeated[:10]:  # Top 10
            if len(sequence) >= 3 and count >= threshold:
                savings = (len(sequence) - 1) * count
                suggestions.append({
                    'pattern': sequence,
                    'frequency': count,
                    'keystrokes_current': len(sequence),
                    'keystrokes_saved': savings,
                    'percentage': (count / len(keys)) * 100,
                    'recommended': savings > 100,
                })

        return sorted(suggestions, key=lambda x: x['keystrokes_saved'], reverse=True)

    def calculate_typing_efficiency(self, keys: List[str], context: str = None) -> Dict[str, float]:
        """
        Calculate typing efficiency metrics

        Returns:
            Dict with efficiency scores
        """
        total_keys = len(keys)
        if total_keys == 0:
            return {'efficiency': 0, 'wasted_keystrokes': 0}

        # Count backspaces (wasted effort)
        backspaces = keys.count('backspace') + keys.count('delete')

        # Count modifier combos vs single keys
        modifiers = ['shift', 'ctrl', 'alt', 'cmd', 'super']
        modifier_count = sum(keys.count(m) for m in modifiers)

        # Calculate efficiency
        productive_keys = total_keys - backspaces - modifier_count
        efficiency = (productive_keys / total_keys) * 100 if total_keys > 0 else 0

        return {
            'efficiency': efficiency,
            'total_keys': total_keys,
            'productive_keys': productive_keys,
            'backspaces': backspaces,
            'backspace_rate': (backspaces / total_keys) * 100 if total_keys > 0 else 0,
            'modifier_usage': (modifier_count / total_keys) * 100 if total_keys > 0 else 0,
        }


class PythonAnalyzer:
    """Specialized analyzer for Python code"""

    # Python symbol priority for Voyager layout
    SYMBOL_PRIORITY = {
        'priority_1_home_row': ['(', ')', '[', ']', ':', '_', '.', '='],
        'priority_2_easy_reach': ['"', '#', ',', '@', '-', '+', "'"],
        'priority_3_less_common': ['{', '}', '<', '>', '|', '\\', ';', '`', '~', '!', '?']
    }

    @staticmethod
    def analyze_python_symbols(keys: List[str]) -> Dict[str, any]:
        """Analyze Python-specific symbol usage"""
        symbol_counts = Counter([k for k in keys if not k.isalnum()])

        # Categorize by priority
        priority_analysis = {}
        for priority, symbols in PythonAnalyzer.SYMBOL_PRIORITY.items():
            count = sum(symbol_counts.get(s, 0) for s in symbols)
            priority_analysis[priority] = {
                'count': count,
                'symbols': {s: symbol_counts.get(s, 0) for s in symbols if s in symbol_counts}
            }

        # Calculate priority ratio
        total_symbols = sum(symbol_counts.values())
        p1_count = priority_analysis['priority_1_home_row']['count']
        priority_ratio = (p1_count / total_symbols * 100) if total_symbols > 0 else 0

        return {
            'priority_analysis': priority_analysis,
            'priority_ratio': priority_ratio,
            'total_symbols': total_symbols,
            'recommendation': 'Focus on home row placement for priority 1 symbols'
        }

    @staticmethod
    def detect_python_patterns(text: str) -> Dict[str, any]:
        """Detect common Python patterns"""
        patterns = {
            'list_comp': len(re.findall(r'\[.+for\s+.+in\s+.+\]', text)),
            'dict_comp': len(re.findall(r'\{.+for\s+.+in\s+.+\}', text)),
            'f_strings': len(re.findall(r'f["\']', text)),
            'docstrings': len(re.findall(r'"""[\s\S]*?"""', text)) + len(re.findall(r"'''[\s\S]*?'''", text)),
            'type_hints': len(re.findall(r'->', text)) + len(re.findall(r':\s*\w+', text)),
            'dunder_methods': len(re.findall(r'__\w+__', text)),
            'decorators': len(re.findall(r'@\w+', text)),
        }

        return patterns
