"""
Context detection system
Identifies the language/context being typed (Python, JS, shell, etc.)
"""

import time
import re
from typing import Dict, List, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum


class Context(Enum):
    """Enum for detected contexts"""
    IDLE = "idle"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SHELL = "shell"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    MARKDOWN = "markdown"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class ContextSignal:
    """Represents a signal for context detection"""
    signal_type: str  # 'keyword', 'pattern', 'symbol', 'file'
    value: str
    confidence: float  # 0.0 to 1.0
    timestamp: float


class ContextDetector:
    """Detects the programming language or context being typed"""

    # Context definitions with signals
    CONTEXTS = {
        Context.PYTHON: {
            'keywords': [
                'def', 'class', 'import', 'from', 'for', 'in', 'self',
                '__init__', 'return', 'if', 'elif', 'else', 'while',
                'try', 'except', 'finally', 'raise', 'with', 'as',
                'lambda', 'yield', 'print', 'range', 'len', 'str',
                'dict', 'list', 'tuple', 'set', 'True', 'False', 'None',
            ],
            'patterns': [
                r'\.py\b',
                r'python',
                r'pip\s+install',
                r'virtualenv',
                r'__\w+__',  # Dunder methods
                r'@\w+\(',  # Decorators with parens
            ],
            'symbols': [':', '__', '[]', "''", '"""'],
            'extensions': ['.py', '.pyw'],
            'weight': 1.0,
        },
        Context.JAVASCRIPT: {
            'keywords': [
                'const', 'let', 'var', 'function', 'return',
                'if', 'else', 'for', 'while', 'switch', 'case',
                'async', 'await', 'Promise', 'console', 'require',
                'import', 'export', 'default', 'class', 'extends',
                'this', 'new', 'typeof', 'instanceof',
            ],
            'patterns': [
                r'\.js\b',
                r'\.jsx\b',
                r'npm\s+',
                r'node\s+',
                r'=>',  # Arrow function
                r'console\.log',
                r'require\(',
            ],
            'symbols': ['=>', '{}', '`', '${'],
            'extensions': ['.js', '.jsx', '.mjs'],
            'weight': 1.0,
        },
        Context.TYPESCRIPT: {
            'keywords': [
                'interface', 'type', 'enum', 'namespace', 'implements',
                'extends', 'public', 'private', 'protected', 'readonly',
                'const', 'let', 'var', 'function', 'async', 'await',
            ],
            'patterns': [
                r'\.ts\b',
                r'\.tsx\b',
                r':\s*\w+\s*[=;]',  # Type annotations
                r'<\w+>',  # Generics
            ],
            'symbols': ['<>', ':', '=>'],
            'extensions': ['.ts', '.tsx'],
            'weight': 1.0,
        },
        Context.SHELL: {
            'keywords': [
                'cd', 'ls', 'grep', 'awk', 'sed', 'cat', 'echo',
                'git', 'docker', 'sudo', 'chmod', 'chown', 'mkdir',
                'rm', 'mv', 'cp', 'find', 'export', 'source',
            ],
            'patterns': [
                r'\.sh\b',
                r'bash',
                r'zsh',
                r'#!/',
                r'\$\w+',  # Variables
            ],
            'symbols': ['|', '&&', '||', '$', '#', '>>'],
            'extensions': ['.sh', '.bash', '.zsh'],
            'weight': 1.0,
        },
        Context.SQL: {
            'keywords': [
                'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT',
                'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'ORDER',
                'INSERT', 'INTO', 'UPDATE', 'DELETE', 'CREATE',
                'TABLE', 'DATABASE', 'INDEX', 'DROP', 'ALTER',
            ],
            'patterns': [
                r'\.sql\b',
                r'SELECT\s+.*\s+FROM',
            ],
            'symbols': [],
            'extensions': ['.sql'],
            'weight': 1.0,
        },
        Context.HTML: {
            'keywords': [
                'div', 'span', 'body', 'head', 'html', 'script',
                'style', 'link', 'meta', 'title', 'href', 'src',
            ],
            'patterns': [
                r'\.html\b',
                r'<\w+>',
                r'<\/\w+>',
                r'<!DOCTYPE',
            ],
            'symbols': ['<>', '</', '/>'],
            'extensions': ['.html', '.htm'],
            'weight': 1.0,
        },
        Context.CSS: {
            'keywords': [
                'color', 'background', 'margin', 'padding', 'border',
                'width', 'height', 'display', 'flex', 'grid',
                'position', 'absolute', 'relative', 'fixed',
            ],
            'patterns': [
                r'\.css\b',
                r'\.\w+\s*\{',  # Class selector
                r'#\w+\s*\{',  # ID selector
                r':\s*\w+;',  # Property
            ],
            'symbols': ['{}', ':', ';', '#', '.'],
            'extensions': ['.css', '.scss', '.sass'],
            'weight': 1.0,
        },
        Context.MARKDOWN: {
            'keywords': [],
            'patterns': [
                r'\.md\b',
                r'#+\s+',  # Headers
                r'\[.*\]\(.*\)',  # Links
                r'```',  # Code blocks
            ],
            'symbols': ['#', '*', '-', '[', ']', '`'],
            'extensions': ['.md', '.markdown'],
            'weight': 1.0,
        },
    }

    # State machine states
    STATE_IDLE = "IDLE"
    STATE_CANDIDATE = "CANDIDATE"
    STATE_ACTIVE = "ACTIVE"

    def __init__(self, sensitivity: float = 0.7):
        """
        Initialize context detector

        Args:
            sensitivity: Threshold for context activation (0.0-1.0)
        """
        self.sensitivity = sensitivity
        self.state = self.STATE_IDLE
        self.active_context: Optional[Context] = None
        self.candidate_context: Optional[Context] = None
        self.confidence_score = 0.0
        self.signals_detected: List[ContextSignal] = []
        self.last_activity = time.time()
        self.context_history: List[Context] = []
        self.context_durations: Dict[Context, float] = defaultdict(float)

        # Scoring
        self.signal_window = 30  # seconds
        self.min_signals = 3  # Minimum signals to activate context

    def detect_context(self, recent_buffer: List[str], force: bool = False) -> Optional[Context]:
        """
        Main context detection method

        Args:
            recent_buffer: Recent keys typed (last 100 or so)
            force: Force re-detection even if context is active

        Returns:
            Detected context or None
        """
        current_time = time.time()

        # Join buffer to text for pattern matching
        buffer_text = ''.join(recent_buffer)

        # Clear old signals
        self._clear_old_signals(current_time)

        # Detect signals in buffer
        detected_signals = self._detect_signals(buffer_text, current_time)
        self.signals_detected.extend(detected_signals)

        # Calculate confidence scores for each context
        scores = self._calculate_context_scores()

        # Get best match
        if scores:
            best_context, best_score = max(scores.items(), key=lambda x: x[1])

            # State machine logic
            if self.state == self.STATE_IDLE:
                if best_score >= self.sensitivity / 2:
                    self.state = self.STATE_CANDIDATE
                    self.candidate_context = best_context
                    self.confidence_score = best_score

            elif self.state == self.STATE_CANDIDATE:
                if best_score >= self.sensitivity and len(self.signals_detected) >= self.min_signals:
                    self.state = self.STATE_ACTIVE
                    self.active_context = best_context
                    self.confidence_score = best_score
                    self.context_history.append(best_context)

            elif self.state == self.STATE_ACTIVE:
                # Update confidence
                self.confidence_score = best_score

                # Check if context has changed
                if best_context != self.active_context and best_score >= self.sensitivity:
                    self.active_context = best_context
                    self.context_history.append(best_context)

                # Deactivate if confidence drops too low
                if best_score < self.sensitivity / 3:
                    self.state = self.STATE_IDLE
                    self.active_context = None

        self.last_activity = current_time
        return self.active_context

    def _detect_signals(self, text: str, timestamp: float) -> List[ContextSignal]:
        """Detect context signals in text"""
        signals = []

        for context, patterns in self.CONTEXTS.items():
            # Check keywords
            text_lower = text.lower()
            for keyword in patterns['keywords']:
                if keyword.lower() in text_lower:
                    signals.append(ContextSignal(
                        signal_type='keyword',
                        value=keyword,
                        confidence=0.8,
                        timestamp=timestamp
                    ))

            # Check regex patterns
            for pattern in patterns['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    signals.append(ContextSignal(
                        signal_type='pattern',
                        value=pattern,
                        confidence=0.9,
                        timestamp=timestamp
                    ))

            # Check symbols
            for symbol in patterns['symbols']:
                if symbol in text:
                    signals.append(ContextSignal(
                        signal_type='symbol',
                        value=symbol,
                        confidence=0.6,
                        timestamp=timestamp
                    ))

        return signals

    def _calculate_context_scores(self) -> Dict[Context, float]:
        """Calculate confidence scores for each context"""
        scores = defaultdict(float)

        for signal in self.signals_detected:
            # Find which context(s) this signal belongs to
            for context, patterns in self.CONTEXTS.items():
                if (signal.value in patterns['keywords'] or
                    signal.value in patterns['patterns'] or
                    signal.value in patterns['symbols']):
                    scores[context] += signal.confidence * patterns['weight']

        # Normalize scores
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {ctx: score / max_score for ctx, score in scores.items()}

        return scores

    def _clear_old_signals(self, current_time: float):
        """Clear signals older than the signal window"""
        self.signals_detected = [
            s for s in self.signals_detected
            if current_time - s.timestamp <= self.signal_window
        ]

    def get_active_context(self) -> Optional[Context]:
        """Get the currently active context"""
        return self.active_context

    def get_confidence(self) -> float:
        """Get confidence score for active context"""
        return self.confidence_score

    def get_context_statistics(self) -> Dict:
        """Get statistics about context usage"""
        context_counts = Counter(self.context_history)

        return {
            'current_context': self.active_context.value if self.active_context else None,
            'confidence': self.confidence_score,
            'state': self.state,
            'signal_count': len(self.signals_detected),
            'context_counts': dict(context_counts),
            'most_common': context_counts.most_common(1)[0] if context_counts else None,
        }

    def reset(self):
        """Reset detector to idle state"""
        self.state = self.STATE_IDLE
        self.active_context = None
        self.candidate_context = None
        self.confidence_score = 0.0
        self.signals_detected.clear()


