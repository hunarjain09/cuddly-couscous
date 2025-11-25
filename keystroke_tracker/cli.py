"""
CLI interface for keystroke tracker
Main entry point for all commands
"""

import click
import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from keystroke_tracker.tracker import KeystrokeTracker
from keystroke_tracker.analyzer import KeystrokeAnalyzer


console = Console()


@click.group()
@click.version_option(version='2.0.0')
def cli():
    """
    Keystroke Tracker - ZSA Voyager Layout Optimizer

    A comprehensive tool for tracking keystrokes and optimizing keyboard layouts
    based on your actual typing patterns.
    """
    pass


# ==============================================================================
# Phase 1: Data Collection Commands
# ==============================================================================

@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
def start(data_file):
    """Start tracking keystrokes"""
    console.print("[bold green]Starting keystroke tracker...[/bold green]")
    tracker = KeystrokeTracker(data_file=data_file)

    try:
        tracker.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Tracking stopped by user[/yellow]")
        tracker.stop()


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--top', default=50, help='Number of top items to show')
def stats(data_file, top):
    """Show keystroke statistics"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)
        summary = analyzer.get_summary_stats()

        console.print(f"\n[bold]Keystroke Statistics[/bold]")
        console.print(f"Total Keystrokes: {summary['total_keystrokes']:,}")
        console.print(f"Sessions: {summary['total_sessions']}")
        console.print(f"Unique Keys: {summary['unique_keys']}")

        # Top keys table
        table = Table(title=f"\nTop {min(top, len(summary['most_common_keys']))} Keys")
        table.add_column("Rank", style="cyan")
        table.add_column("Key", style="magenta")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")

        total = summary['total_keystrokes']
        for i, (key, count) in enumerate(summary['most_common_keys'][:top], 1):
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(str(i), key, f"{count:,}", f"{pct:.2f}%")

        console.print(table)

        # Top bigrams
        if summary['most_common_bigrams']:
            table2 = Table(title="\nTop 20 Bigrams")
            table2.add_column("Rank", style="cyan")
            table2.add_column("Bigram", style="magenta")
            table2.add_column("Count", style="green")

            for i, (bigram, count) in enumerate(summary['most_common_bigrams'][:20], 1):
                table2.add_row(str(i), bigram, f"{count:,}")

            console.print(table2)

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")
        console.print("[yellow]Start tracking with: keystroke-tracker start[/yellow]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
def finger_analysis(data_file):
    """Analyze finger usage and load distribution"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)
        analysis = analyzer.analyze_finger_usage()

        console.print("\n[bold]Finger Usage Analysis[/bold]\n")

        # Finger load table
        table = Table(title="Finger Load Distribution")
        table.add_column("Finger", style="cyan")
        table.add_column("Load %", style="green")
        table.add_column("Bar", style="yellow")

        finger_load = analysis['finger_load']
        sorted_fingers = sorted(finger_load.items(), key=lambda x: x[1], reverse=True)

        for finger, load in sorted_fingers:
            bar = '█' * int(load / 2)  # Scale for display
            table.add_row(finger, f"{load:.2f}%", bar)

        console.print(table)

        # Metrics
        console.print(f"\n[bold]Ergonomic Metrics:[/bold]")
        console.print(f"  SFB Rate: [{'green' if analysis['sfb_rate'] < 2 else 'red'}]{analysis['sfb_rate']:.2f}%[/] (target: <2%)")
        console.print(f"  Hand Alternation: [{'green' if analysis['hand_alternation_rate'] > 60 else 'yellow'}]{analysis['hand_alternation_rate']:.2f}%[/] (target: >60%)")
        console.print(f"  Overall Score: [bold]{analysis['assessment']['overall_score']:.1f}/100[/bold]")

        # Issues and recommendations
        if analysis['assessment']['issues']:
            console.print("\n[bold red]Issues:[/bold red]")
            for issue in analysis['assessment']['issues']:
                console.print(f"  • {issue}")

        if analysis['assessment']['recommendations']:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in analysis['assessment']['recommendations']:
                console.print(f"  • {rec}")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--threshold', default=100, help='Minimum count to display')
