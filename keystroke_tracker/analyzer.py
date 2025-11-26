"""
Main analyzer module
Provides high-level analysis functions combining all components
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

from keystroke_tracker.utils.finger_map import FingerMap
from keystroke_tracker.utils.timing import HesitationDetector, TransitionTracker
from keystroke_tracker.utils.patterns import PatternDetector, PythonAnalyzer
from keystroke_tracker.detector import ContextDetector, Context
from keystroke_tracker.voyager.simulator import VoyagerSimulator, ThumbKeyAnalyzer
from keystroke_tracker.voyager.optimizer import SymbolOptimizer
from keystroke_tracker.voyager.exporter import OryxExporter


class KeystrokeAnalyzer:
    """Main analyzer class that combines all analysis components"""

    def __init__(self, data_file: str):
        """
        Initialize analyzer

        Args:
            data_file: Path to keystroke data JSON file
        """
        self.data_file = data_file
        self.data = self._load_data()

        # Initialize analyzers
        self.pattern_detector = PatternDetector()
        self.context_detector = ContextDetector()

    def _load_data(self) -> Dict:
        """Load keystroke data from file"""
        if not Path(self.data_file).exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        with open(self.data_file, 'r') as f:
            return json.load(f)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        keys = self.data.get('keys', {})
        bigrams = self.data.get('bigrams', {})
        combos = self.data.get('combos', {})

        total_keys = sum(keys.values()) if keys else 0

        return {
            'total_keystrokes': self.data.get('total_keystrokes', 0),
            'total_sessions': self.data.get('total_sessions', 0),
            'unique_keys': len(keys),
            'unique_bigrams': len(bigrams),
            'unique_combos': len(combos),
            'most_common_keys': sorted(keys.items(), key=lambda x: x[1], reverse=True)[:20],
            'most_common_bigrams': sorted(bigrams.items(), key=lambda x: x[1], reverse=True)[:20],
        }

    def analyze_finger_usage(self) -> Dict:
        """Analyze finger load distribution"""
        keys = self.data.get('keys', {})
        bigrams = self.data.get('bigrams', {})

        # Calculate finger load
        finger_load = FingerMap.calculate_finger_load(keys)

        # Calculate SFB rate
        sfb_rate = FingerMap.calculate_sfb_rate(bigrams)

        # Calculate hand alternation
        hand_alt = FingerMap.calculate_hand_alternation_rate(bigrams)

        # Find most overused fingers
        sorted_fingers = sorted(finger_load.items(), key=lambda x: x[1], reverse=True)

        return {
            'finger_load': {f.value: load for f, load in finger_load.items()},
            'sfb_rate': sfb_rate,
            'hand_alternation_rate': hand_alt,
            'most_used_fingers': [(f.value, load) for f, load in sorted_fingers[:5]],
            'least_used_fingers': [(f.value, load) for f, load in sorted_fingers[-5:]],
            'assessment': self._assess_finger_usage(sfb_rate, hand_alt, sorted_fingers),
        }

    def _assess_finger_usage(self, sfb_rate: float, hand_alt: float, finger_loads: List) -> Dict:
        """Assess finger usage and provide recommendations"""
        issues = []
        recommendations = []

        # Check SFB rate
        if sfb_rate > 2.0:
            issues.append(f"High same-finger bigram rate: {sfb_rate:.2f}% (target: <2%)")
            recommendations.append("Consider reorganizing common bigrams to use different fingers")

        # Check hand alternation
        if hand_alt < 60:
            issues.append(f"Low hand alternation: {hand_alt:.2f}% (target: >60%)")
            recommendations.append("Move frequently used keys to alternate between hands")

        # Check finger balance
        if finger_loads:
            max_load = finger_loads[0][1]
            min_load = finger_loads[-1][1]
            if max_load > 20 and max_load / max(min_load, 0.1) > 5:
                issues.append(f"Unbalanced finger usage: {finger_loads[0][0].value} is overused")
                recommendations.append(f"Redistribute load from {finger_loads[0][0].value}")

        return {
            'issues': issues,
            'recommendations': recommendations,
            'overall_score': self._calculate_ergonomic_score(sfb_rate, hand_alt),
        }

    def _calculate_ergonomic_score(self, sfb_rate: float, hand_alt: float) -> float:
        """Calculate overall ergonomic score (0-100)"""
        score = 100

        # Penalize high SFB rate
        if sfb_rate > 2.0:
            score -= (sfb_rate - 2.0) * 10

        # Penalize low hand alternation
        if hand_alt < 60:
            score -= (60 - hand_alt) * 0.5

        return max(0, min(100, score))

    def analyze_transitions(self, top_n: int = 50) -> Dict:
        """Analyze key transitions"""
        bigrams = self.data.get('bigrams', {})

        # Reconstruct transition tracker
        tracker = TransitionTracker()

        for bigram, count in bigrams.items():
            if len(bigram) >= 2:
                # Estimate timing (we don't have actual timing data here)
                avg_timing = 150  # Default
                tracker.transitions[f"{bigram[0]}→{bigram[1]}"] = {
                    'count': count,
                    'total_timing': avg_timing * count,
                    'avg_timing': avg_timing,
                    'min_timing': avg_timing,
                    'max_timing': avg_timing,
                }

        top_transitions = tracker.get_top_transitions(top_n)
        awkward_transitions = tracker.get_awkward_transitions(min_count=10)

        return {
            'top_transitions': [
                {
                    'transition': trans,
                    'count': data['count'],
                    'avg_timing_ms': data['avg_timing'],
                    'comfort_score': tracker.calculate_comfort_score(*trans.split('→'))
                }
                for trans, data in top_transitions
            ],
            'awkward_transitions': [
                {
                    'transition': trans,
                    'count': data['count'],
                    'comfort_score': data.get('comfort_score', 0),
                    'reason': self._explain_awkwardness(trans)
                }
                for trans, data in awkward_transitions[:20]
            ],
        }

    def _explain_awkwardness(self, transition: str) -> str:
        """Explain why a transition is awkward"""
        if '→' not in transition:
            return "Unknown"

        key1, key2 = transition.split('→')

        if FingerMap.is_same_finger_bigram(key1, key2):
            return "Same finger bigram"

        row_jump = FingerMap.calculate_row_jump(key1, key2)
        if row_jump >= 2:
            return f"Large row jump ({row_jump} rows)"

        return "Uncomfortable reach"

    def analyze_python_usage(self) -> Dict:
        """Analyze Python-specific typing patterns"""
        keys_list = []

        # Reconstruct key sequence from bigrams/trigrams
        # This is an approximation
        keys = self.data.get('keys', {})
        for key, count in keys.items():
            keys_list.extend([key] * min(count, 100))

        # Analyze symbols
        symbol_analysis = PythonAnalyzer.analyze_python_symbols(keys_list)

        # Detect patterns if we have text
        patterns = {}
        if 'sessions' in self.data:
            for session_data in self.data['sessions'].values():
                if 'keys' in session_data:
                    session_keys = session_data['keys']
                    # This would need actual text to work properly
                    # For now, just analyze symbol usage

        return {
            'symbol_analysis': symbol_analysis,
            'recommendations': [
                "Place priority 1 symbols on home row",
                "Use thumbs for high-frequency brackets",
                "Consider macros for common patterns like 'def ', 'import '",
            ]
        }

    def simulate_voyager(self) -> Dict:
        """Simulate typing on Voyager keyboard"""
        simulator = VoyagerSimulator()
        analysis = simulator.analyze_layer_efficiency(self.data)

        return analysis

    def suggest_thumb_keys(self) -> List[Dict]:
        """Suggest optimal thumb key assignments"""
        return ThumbKeyAnalyzer.analyze_thumb_candidates(self.data, top_n=10)

    def optimize_layout(self, context: str = 'python') -> Dict:
        """
        Generate optimized layout

        Args:
            context: Programming context

        Returns:
            Dict with optimized assignments and metadata
        """
        optimizer = SymbolOptimizer(self.data, context=context)
        assignments = optimizer.optimize_symbols(layer=0)

        # Generate rationale
        rationale = optimizer.generate_layout_rationale(assignments)

        return {
            'assignments': [
                {
                    'key': a.key,
                    'position': a.position,
                    'layer': a.layer,
                    'finger': a.finger,
                    'frequency': a.frequency,
                    'score': a.score,
                    'reason': a.reason,
                }
                for a in assignments
            ],
            'rationale': rationale,
            'context': context,
        }

    def export_to_oryx(
        self,
        assignments: List,
        output_file: str,
        layout_name: str = "Optimized Layout"
    ) -> str:
        """
        Export layout to Oryx format

        Args:
            assignments: List of key assignments from optimizer
            output_file: Output file path
            layout_name: Name for the layout

        Returns:
            Path to exported file
        """
        exporter = OryxExporter(layout_name=layout_name)

        # Convert assignment dicts back to objects if needed
        from keystroke_tracker.voyager.optimizer import KeyAssignment

        if assignments and isinstance(assignments[0], dict):
            assignments = [
                KeyAssignment(
                    key=a['key'],
                    position=tuple(a['position']),
                    layer=a['layer'],
                    finger=a['finger'],
                    reach_difficulty=0,
                    frequency=a['frequency'],
                    score=a['score'],
                    reason=a['reason'],
                )
                for a in assignments
            ]

        exporter.export_layout(assignments, output_file=output_file)
        return output_file

    def generate_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive analysis report

        Args:
            output_file: Optional file to save report

        Returns:
            Report as markdown string
        """
        report = "# Keystroke Analysis Report\n\n"

        # Summary
        report += "## Summary\n\n"
        summary = self.get_summary_stats()
        report += f"- **Total Keystrokes**: {summary['total_keystrokes']:,}\n"
        report += f"- **Sessions**: {summary['total_sessions']}\n"
        report += f"- **Unique Keys**: {summary['unique_keys']}\n"
        report += f"- **Unique Bigrams**: {summary['unique_bigrams']}\n\n"

        # Top keys
        report += "### Top 10 Keys\n\n"
        for key, count in summary['most_common_keys'][:10]:
            report += f"- `{key}`: {count:,}\n"
        report += "\n"

        # Finger analysis
        report += "## Finger Analysis\n\n"
        finger_analysis = self.analyze_finger_usage()
        report += f"- **SFB Rate**: {finger_analysis['sfb_rate']:.2f}%\n"
        report += f"- **Hand Alternation**: {finger_analysis['hand_alternation_rate']:.2f}%\n"
        report += f"- **Ergonomic Score**: {finger_analysis['assessment']['overall_score']:.1f}/100\n\n"

        if finger_analysis['assessment']['issues']:
            report += "### Issues\n\n"
            for issue in finger_analysis['assessment']['issues']:
                report += f"- {issue}\n"
            report += "\n"

        if finger_analysis['assessment']['recommendations']:
            report += "### Recommendations\n\n"
            for rec in finger_analysis['assessment']['recommendations']:
                report += f"- {rec}\n"
            report += "\n"

        # Voyager simulation
        report += "## Voyager Simulation\n\n"
        voyager_sim = self.simulate_voyager()
        if 'error' not in voyager_sim:
            report += f"- **Layer Switches per 100 chars**: {voyager_sim['switches_per_100_chars']:.2f}\n"
            report += f"- **Efficiency Score**: {voyager_sim['efficiency_score']:.1f}/100\n"
            report += f"- **Meets Target**: {'✓' if voyager_sim['meets_target'] else '✗'}\n\n"

            if voyager_sim.get('recommendations'):
                report += "### Recommendations\n\n"
                for rec in voyager_sim['recommendations']:
                    report += f"- {rec}\n"
                report += "\n"

        # Thumb key suggestions
        report += "## Thumb Key Candidates\n\n"
        thumb_keys = self.suggest_thumb_keys()
        for i, candidate in enumerate(thumb_keys[:5], 1):
            report += f"{i}. **{candidate['key']}**: {candidate['frequency']} uses - {candidate['reason']}\n"
        report += "\n"

        # Save if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_file}")

        return report
