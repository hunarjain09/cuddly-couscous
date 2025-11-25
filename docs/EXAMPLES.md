# Usage Examples

## Example 1: Python Developer

**Goal**: Optimize layout for Python development

```bash
# 1. Track for 2 weeks during normal Python work
keystroke-tracker start

# 2. Analyze Python patterns
keystroke-tracker python-analysis

# Output:
# Symbol Priority Analysis:
#   Priority 1 (Home Row): 45,234 uses
#     • ( : 8,234
#     • ) : 8,234
#     • [ : 3,456
#     • ] : 3,456
#     • : : 5,678

# 3. Generate Python-optimized layout
keystroke-tracker optimize-symbols --context python

# 4. Export to Oryx
keystroke-tracker export-oryx \
    --context python \
    --name "Python Optimized"
```

**Result**: Layout with `()[]_:` on home row, reducing SFB rate from 3.2% to 1.8%.

## Example 2: Full-Stack Developer

**Goal**: Optimize for Python + JavaScript + Shell

```bash
# Track diverse work
keystroke-tracker start

# After 2 weeks, check context distribution
keystroke-tracker stats

# Analyze each context
keystroke-tracker python-analysis
keystroke-tracker voyager-simulate

# Generate balanced layout
keystroke-tracker optimize-symbols --context python
# Review and adjust for JavaScript symbols like => { }

# Export
keystroke-tracker export-oryx --name "Full Stack Layout"
```

## Example 3: Ergonomic Issues

**Goal**: Reduce finger pain from overuse

```bash
# Analyze current finger usage
keystroke-tracker finger-analysis

# Output:
# Finger Load Distribution:
#   right_pinky: 18.5%  ████████████████████
#   left_index:  15.2%  ███████████████
#   right_index: 14.8%  ███████████████

# Issues:
#   • High load on right pinky (>15%)
#   • SFB rate: 3.4% (target: <2%)

# Recommendations:
#   • Move frequent keys away from pinky
#   • Reorganize common bigrams

# Generate optimized layout to address issues
keystroke-tracker optimize-symbols
```

**Result**: Right pinky load reduced to 12.3%, SFB rate to 1.9%.

## Example 4: Macro Opportunities

**Goal**: Find patterns worth converting to macros

```bash
# Suggest macros (frequency >= 50)
keystroke-tracker suggest-macros --min-frequency 50

# Output:
# Top Macro Suggestions:
#   1. "()" - Used 487 times - Save 487 keystrokes
#   2. "def " - Used 234 times - Save 702 keystrokes
#   3. "import " - Used 189 times - Save 1,134 keystrokes
#   4. "__init__" - Used 67 times - Save 469 keystrokes

# Export macro suggestions
keystroke-tracker suggest-macros \
    --output exports/macros.json
```

**Implementation**: Add macros to Oryx layout for highest-value patterns.

## Example 5: Migration Tracking

**Goal**: Track progress adapting to new layout

```bash
# Before migration: track baseline
keystroke-tracker start --data-file data/baseline.json
# (Use for 1 week)

# After switching to Voyager: track progress
keystroke-tracker start --data-file data/week1-voyager.json
# (Use for 1 week)

# Compare
keystroke-tracker stats --data-file data/baseline.json
# WPM: 71, Error rate: 1.2%

keystroke-tracker stats --data-file data/week1-voyager.json
# WPM: 52, Error rate: 2.8%
# Recovery: 73%

# Week 2, 3, 4... continue tracking
# Track improvement over time
```

## Example 6: Voyager Simulation

**Goal**: Predict performance before buying Voyager

```bash
# Track on current keyboard
keystroke-tracker start
# (Track for at least 50,000 keystrokes)

# Simulate Voyager usage
keystroke-tracker voyager-simulate

# Output:
# Characters Typed: 52,438
# Layer Switches: 2,847
# Switches per 100 chars: 5.43 (target: <5)
# Overhead: 427,050 ms (8.1 ms/char)
# Efficiency Score: 89.2/100

# Recommendations:
#   • High layer switching detected
#   • Consider moving frequent symbols to base layer
```

**Decision**: Optimize layout before purchasing to reduce layer switching.

## Example 7: Team Layout

**Goal**: Create shared layout for team with similar typing patterns

```bash
# Each team member tracks individually
# Person 1:
keystroke-tracker start --data-file data/person1.json

# Person 2:
keystroke-tracker start --data-file data/person2.json

# Combine data (manually merge JSON files)
# Or track on shared machine

# Optimize for combined patterns
keystroke-tracker optimize-symbols --data-file data/team-combined.json

# Generate team layout
keystroke-tracker export-oryx --name "Team Layout v1"
```

## Example 8: Context-Specific Layers

**Goal**: Different layouts for coding vs writing

```bash
# Analyze context distribution
keystroke-tracker stats

# Python-specific layer (Layer 0-1)
keystroke-tracker optimize-symbols --context python

# General text layer (Layer 2-3)
# Focus on common punctuation, navigation

# Export multi-layer layout
keystroke-tracker export-oryx
# Manually customize layers in Oryx for different contexts
```

## Pro Tips

1. **Track longer for better data**: 100k+ keystrokes = more accurate
2. **Include all work**: coding, terminal, emails, documentation
3. **Review before committing**: analyze reports carefully
4. **Iterate**: optimize → test → refine → optimize again
5. **Share results**: help the community with your findings

## Sample Reports

Check `exports/analysis-reports/` for generated reports including:
- Full analysis report
- Layout rationale
- Symbol optimization
- Macro suggestions
- Voyager simulation results
