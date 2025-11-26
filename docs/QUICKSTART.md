# Quick Start Guide

## Installation

```bash
# Install in development mode
pip install -e .

# Verify installation
keystroke-tracker --version
```

## Basic Workflow

### 1. Start Tracking (1-2 weeks)

```bash
keystroke-tracker start
```

Work normally. The tracker runs in the background. Press `Ctrl+C` when done.

### 2. Check Your Data

```bash
# Basic stats
keystroke-tracker stats

# Finger analysis
keystroke-tracker finger-analysis
```

### 3. Run Full Analysis

```bash
# Generate comprehensive report
keystroke-tracker export-report --output reports/analysis.md

# Simulate on Voyager
keystroke-tracker voyager-simulate

# Python-specific analysis
keystroke-tracker python-analysis
```

### 4. Optimize Layout

```bash
# Generate optimized layout
keystroke-tracker optimize-symbols --context python \
    --output exports/rationale.md

# Export to Oryx
keystroke-tracker export-oryx \
    --output exports/layouts/my-layout.json \
    --name "My Optimized Layout"
```

### 5. Flash to Voyager

1. Go to https://configure.zsa.io
2. Import `my-layout.json`
3. Review and customize
4. Flash to keyboard

## Tips

- **Track for minimum 50,000 keystrokes** for accurate results
- **Include diverse work**: coding, terminal, documentation
- **Be natural**: don't change your typing during tracking
- **Review reports carefully** before committing to a layout
- **Start gradual**: change a few keys at a time

## Common Issues

### Permission Denied

On Linux/Mac, you may need elevated permissions:

```bash
sudo keystroke-tracker start
```

### No Data File

If you see "data file not found", you haven't tracked yet:

```bash
keystroke-tracker start  # Track first!
```

### Import Errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Next Steps

- Read the full [README](../README.md)
- Review generated reports in `exports/`
- Join the ergonomic keyboard community
- Share your optimized layout!
