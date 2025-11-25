"""
Core keystroke tracking system
Captures keystrokes with timing, context, and metadata
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict, Counter
from datetime import datetime
import threading

from pynput import keyboard

from keystroke_tracker.utils.finger_map import FingerMap
from keystroke_tracker.utils.timing import HesitationDetector, TransitionTracker
from keystroke_tracker.utils.patterns import PatternDetector


class KeystrokeTracker:
    """Main keystroke tracking class"""

    def __init__(self, data_file: str = None):
        """
        Initialize keystroke tracker

        Args:
            data_file: Path to JSON file for storing data
        """
        self.data_file = data_file or os.path.join('data', 'keystrokes.json')
        self.ensure_data_dir()

        # Session data
        self.session_start = time.time()
        self.session_id = f"session_{int(self.session_start)}"

        # Keystroke data
        self.keys: List[str] = []
        self.timestamps: List[float] = []
        self.key_counts: Counter = Counter()
        self.bigrams: Counter = Counter()
        self.trigrams: Counter = Counter()
        self.combos: Counter = Counter()

        # Current state
        self.buffer: List[str] = []  # Recent keys for context detection
        self.buffer_size = 100
        self.current_modifiers: Set[str] = set()

        # Analyzers
        self.hesitation_detector = HesitationDetector()
        self.transition_tracker = TransitionTracker()
        self.pattern_detector = PatternDetector()

        # Statistics
        self.total_keystrokes = 0
        self.session_duration = 0

        # Load existing data
        self.data = self.load_data()

        # Listener
        self.listener = None
        self.running = False

        # Auto-save
        self.save_interval = 60  # Save every 60 seconds
        self.last_save = time.time()
        self.save_lock = threading.Lock()

    def ensure_data_dir(self):
        """Ensure data directory exists"""
        data_dir = os.path.dirname(self.data_file)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)

    def load_data(self) -> Dict:
        """Load existing keystroke data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading data: {e}")
                return self._get_empty_data()
        return self._get_empty_data()

    def _get_empty_data(self) -> Dict:
        """Get empty data structure"""
        return {
            'total_keystrokes': 0,
            'total_sessions': 0,
            'first_session': None,
            'last_session': None,
            'keys': {},
            'bigrams': {},
            'trigrams': {},
            'combos': {},
            'sessions': {},
            'finger_stats': {},
            'transitions': {},
        }

    def save_data(self, force: bool = False):
        """
        Save keystroke data to file

        Args:
            force: Force save even if interval hasn't passed
        """
        current_time = time.time()

        if not force and (current_time - self.last_save) < self.save_interval:
            return

        with self.save_lock:
            try:
                # Update session data
                self.session_duration = current_time - self.session_start

                # Merge current session into overall data
                self._merge_session_data()

                # Write to file
                with open(self.data_file, 'w') as f:
                    json.dump(self.data, f, indent=2)

                self.last_save = current_time
                print(f"Data saved to {self.data_file}")

            except Exception as e:
                print(f"Error saving data: {e}")

    def _merge_session_data(self):
        """Merge current session data into overall statistics"""
        # Update totals
        self.data['total_keystrokes'] += self.total_keystrokes
        self.data['total_sessions'] += 1

        if not self.data['first_session']:
            self.data['first_session'] = self.session_id

        self.data['last_session'] = self.session_id

        # Merge key counts
        for key, count in self.key_counts.items():
            self.data['keys'][key] = self.data['keys'].get(key, 0) + count

        # Merge bigrams
        for bigram, count in self.bigrams.items():
            self.data['bigrams'][bigram] = self.data['bigrams'].get(bigram, 0) + count

        # Merge trigrams
        for trigram, count in self.trigrams.items():
            self.data['trigrams'][trigram] = self.data['trigrams'].get(trigram, 0) + count

        # Merge combos
        for combo, count in self.combos.items():
            self.data['combos'][combo] = self.data['combos'].get(combo, 0) + count

        # Store session data
        self.data['sessions'][self.session_id] = {
            'start_time': self.session_start,
            'duration': self.session_duration,
            'keystrokes': self.total_keystrokes,
            'keys': dict(self.key_counts),
            'timestamp': datetime.now().isoformat(),
        }

        # Calculate and store finger statistics
        self.data['finger_stats'] = self._calculate_finger_stats()

        # Store transition data
        top_transitions = self.transition_tracker.get_top_transitions(100)
        for transition, data in top_transitions:
            self.data['transitions'][transition] = {
                'count': data['count'],
                'avg_timing': data['avg_timing'],
                'comfort_score': self.transition_tracker.calculate_comfort_score(
                    *transition.split('→')
                ) if '→' in transition else 0
            }

    def _calculate_finger_stats(self) -> Dict:
        """Calculate finger usage statistics"""
        finger_load = FingerMap.calculate_finger_load(self.data['keys'])

        return {
            'finger_load': {f.value: load for f, load in finger_load.items()},
            'sfb_rate': FingerMap.calculate_sfb_rate(self.data['bigrams']),
            'hand_alternation_rate': FingerMap.calculate_hand_alternation_rate(self.data['bigrams']),
        }

    def _normalize_key(self, key) -> str:
        """Normalize key representation"""
        try:
            # Handle special keys
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            elif hasattr(key, 'name'):
                return f"[{key.name}]"
            else:
                return str(key).replace('Key.', '[').replace('>', ']')
        except AttributeError:
            return str(key)

    def on_press(self, key):
        """Handle key press event"""
        try:
            key_str = self._normalize_key(key)
            timestamp = time.time()

            # Track modifiers
            if key_str in ['[shift]', '[ctrl]', '[alt]', '[cmd]', '[super]']:
                self.current_modifiers.add(key_str.strip('[]'))
                return

            # Record the keystroke
            self.keys.append(key_str)
            self.timestamps.append(timestamp)
            self.buffer.append(key_str)

            # Limit buffer size
            if len(self.buffer) > self.buffer_size:
                self.buffer.pop(0)

            # Update counts
            self.key_counts[key_str] += 1
            self.total_keystrokes += 1

            # Track combos with modifiers
            if self.current_modifiers:
                combo = '+'.join(sorted(self.current_modifiers)) + '+' + key_str
                self.combos[combo] += 1

            # Track bigrams and trigrams
            if len(self.keys) >= 2:
                bigram = self.keys[-2] + self.keys[-1]
                self.bigrams[bigram] += 1

                # Record transition timing
                if len(self.timestamps) >= 2:
                    timing_ms = (self.timestamps[-1] - self.timestamps[-2]) * 1000
                    finger1 = FingerMap.get_finger(self.keys[-2])
                    finger2 = FingerMap.get_finger(self.keys[-1])

                    self.transition_tracker.record_transition(
                        self.keys[-2],
                        self.keys[-1],
                        timing_ms,
                        finger1.value if finger1 else None,
                        finger2.value if finger2 else None
                    )

            if len(self.keys) >= 3:
                trigram = self.keys[-3] + self.keys[-2] + self.keys[-1]
                self.trigrams[trigram] += 1

            # Auto-save check
            if time.time() - self.last_save >= self.save_interval:
                self.save_data()

        except Exception as e:
            print(f"Error in on_press: {e}")

    def on_release(self, key):
        """Handle key release event"""
        try:
            key_str = self._normalize_key(key)

            # Remove from current modifiers
            if key_str.strip('[]') in self.current_modifiers:
                self.current_modifiers.remove(key_str.strip('[]'))

            # Check for escape to stop
            if key == keyboard.Key.esc:
                pass  # Don't auto-stop on ESC

        except Exception as e:
            print(f"Error in on_release: {e}")

    def start(self):
        """Start tracking keystrokes"""
        if self.running:
            print("Tracker is already running")
            return

        self.running = True
        print("Keystroke tracking started. Press Ctrl+C to stop.")
        print(f"Data will be saved to: {self.data_file}")

        # Start listener
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

        try:
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop tracking keystrokes"""
        if not self.running:
            return

        print("\nStopping keystroke tracking...")
        self.running = False

        if self.listener:
            self.listener.stop()

        # Final save
        self.save_data(force=True)

        # Print summary
        self.print_session_summary()

    def print_session_summary(self):
        """Print summary of current session"""
        print("\n" + "=" * 50)
        print("SESSION SUMMARY")
        print("=" * 50)
        print(f"Duration: {self.session_duration:.1f} seconds")
        print(f"Total keystrokes: {self.total_keystrokes}")
        print(f"Keys per second: {self.total_keystrokes / self.session_duration:.2f}")
        print(f"\nTop 10 keys:")
        for key, count in self.key_counts.most_common(10):
            print(f"  {key}: {count}")

        # Finger analysis
        finger_load = FingerMap.calculate_finger_load(dict(self.key_counts))
        print(f"\nFinger load (top 5):")
        sorted_fingers = sorted(finger_load.items(), key=lambda x: x[1], reverse=True)
        for finger, percentage in sorted_fingers[:5]:
            print(f"  {finger.value}: {percentage:.1f}%")

        print(f"\nSFB Rate: {FingerMap.calculate_sfb_rate(dict(self.bigrams)):.2f}%")
        print(f"Hand Alternation: {FingerMap.calculate_hand_alternation_rate(dict(self.bigrams)):.2f}%")

        print(f"\nData saved to: {self.data_file}")
        print("=" * 50)

    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            'session': {
                'duration': time.time() - self.session_start,
                'keystrokes': self.total_keystrokes,
                'keys_per_second': self.total_keystrokes / (time.time() - self.session_start),
            },
            'total': {
                'keystrokes': self.data['total_keystrokes'],
                'sessions': self.data['total_sessions'],
            },
            'top_keys': self.key_counts.most_common(20),
            'top_bigrams': self.bigrams.most_common(20),
            'finger_stats': self._calculate_finger_stats(),
            'timing': self.hesitation_detector.get_timing_stats(),
        }