def transitions(data_file, threshold):
    """Analyze key transitions"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)
        analysis = analyzer.analyze_transitions(top_n=50)

        # Top transitions
        table = Table(title="Top Key Transitions")
        table.add_column("Transition", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Comfort", style="yellow")

        for trans in analysis['top_transitions'][:20]:
            if trans['count'] >= threshold:
                comfort = trans['comfort_score']
                comfort_color = 'green' if comfort > 70 else 'yellow' if comfort > 40 else 'red'
                table.add_row(
                    trans['transition'],
                    f"{trans['count']:,}",
                    f"[{comfort_color}]{comfort:.1f}[/]"
                )

        console.print(table)

        # Awkward transitions
        if analysis['awkward_transitions']:
            console.print("\n[bold red]Awkward Transitions (Low Comfort):[/bold red]\n")
            for trans in analysis['awkward_transitions'][:10]:
                console.print(f"  • {trans['transition']}: {trans['reason']} ({trans['count']} times)")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
def python_analysis(data_file):
    """Analyze Python-specific typing patterns"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)
        analysis = analyzer.analyze_python_usage()

        console.print("\n[bold]Python Typing Analysis[/bold]\n")

        symbol_analysis = analysis['symbol_analysis']

        # Priority analysis
        console.print("[bold]Symbol Priority Analysis:[/bold]")
        for priority, data in symbol_analysis['priority_analysis'].items():
            console.print(f"\n  {priority.replace('_', ' ').title()}: {data['count']} uses")
            if data['symbols']:
                top_symbols = sorted(data['symbols'].items(), key=lambda x: x[1], reverse=True)[:5]
                for sym, count in top_symbols:
                    console.print(f"    • {sym}: {count}")

        console.print(f"\n[bold]Priority Ratio:[/bold] {symbol_analysis['priority_ratio']:.1f}%")
        console.print("(Percentage of symbols that are priority 1 - should be on home row)")

        # Recommendations
        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for rec in analysis['recommendations']:
            console.print(f"  • {rec}")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


# ==============================================================================
# Phase 2: Voyager Analysis Commands
# ==============================================================================

@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
def voyager_simulate(data_file):
    """Simulate typing on Voyager keyboard"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)
        simulation = analyzer.simulate_voyager()

        if 'error' in simulation:
            console.print(f"[red]Error: {simulation['error']}[/red]")
            return

        console.print("\n[bold]Voyager Simulation Results[/bold]\n")

        console.print(f"Characters Typed: {simulation['chars_typed']:,}")
        console.print(f"Layer Switches: {simulation['layer_switches']:,}")
        console.print(f"Switches per 100 chars: [bold]{simulation['switches_per_100_chars']:.2f}[/bold] (target: <5)")
        console.print(f"Overhead: {simulation['overhead_ms']:,.0f} ms ({simulation['overhead_per_char_ms']:.1f} ms/char)")

        # Efficiency
        score = simulation['efficiency_score']
        score_color = 'green' if score > 80 else 'yellow' if score > 60 else 'red'
        console.print(f"\nEfficiency Score: [{score_color}]{score:.1f}/100[/]")
        console.print(f"Meets Target: [{'green' if simulation['meets_target'] else 'red'}]{'✓' if simulation['meets_target'] else '✗'}[/]")

        # Layer distribution
        if 'layer_distribution' in simulation:
            console.print("\n[bold]Layer Distribution:[/bold]")
            for layer, pct in sorted(simulation['layer_distribution'].items()):
                bar = '█' * int(pct / 2)
                console.print(f"  Layer {layer}: {pct:5.1f}% {bar}")

        # Recommendations
        if simulation.get('recommendations'):
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in simulation['recommendations']:
                console.print(f"  • {rec}")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--top', default=10, help='Number of candidates to show')
def thumb_candidates(data_file, top):
    """Suggest optimal thumb key assignments"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)
        candidates = analyzer.suggest_thumb_keys()

        console.print("\n[bold]Thumb Key Candidates[/bold]\n")
        console.print("These keys are used frequently and would benefit from thumb placement:\n")

        table = Table()
        table.add_column("Rank", style="cyan")
        table.add_column("Key", style="magenta")
        table.add_column("Frequency", style="green")
        table.add_column("Reason", style="yellow")

        for i, candidate in enumerate(candidates[:top], 1):
            table.add_row(
                str(i),
                candidate['key'],
                f"{candidate['frequency']:,}",
                candidate['reason']
            )

        console.print(table)

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


# ==============================================================================
# Phase 3: Optimization Commands
# ==============================================================================

