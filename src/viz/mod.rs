//! Visualization module for heatmaps and charts

use std::collections::HashMap;

// Keyboard layout as data (QWERTY)
pub const KEYBOARD_LAYOUT: &[&[&str]] = &[
    &["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
    &["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\"],
    &["a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'"],
    &["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
    &["space"],
];

/// Render ASCII heatmap
pub fn render_ascii_heatmap(counts: &HashMap<String, u64>) -> String {
    let blocks = ['░', '▒', '▓', '█'];
    let max = *counts.values().max().unwrap_or(&1);

    let mut output = String::new();
    for row in KEYBOARD_LAYOUT {
        for key in *row {
            let count = *counts.get(*key).unwrap_or(&0);
            let idx = if max == 0 {
                0
            } else {
                ((count as f64 / max as f64) * 3.0) as usize
            };
            output.push(blocks[idx.min(3)]);
            output.push(' ');
        }
        output.push('\n');
    }
    output
}

/// Get heat color intensity (0.0 to 1.0)
pub fn heat_intensity(count: u64, max: u64) -> f64 {
    if max == 0 {
        0.0
    } else {
        count as f64 / max as f64
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ascii_heatmap_empty() {
        let counts = HashMap::new();
        let heatmap = render_ascii_heatmap(&counts);
        assert!(!heatmap.is_empty());
        assert!(heatmap.contains('░'));
    }

    #[test]
    fn test_heat_intensity() {
        assert_eq!(heat_intensity(0, 100), 0.0);
        assert_eq!(heat_intensity(50, 100), 0.5);
        assert_eq!(heat_intensity(100, 100), 1.0);
    }
}
