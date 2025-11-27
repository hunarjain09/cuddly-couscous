# kstrk — Keystroke Tracker CLI

> A minimalist CLI binary for macOS that tracks keystrokes, generates heatmaps, and tokenizes input patterns.

**Inspired by**:
- [jpv-os/Keylogger](https://github.com/jpv-os/Keylogger) — IntelliJ plugin with APM tracking, milestones, ignore lists
- [selfspy/selfspy](https://github.com/selfspy/selfspy) — Battle-tested activity monitor with privacy-focused design

## Philosophy

Following Unix philosophy: **do one thing well**. Track keystrokes with clarity over cleverness, data-driven design, and progressive refinement.

## Features

- **Real-time APM Tracking** — Monitor Actions Per Minute and Keys Per Second
- **Milestone System** — Gamified achievement tracking (First Thousand, Millionaire, Legend, etc.)
- **Keyboard Heatmaps** — Visualize your most-used keys (ASCII and TUI modes)
- **Privacy-First** — Option to store only counts, not actual keystrokes (`--no-text`)
- **Process Context** — Track which applications you type in most
- **Tokenization** — Simple space and time-based token detection
- **Streak Tracking** — Daily activity streaks for motivation
- **Query Engine** — Powerful queries inspired by selfspy's `selfstats`

## Requirements

- **macOS only** (uses `CGEventTap` for keyboard monitoring)
- Rust 1.70+ (for building from source)
- Accessibility permissions (required for keyboard monitoring)

## Installation

### From Source

```bash
git clone https://github.com/hunarjain09/cuddly-couscous.git
cd cuddly-couscous
cargo build --release
cp target/release/kstrk /usr/local/bin/
```

## Quick Start

### 1. Grant Accessibility Permissions

On first run, kstrk will request accessibility permissions:

```bash
kstrk start
```

This opens System Settings → Privacy & Security → Accessibility. Grant permission and run the command again.

### 2. Start Tracking

```bash
# Run in foreground (recommended for testing)
kstrk start --foreground

# Press Ctrl+C to stop
```

### 3. View Stats

```bash
# Check status
kstrk status

# View keyboard heatmap
kstrk heatmap --ascii

# Show statistics
kstrk stats

# View milestones
kstrk milestones
```

## Usage

### Starting the Tracker

```bash
# Start in foreground
kstrk start --foreground

# Customize tokenization gap threshold
kstrk start --gap-threshold 1000

# Privacy mode (no keystroke text, only counts)
kstrk start --no-text
```

### Viewing Stats

```bash
# Show current status
kstrk status

# Live watch mode (updates every second)
kstrk watch

# Show heatmap
kstrk heatmap --ascii
kstrk heatmap --range week

# Show statistics
kstrk stats
kstrk stats --range today

# Show milestones
kstrk milestones
```

### Query Data (selfspy-inspired)

```bash
# Show keystrokes by process
kstrk query by-process

# Show keystrokes by window
kstrk query by-window -P "VSCode"

# Show typing activity in specific window
kstrk query by-window -T "main.rs"

# Show key frequency distribution
kstrk query key-freqs --human-readable
```

### Configuration

```bash
# Show config file path
kstrk config path

# Edit config
kstrk config edit

# Show current config
kstrk config show

# Reset to defaults
kstrk config reset
```

### Export Data

```bash
# Export to JSON
kstrk export -o ~/keystrokes.json

# Export to CSV
kstrk export -o ~/keystrokes.csv --format csv
```

## Configuration File

Located at `~/.config/kstrk/config.toml`:

```toml
[capture]
# Ignore specific keys
ignore_keys = ["CapsLock", "NumLock", "ScrollLock"]

# Ignore modifier-only keypresses
ignore_lone_modifiers = true

# Minimum gap (ms) to consider as "pause" for tokenization
token_gap_threshold = 500

[stats]
# APM window size in seconds
apm_window_secs = 60

# Enable milestone notifications
milestones_enabled = true

[storage]
# Retention: how long to keep detailed data (days)
retention_days = 365

# Aggregate older data to daily summaries
aggregate_after_days = 30

[heatmap]
# Color scheme: "heat" (red-yellow), "viridis", "cool"
color_scheme = "heat"

# Show key labels on heatmap
show_labels = true
```

## Example Output

### Status

```
$ kstrk status
╭─────────────────────────────────────────╮
│ kstrk — Keystroke Tracker               │
├─────────────────────────────────────────┤
│ Status:    ● Running (PID 12345)        │
│ Session:   2h 34m                        │
│ APM:       87.3 (current)                │
│ Today:     15,234 keystrokes             │
│ All-time:  1,234,567 keystrokes          │
│ Streak:    🔥 12 days                    │
╰─────────────────────────────────────────╯
```

### Heatmap

```
$ kstrk heatmap --ascii
Keyboard Heatmap (today)

░  1  2  3  4  5  6  7  8  9  0  -  =
░  ░  ▒  ▒  ▓  ░  ░  ░  ▒  ░  ░  ░  ░
░  ░  █  ░  ▓  ░  ░  █  ▓  ░  ░  ░  ░
█  █  ▒  ░  ░  ▒  ░  ░  ░  ░  ░
░  ░  ▒  ░  ░  ░  ░  ░  ░  ░
████████████████████

Legend: ░ low  ▒ medium  ▓ high  █ very high
```

### Milestones

```
$ kstrk milestones
🏆 Milestones
─────────────────────────────────
✓ 🎯 First Thousand     —           1,000
✓ 🎖️ Ten Thousand Club  —          10,000
✓ 💯 Centurion          —         100,000
✓ 🏆 Millionaire        —       1,000,000
○ 👑 Legend             —      10,000,000 (need 8,765,433 more)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI Layer                              │
│  (clap: start/stop/status/heatmap/stats/export)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  Capture  │   │  Storage  │   │ Visualize │
        │  Module   │   │  Module   │   │  Module   │
        └───────────┘   └───────────┘   └───────────┘
              │               │               │
              ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │CGEventTap │   │  SQLite   │   │ Ratatui   │
        │(core-gfx) │   │  + JSON   │   │ Heatmap   │
        └───────────┘   └───────────┘   └───────────┘
```

## Data Storage

All data is stored locally:

- **Database**: `~/.local/share/kstrk/kstrk.db` (SQLite)
- **Config**: `~/.config/kstrk/config.toml`
- **Lock file**: `~/.local/share/kstrk/kstrk.lock` (prevents duplicate instances)

### Database Schema

```sql
-- Process tracking
CREATE TABLE processes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Window context
CREATE TABLE windows (
    id INTEGER PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id),
    title TEXT NOT NULL,
    UNIQUE(process_id, title)
);

-- Keystroke records
CREATE TABLE keys (
    id INTEGER PRIMARY KEY,
    window_id INTEGER NOT NULL REFERENCES windows(id),
    created_at TIMESTAMP NOT NULL,
    key_text TEXT,              -- Optional (encrypted)
    key_count INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL
);

-- Hourly aggregates for heatmaps
CREATE TABLE hourly_stats (
    id INTEGER PRIMARY KEY,
    hour_bucket INTEGER NOT NULL,
    key_type TEXT NOT NULL,
    count INTEGER NOT NULL,
    UNIQUE(hour_bucket, key_type)
);
```

## Privacy & Security

1. **Local only** — All data stored locally, never sent anywhere
2. **No text mode** — Use `--no-text` to store only counts, not keystrokes
3. **Clear data** — Delete database to remove all tracked data
4. **Encryption** — Optional password protection for keystroke data (TODO)

## Development

### Project Structure

```
kstrk/
├── src/
│   ├── capture/        # Keyboard event capture (CGEventTap)
│   ├── storage/        # SQLite persistence
│   ├── stats/          # APM, milestones, live stats
│   ├── tokenize/       # Token detection
│   ├── viz/            # Heatmaps and visualizations
│   ├── cli/            # Command-line interface
│   ├── daemon/         # Background daemon + IPC
│   ├── config/         # Configuration management
│   └── query/          # Query engine (selfstats-inspired)
├── tests/              # Integration tests
└── resources/          # launchd templates, etc.
```

### Running Tests

```bash
# Run all tests
cargo test

# Run specific test
cargo test test_keycode_mapping

# Run with output
cargo test -- --nocapture
```

### Building

```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Run without installing
cargo run -- start --foreground
```

## Roadmap

### Phase 1: Core Capture (MVP) ✅
- [x] Basic CGEventTap setup
- [x] Keycode mapping
- [x] Accessibility permission check

### Phase 2: Storage ✅
- [x] SQLite schema
- [x] Hourly aggregation
- [x] Process/window tracking

### Phase 3: CLI ✅
- [x] clap structure
- [x] start/stop/status commands
- [x] Daemon mode

### Phase 4: Visualization ✅
- [x] ASCII heatmap
- [ ] Ratatui TUI heatmap (TODO)

### Phase 5: Tokenization ✅
- [x] Space-based splitting
- [x] Time-based splitting
- [x] Code detection heuristics

### Phase 6: Polish (TODO)
- [ ] Full IPC implementation
- [ ] Window title tracking (macOS)
- [ ] Export to CSV/JSON
- [ ] Advanced query filters
- [ ] Encryption for keystroke data
- [ ] launchd service integration

## Troubleshooting

### Accessibility Permission Issues

If kstrk can't capture keystrokes:

1. Go to: System Settings → Privacy & Security → Accessibility
2. Add your terminal app (Terminal.app, iTerm2, etc.)
3. Restart kstrk

### "Already Running" Error

If you see a lock file error:

```bash
# Check if kstrk is actually running
ps aux | grep kstrk

# If not running, remove stale lock file
rm ~/.local/share/kstrk/kstrk.lock
```

### Build Errors on Non-macOS

This project **only builds on macOS** due to Apple-specific frameworks. If you're on Linux/Windows, you'll see `core-graphics` link errors — this is expected.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `cargo test` passes
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [jpv-os/Keylogger](https://github.com/jpv-os/Keylogger) — Inspiration for APM tracking and milestones
- [selfspy/selfspy](https://github.com/selfspy/selfspy) — Architecture inspiration for daemon and query design
- The Rust community for excellent crates

## Related Projects

- [selfspy](https://github.com/selfspy/selfspy) — Cross-platform activity logger
- [ActivityWatch](https://github.com/ActivityWatch/activitywatch) — Comprehensive time tracker
- [RescueTime](https://www.rescuetime.com/) — Commercial time tracking

---

**Note**: This tool monitors all keyboard input when running. Use responsibly and be aware of privacy implications.
