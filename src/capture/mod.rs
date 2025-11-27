mod event_tap;
mod keymap;
pub mod window;

pub use event_tap::{start_capture, CaptureError};
pub use keymap::{keycode_to_key, ArrowDirection, KeyType, ModifierKey, SpecialKey};

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fmt;

/// Core data structure for raw keyboard events
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyEvent {
    pub keycode: u16,
    pub key_type: KeyType,
    pub timestamp: DateTime<Utc>,
    pub modifiers: Modifiers,
}

impl KeyEvent {
    pub fn new(keycode: u16, timestamp: DateTime<Utc>, flags: u64) -> Self {
        Self {
            keycode,
            key_type: keycode_to_key(keycode),
            timestamp,
            modifiers: Modifiers::from_flags(flags),
        }
    }
}

/// Modifier key state
#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
pub struct Modifiers {
    pub shift: bool,
    pub control: bool,
    pub option: bool,
    pub command: bool,
}

impl Modifiers {
    pub fn from_flags(flags: u64) -> Self {
        // macOS CGEventFlags values
        const SHIFT: u64 = 0x00020000;
        const CONTROL: u64 = 0x00040000;
        const OPTION: u64 = 0x00080000;
        const COMMAND: u64 = 0x00100000;

        Self {
            shift: (flags & SHIFT) != 0,
            control: (flags & CONTROL) != 0,
            option: (flags & OPTION) != 0,
            command: (flags & COMMAND) != 0,
        }
    }

    pub fn is_empty(&self) -> bool {
        !self.shift && !self.control && !self.option && !self.command
    }
}

impl fmt::Display for Modifiers {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut parts = Vec::new();
        if self.control {
            parts.push("Ctrl");
        }
        if self.option {
            parts.push("Opt");
        }
        if self.shift {
            parts.push("Shift");
        }
        if self.command {
            parts.push("Cmd");
        }
        write!(f, "{}", parts.join("+"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_modifiers_from_flags() {
        let flags = 0x00020000; // Shift
        let mods = Modifiers::from_flags(flags);
        assert!(mods.shift);
        assert!(!mods.control);
        assert!(!mods.option);
        assert!(!mods.command);
    }

    #[test]
    fn test_modifiers_display() {
        let mods = Modifiers {
            shift: true,
            control: true,
            option: false,
            command: false,
        };
        assert_eq!(mods.to_string(), "Ctrl+Shift");
    }
}