@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--context', default='python', help='Programming context (python, javascript, etc.)')
@click.option('--output', default='exports/layout-rationale.md', help='Output file for rationale')
def optimize_symbols(data_file, context, output):
    """Optimize symbol placement for Voyager layout"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)

        console.print(f"\n[bold]Optimizing layout for {context}...[/bold]\n")

        result = analyzer.optimize_layout(context=context)
        assignments = result['assignments']

        # Display top assignments
        table = Table(title=f"Optimized Symbol Placement (Top 20)")
        table.add_column("Key", style="cyan")
        table.add_column("Position", style="magenta")
        table.add_column("Finger", style="yellow")
        table.add_column("Frequency", style="green")
        table.add_column("Score", style="blue")

        for assignment in assignments[:20]:
            table.add_row(
                assignment['key'],
                f"({assignment['position'][0]},{assignment['position'][1]})",
                assignment['finger'],
                f"{assignment['frequency']:,}",
                f"{assignment['score']:.0f}"
            )

        console.print(table)

        # Save rationale
        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, 'w') as f:
            f.write(result['rationale'])

        console.print(f"\n[green]Layout rationale saved to: {output}[/green]")
        console.print(f"Total symbols optimized: {len(assignments)}")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--min-frequency', default=50, help='Minimum frequency for macro suggestion')
@click.option('--output', default=None, help='Output file for macro suggestions')
def suggest_macros(data_file, min_frequency, output):
    """Suggest macro candidates based on frequency"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)

        # Get keystroke data
        with open(data_file, 'r') as f:
            data = json.load(f)

        # Reconstruct key list
        keys = []
        for key, count in data.get('keys', {}).items():
            keys.extend([key] * min(count, 100))

        # Use pattern detector
        from keystroke_tracker.utils.patterns import PatternDetector
        detector = PatternDetector()
        suggestions = detector.suggest_macros(keys, threshold=min_frequency)

        if not suggestions:
            console.print(f"[yellow]No patterns found with frequency >= {min_frequency}[/yellow]")
            return

        console.print("\n[bold]Macro Suggestions[/bold]\n")
        console.print(f"Patterns with frequency >= {min_frequency}:\n")

        table = Table()
        table.add_column("Rank", style="cyan")
        table.add_column("Pattern", style="magenta")
        table.add_column("Frequency", style="green")
        table.add_column("Keystrokes Saved", style="yellow")
        table.add_column("Recommended", style="blue")

        for i, suggestion in enumerate(suggestions[:20], 1):
            table.add_row(
                str(i),
                suggestion['pattern'],
                f"{suggestion['frequency']}",
                f"{suggestion['keystrokes_saved']}",
                '✓' if suggestion['recommended'] else ''
            )

        console.print(table)

        # Save if requested
        if output:
            os.makedirs(os.path.dirname(output), exist_ok=True)
            with open(output, 'w') as f:
                json.dump(suggestions, f, indent=2)
            console.print(f"\n[green]Macro suggestions saved to: {output}[/green]")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--context', default='python', help='Programming context')
@click.option('--output', default='exports/layouts/voyager-optimized.json', help='Output Oryx JSON file')
@click.option('--name', default='Optimized Layout', help='Layout name')
def export_oryx(data_file, context, output, name):
    """Export optimized layout to Oryx-compatible JSON"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)

        console.print(f"\n[bold]Generating Oryx layout...[/bold]\n")

        # Optimize layout
        result = analyzer.optimize_layout(context=context)
        assignments = result['assignments']

        # Export to Oryx
        os.makedirs(os.path.dirname(output), exist_ok=True)
        output_path = analyzer.export_to_oryx(assignments, output, layout_name=name)

        console.print(f"[green]✓ Oryx layout exported to: {output_path}[/green]")
        console.print(f"\nNext steps:")
        console.print("  1. Go to https://configure.zsa.io")
        console.print("  2. Import the JSON file")
        console.print("  3. Review and customize if needed")
        console.print("  4. Flash to your Voyager")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--context', default='python', help='Programming context')
@click.option('--output', default='exports/layout-cheatsheet.md', help='Output file')
@click.option('--format', default='markdown', type=click.Choice(['markdown', 'text']))
def generate_cheatsheet(data_file, context, output, format):
    """Generate printable layout cheatsheet"""
    try:
        from keystroke_tracker.voyager.exporter import OryxExporter

        analyzer = KeystrokeAnalyzer(data_file)

        console.print(f"\n[bold]Generating cheatsheet...[/bold]\n")

        # Optimize layout
        result = analyzer.optimize_layout(context=context)

        # Convert to KeyAssignment objects
        from keystroke_tracker.voyager.optimizer import KeyAssignment
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
            for a in result['assignments']
        ]

        # Generate cheatsheet
        exporter = OryxExporter(layout_name="Optimized Layout")
        cheatsheet = exporter.generate_cheatsheet(assignments, output_format=format)

        # Save
        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, 'w') as f:
            f.write(cheatsheet)

        console.print(f"[green]✓ Cheatsheet saved to: {output}[/green]")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


# ==============================================================================
# Reporting Commands
# ==============================================================================

@cli.command()
@click.option('--data-file', default='data/keystrokes.json', help='Data file path')
@click.option('--output', default='exports/analysis-reports/full-report.md', help='Output file')
def export_report(data_file, output):
    """Generate comprehensive analysis report"""
    try:
        analyzer = KeystrokeAnalyzer(data_file)

        console.print("\n[bold]Generating comprehensive report...[/bold]\n")

        os.makedirs(os.path.dirname(output), exist_ok=True)
        report = analyzer.generate_report(output_file=output)

        console.print(f"[green]✓ Report generated: {output}[/green]")
        console.print("\nReport includes:")
        console.print("  • Summary statistics")
        console.print("  • Finger usage analysis")
        console.print("  • Voyager simulation")
        console.print("  • Thumb key recommendations")
        console.print("  • Optimization suggestions")

    except FileNotFoundError:
        console.print(f"[red]Error: Data file not found: {data_file}[/red]")


if __name__ == '__main__':
    cli()