class ContextAwareAnalyzer:
    """Analyzer that tracks statistics per context"""

    def __init__(self):
        self.context_detector = ContextDetector()
        self.context_data: Dict[Context, Dict] = defaultdict(lambda: {
            'keystrokes': 0,
            'keys': Counter(),
            'bigrams': Counter(),
            'symbols': Counter(),
            'duration': 0,
            'start_time': None,
        })
        self.current_context_start = None

    def update(self, keys: List[str], context: Optional[Context] = None):
        """
        Update statistics for current context

        Args:
            keys: Recent keys typed
            context: Current context (if known)
        """
        if not context:
            context = self.context_detector.detect_context(keys)

        if not context:
            return

        # Initialize context start time
        if self.current_context_start is None:
            self.current_context_start = time.time()

        data = self.context_data[context]
        data['keystrokes'] += len(keys)

        # Update counters
        for key in keys:
            data['keys'][key] += 1

            # Track symbols
            if not key.isalnum() and not key.startswith('['):
                data['symbols'][key] += 1

        # Track bigrams
        for i in range(len(keys) - 1):
            bigram = keys[i] + keys[i + 1]
            data['bigrams'][bigram] += 1

        # Update duration
        if self.current_context_start:
            data['duration'] = time.time() - self.current_context_start

    def get_context_report(self, context: Context) -> Dict:
        """Get report for a specific context"""
        data = self.context_data.get(context)
        if not data:
            return {}

        return {
            'context': context.value,
            'keystrokes': data['keystrokes'],
            'duration': data['duration'],
            'keys_per_second': data['keystrokes'] / data['duration'] if data['duration'] > 0 else 0,
            'top_keys': data['keys'].most_common(20),
            'top_symbols': data['symbols'].most_common(10),
            'top_bigrams': data['bigrams'].most_common(20),
        }

    def get_all_contexts_report(self) -> Dict[str, Dict]:
        """Get report for all detected contexts"""
        return {
            context.value: self.get_context_report(context)
            for context in self.context_data.keys()
        }
