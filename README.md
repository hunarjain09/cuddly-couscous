# Keystroke Tracker - ZSA Voyager Layout Optimizer

**Version 2.0.0**

A comprehensive tool for tracking keystrokes and optimizing keyboard layouts based on your actual typing patterns. Specifically designed for the ZSA Voyager 52-key split ergonomic keyboard.

## 🎯 Features

- **Real-time Keystroke Tracking**: Captures every keystroke with timing information
- **Finger Usage Analysis**: Maps keys to fingers and calculates ergonomic metrics
- **Context Detection**: Automatically identifies Python, JavaScript, shell, and other contexts
- **Transition Analysis**: Identifies awkward key combinations and same-finger bigrams
- **Voyager Simulation**: Predicts layer switches and overhead on Voyager layout
- **Symbol Optimization**: Data-driven placement of symbols based on frequency
- **Macro Suggestions**: Identifies patterns worth converting to macros
- **Oryx Export**: Generates JSON files for ZSA Oryx configurator
- **Comprehensive Reports**: Beautiful terminal output and markdown reports

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Commands Reference](#commands-reference)
- [Project Structure](#project-structure)
- [Methodology](#methodology)
- [Contributing](#contributing)

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Permissions to capture keyboard input (may require sudo/admin)

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd cuddly-couscous

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Verify Installation

```bash
keystroke-tracker --version
```

## 🚀 Quick Start

### 1. Start Tracking

Begin collecting keystroke data:

```bash
keystroke-tracker start
```

Press `Ctrl+C` to stop tracking. Data is auto-saved every 60 seconds.

**Recommended**: Track for at least 1-2 weeks for accurate analysis.

### 2. View Statistics

```bash
keystroke-tracker stats
```

Shows:
- Total keystrokes
- Top keys and bigrams
- Session information

### 3. Analyze Finger Usage

```bash
keystroke-tracker finger-analysis
```

Displays:
- Finger load distribution
- Same-finger bigram (SFB) rate
- Hand alternation rate
- Ergonomic recommendations

### 4. Simulate on Voyager

```bash
keystroke-tracker voyager-simulate
```

Shows how many layer switches your typing would require on Voyager.

### 5. Optimize Layout

```bash
keystroke-tracker optimize-symbols --context python
```

Generates an optimized symbol layout based on your typing data.

### 6. Export to Oryx

```bash
keystroke-tracker export-oryx --output exports/layouts/my-layout.json
```

Creates a JSON file you can import into [ZSA Oryx](https://configure.zsa.io).

## 📖 Usage Guide

### Phase 1: Data Collection (Weeks 1-2)

**Goal**: Collect baseline typing data on your current keyboard.

```bash
# Start tracking
keystroke-tracker start

# Let it run during your normal work
# Stop when done: Ctrl+C

# Check progress
keystroke-tracker stats --top 50
```

**Best Practices**:
- Track for minimum 50,000 keystrokes (ideally 100,000+)
- Include diverse tasks: coding, documentation, terminal work
- Don't change your typing style - be natural

### Phase 2: Analysis (Week 3)

**Goal**: Understand your typing patterns.

```bash
# Overall statistics
keystroke-tracker stats

# Finger usage
keystroke-tracker finger-analysis

# Key transitions
keystroke-tracker transitions --threshold 100

# Python-specific analysis
keystroke-tracker python-analysis

# Voyager simulation
keystroke-tracker voyager-simulate

# Thumb key suggestions
keystroke-tracker thumb-candidates

# Macro opportunities
keystroke-tracker suggest-macros --min-frequency 50
```

### Phase 3: Optimization (Week 4)

**Goal**: Generate optimized layout.

```bash
# Optimize for Python
keystroke-tracker optimize-symbols --context python \
    --output exports/layout-rationale.md

# Generate cheatsheet
keystroke-tracker generate-cheatsheet \
    --output exports/layout-cheatsheet.md

# Export to Oryx format
keystroke-tracker export-oryx \
    --output exports/layouts/voyager-optimized-v1.json \
    --name "My Optimized Layout"

# Generate full report
keystroke-tracker export-report \
    --output exports/analysis-reports/full-report.md
```

### Phase 4: Migration (Weeks 5-8)

**Goal**: Switch to Voyager with optimized layout.

1. **Load layout into Oryx**
   - Go to https://configure.zsa.io
   - Import your JSON file
   - Review and customize
   - Flash to Voyager

2. **Start using Voyager**
   - Expect 50-70% speed reduction initially
   - Keep cheatsheet visible
   - Practice daily

3. **Track progress** (Optional)
   ```bash
   # Continue tracking with new keyboard
   keystroke-tracker start --data-file data/voyager-progress.json

   # Compare to baseline
   keystroke-tracker stats --data-file data/voyager-progress.json
   ```

## 📚 Commands Reference

### Data Collection

#### `start`
Start tracking keystrokes.

```bash
keystroke-tracker start [--data-file PATH]
```

Options:
- `--data-file`: Path to data file (default: `data/keystrokes.json`)

#### `stats`
Show keystroke statistics.

```bash
keystroke-tracker stats [--top N] [--data-file PATH]
```

Options:
- `--top`: Number of top items to show (default: 50)
- `--data-file`: Path to data file

### Analysis Commands

#### `finger-analysis`
Analyze finger usage and load distribution.

```bash
keystroke-tracker finger-analysis [--data-file PATH]
```

#### `transitions`
Analyze key-to-key transitions.

```bash
keystroke-tracker transitions [--threshold N] [--data-file PATH]
```

Options:
- `--threshold`: Minimum count to display (default: 100)

#### `python-analysis`
Analyze Python-specific typing patterns.

```bash
keystroke-tracker python-analysis [--data-file PATH]
```

### Voyager Commands

#### `voyager-simulate`
Simulate typing on Voyager keyboard.

```bash
keystroke-tracker voyager-simulate [--data-file PATH]
```

#### `thumb-candidates`
Suggest optimal thumb key assignments.

```bash
keystroke-tracker thumb-candidates [--top N] [--data-file PATH]
```

Options:
- `--top`: Number of candidates (default: 10)

### Optimization Commands

#### `optimize-symbols`
Optimize symbol placement.

```bash
keystroke-tracker optimize-symbols \
    [--context CONTEXT] \
    [--output PATH] \
    [--data-file PATH]
```

Options:
- `--context`: Programming context (python, javascript, etc.)
- `--output`: Output file for rationale

#### `suggest-macros`
Suggest macro candidates.

```bash
keystroke-tracker suggest-macros \
    [--min-frequency N] \
    [--output PATH] \
    [--data-file PATH]
```

Options:
- `--min-frequency`: Minimum frequency (default: 50)

#### `export-oryx`
Export to Oryx-compatible JSON.

```bash
keystroke-tracker export-oryx \
    [--context CONTEXT] \
    [--output PATH] \
    [--name NAME] \
    [--data-file PATH]
```

Options:
- `--context`: Programming context
- `--output`: Output JSON file
- `--name`: Layout name

#### `generate-cheatsheet`
Generate printable cheatsheet.

```bash
keystroke-tracker generate-cheatsheet \
    [--format FORMAT] \
    [--output PATH] \
    [--context CONTEXT] \
    [--data-file PATH]
```

Options:
- `--format`: markdown or text (default: markdown)

### Reporting Commands

#### `export-report`
Generate comprehensive report.

```bash
keystroke-tracker export-report \
    [--output PATH] \
    [--data-file PATH]
```

## 📁 Project Structure

```
keystroke-tracker/
├── keystroke_tracker/
│   ├── __init__.py
│   ├── cli.py                    # CLI interface
│   ├── tracker.py                # Core tracking
│   ├── analyzer.py               # Main analyzer
│   ├── detector.py               # Context detection
│   ├── utils/
│   │   ├── finger_map.py         # Finger mapping
│   │   ├── timing.py             # Timing analysis
│   │   └── patterns.py           # Pattern detection
│   ├── voyager/
│   │   ├── simulator.py          # Voyager simulation
│   │   ├── optimizer.py          # Layout optimization
│   │   └── exporter.py           # Oryx export
│   └── visualizers/
│       └── heatmap.py            # Heatmap generation
├── data/                         # Keystroke data (gitignored)
├── exports/                      # Exported layouts & reports
├── tests/                        # Unit tests
├── requirements.txt
├── setup.py
└── README.md
```

## 🧪 Methodology

### Ergonomic Metrics

**Same-Finger Bigram (SFB) Rate**
- Percentage of key pairs typed with the same finger
- Target: < 2%
- Lower is better

**Hand Alternation Rate**
- Percentage of key pairs alternating between hands
- Target: > 60%
- Higher is better

**Finger Load Distribution**
- Percentage of keystrokes per finger
- Should be balanced according to finger strength
- Index fingers should carry more load than pinkies

### Optimization Algorithm

1. **Frequency Analysis**: Count all key/symbol uses
2. **Pair Detection**: Identify symbols that appear together (e.g., `()`, `[]`)
3. **Position Scoring**: Rate positions by:
   - Row (home row = best)
   - Finger strength
   - Reach distance
4. **Assignment**:
   - Paired symbols → adjacent/mirrored positions
   - High-frequency singles → best available positions
   - Low-frequency → remaining positions

### Voyager Simulation

Estimates layer switching overhead by:
1. Mapping each character to its layer
2. Counting layer switches
3. Calculating time overhead (150ms per switch)
4. Generating efficiency score

Target: < 5 layer switches per 100 characters

## 🎯 Success Metrics

### Data Collection
- ✓ 50,000+ keystrokes tracked
- ✓ Multiple contexts captured (coding, terminal, docs)
- ✓ Representative of normal work

### Analysis
- ✓ SFB rate calculated
- ✓ Finger load balanced
- ✓ Common patterns identified

### Optimization
- ✓ Layout generated
- ✓ Rationale documented
- ✓ Oryx JSON created

### Migration
- ✓ WPM recovery > 80%
- ✓ Error rate < 2%
- ✓ Layer switches < 5 per 100 chars

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- ZSA Technology Labs for the Voyager keyboard
- QMK firmware community
- Ergonomic keyboard community (r/ErgoMechKeyboards)

## 📞 Support

For issues, questions, or suggestions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: This README and generated reports
- Community: r/ErgoMechKeyboards, ZSA Discord

---

**Good luck with your Voyager optimization journey!** 🎹⌨️

Remember: The best layout is one that fits YOUR typing patterns. This tool helps you discover what that is.
