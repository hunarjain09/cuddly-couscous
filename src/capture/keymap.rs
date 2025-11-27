use lazy_static::lazy_static;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;

/// Key type enumeration
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum KeyType {
    Character(char),
    Arrow(ArrowDirection),
    Modifier(ModifierKey),
    Special(SpecialKey),
    Function(u8),
    Unknown(u16),
}

impl KeyType {
    /// Get a human-readable name for this key type
    pub fn name(&self) -> String {
        match self {
            KeyType::Character(c) => c.to_string(),
            KeyType::Arrow(dir) => format!("arrow:{:?}", dir).to_lowercase(),
            KeyType::Modifier(m) => format!("modifier:{:?}", m).to_lowercase(),
            KeyType::Special(s) => format!("special:{:?}", s).to_lowercase(),
            KeyType::Function(n) => format!("F{}", n),
            KeyType::Unknown(code) => format!("unknown:{}", code),
        }
    }
}

impl fmt::Display for KeyType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            KeyType::Character(c) => write!(f, "{}", c),
            KeyType::Arrow(dir) => write!(f, "{:?}", dir),
            KeyType::Modifier(m) => write!(f, "{:?}", m),
            KeyType::Special(s) => write!(f, "{:?}", s),
            KeyType::Function(n) => write!(f, "F{}", n),
            KeyType::Unknown(code) => write!(f, "Unknown({})", code),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArrowDirection {
    Up,
    Down,
    Left,
    Right,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ModifierKey {
    Shift,
    Control,
    Option,
    Command,
    CapsLock,
    Function,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SpecialKey {
    Return,
    Tab,
    Escape,
    Delete,
    Backspace,
    Space,
    ForwardDelete,
    Home,
    End,
    PageUp,
    PageDown,
}

// macOS keycode mapping based on Carbon.h and actual testing
lazy_static! {
    pub static ref KEYCODE_MAP: HashMap<u16, KeyType> = {
        let mut m = HashMap::new();

        // Letters (QWERTY layout)
        m.insert(0, KeyType::Character('a'));
        m.insert(1, KeyType::Character('s'));
        m.insert(2, KeyType::Character('d'));
        m.insert(3, KeyType::Character('f'));
        m.insert(4, KeyType::Character('h'));
        m.insert(5, KeyType::Character('g'));
        m.insert(6, KeyType::Character('z'));
        m.insert(7, KeyType::Character('x'));
        m.insert(8, KeyType::Character('c'));
        m.insert(9, KeyType::Character('v'));
        m.insert(11, KeyType::Character('b'));
        m.insert(12, KeyType::Character('q'));
        m.insert(13, KeyType::Character('w'));
        m.insert(14, KeyType::Character('e'));
        m.insert(15, KeyType::Character('r'));
        m.insert(16, KeyType::Character('y'));
        m.insert(17, KeyType::Character('t'));
        m.insert(31, KeyType::Character('o'));
        m.insert(32, KeyType::Character('u'));
        m.insert(34, KeyType::Character('i'));
        m.insert(35, KeyType::Character('p'));
        m.insert(37, KeyType::Character('l'));
        m.insert(38, KeyType::Character('j'));
        m.insert(40, KeyType::Character('k'));
        m.insert(45, KeyType::Character('n'));
        m.insert(46, KeyType::Character('m'));

        // Numbers
        m.insert(18, KeyType::Character('1'));
        m.insert(19, KeyType::Character('2'));
        m.insert(20, KeyType::Character('3'));
        m.insert(21, KeyType::Character('4'));
        m.insert(23, KeyType::Character('5'));
        m.insert(22, KeyType::Character('6'));
        m.insert(26, KeyType::Character('7'));
        m.insert(28, KeyType::Character('8'));
        m.insert(25, KeyType::Character('9'));
        m.insert(29, KeyType::Character('0'));

        // Symbols
        m.insert(27, KeyType::Character('-'));
        m.insert(24, KeyType::Character('='));
        m.insert(33, KeyType::Character('['));
        m.insert(30, KeyType::Character(']'));
        m.insert(41, KeyType::Character(';'));
        m.insert(39, KeyType::Character('\''));
        m.insert(42, KeyType::Character('\\'));
        m.insert(43, KeyType::Character(','));
        m.insert(47, KeyType::Character('.'));
        m.insert(44, KeyType::Character('/'));
        m.insert(50, KeyType::Character('`'));

        // Arrow keys
        m.insert(123, KeyType::Arrow(ArrowDirection::Left));
        m.insert(124, KeyType::Arrow(ArrowDirection::Right));
        m.insert(125, KeyType::Arrow(ArrowDirection::Down));
        m.insert(126, KeyType::Arrow(ArrowDirection::Up));

        // Special keys
        m.insert(36, KeyType::Special(SpecialKey::Return));
        m.insert(48, KeyType::Special(SpecialKey::Tab));
        m.insert(49, KeyType::Special(SpecialKey::Space));
        m.insert(51, KeyType::Special(SpecialKey::Delete));
        m.insert(53, KeyType::Special(SpecialKey::Escape));
        m.insert(117, KeyType::Special(SpecialKey::ForwardDelete));
        m.insert(115, KeyType::Special(SpecialKey::Home));
        m.insert(119, KeyType::Special(SpecialKey::End));
        m.insert(116, KeyType::Special(SpecialKey::PageUp));
        m.insert(121, KeyType::Special(SpecialKey::PageDown));

        // Function keys
        m.insert(122, KeyType::Function(1));
        m.insert(120, KeyType::Function(2));
        m.insert(99, KeyType::Function(3));
        m.insert(118, KeyType::Function(4));
        m.insert(96, KeyType::Function(5));
        m.insert(97, KeyType::Function(6));
        m.insert(98, KeyType::Function(7));
        m.insert(100, KeyType::Function(8));
        m.insert(101, KeyType::Function(9));
        m.insert(109, KeyType::Function(10));
        m.insert(103, KeyType::Function(11));
        m.insert(111, KeyType::Function(12));

        // Modifiers
        m.insert(56, KeyType::Modifier(ModifierKey::Shift));     // Left Shift
        m.insert(60, KeyType::Modifier(ModifierKey::Shift));     // Right Shift
        m.insert(59, KeyType::Modifier(ModifierKey::Control));   // Left Control
        m.insert(62, KeyType::Modifier(ModifierKey::Control));   // Right Control
        m.insert(58, KeyType::Modifier(ModifierKey::Option));    // Left Option
        m.insert(61, KeyType::Modifier(ModifierKey::Option));    // Right Option
        m.insert(55, KeyType::Modifier(ModifierKey::Command));   // Left Command
        m.insert(54, KeyType::Modifier(ModifierKey::Command));   // Right Command
        m.insert(57, KeyType::Modifier(ModifierKey::CapsLock));
        m.insert(63, KeyType::Modifier(ModifierKey::Function));

        m
    };
}

/// Convert macOS keycode to KeyType
pub fn keycode_to_key(keycode: u16) -> KeyType {
    KEYCODE_MAP
        .get(&keycode)
        .cloned()
        .unwrap_or(KeyType::Unknown(keycode))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_letter_keycodes() {
        assert_eq!(keycode_to_key(0), KeyType::Character('a'));
        assert_eq!(keycode_to_key(1), KeyType::Character('s'));
        assert_eq!(keycode_to_key(2), KeyType::Character('d'));
        assert_eq!(keycode_to_key(3), KeyType::Character('f'));
    }

    #[test]
    fn test_number_keycodes() {
        assert_eq!(keycode_to_key(18), KeyType::Character('1'));
        assert_eq!(keycode_to_key(19), KeyType::Character('2'));
        assert_eq!(keycode_to_key(20), KeyType::Character('3'));
    }

    #[test]
    fn test_arrow_keycodes() {
        assert_eq!(keycode_to_key(123), KeyType::Arrow(ArrowDirection::Left));
        assert_eq!(keycode_to_key(124), KeyType::Arrow(ArrowDirection::Right));
        assert_eq!(keycode_to_key(125), KeyType::Arrow(ArrowDirection::Down));
        assert_eq!(keycode_to_key(126), KeyType::Arrow(ArrowDirection::Up));
    }

    #[test]
    fn test_special_keycodes() {
        assert_eq!(keycode_to_key(36), KeyType::Special(SpecialKey::Return));
        assert_eq!(keycode_to_key(48), KeyType::Special(SpecialKey::Tab));
        assert_eq!(keycode_to_key(49), KeyType::Special(SpecialKey::Space));
        assert_eq!(keycode_to_key(53), KeyType::Special(SpecialKey::Escape));
    }

    #[test]
    fn test_function_keycodes() {
        assert_eq!(keycode_to_key(122), KeyType::Function(1));
        assert_eq!(keycode_to_key(120), KeyType::Function(2));
        assert_eq!(keycode_to_key(111), KeyType::Function(12));
    }

    #[test]
    fn test_unknown_keycode() {
        assert_eq!(keycode_to_key(999), KeyType::Unknown(999));
    }

    #[test]
    fn test_all_printable_chars_mapped() {
        let letters = "asdfghjklqwertyuiopzxcvbnm";
        let mapped: Vec<char> = KEYCODE_MAP
            .values()
            .filter_map(|k| match k {
                KeyType::Character(c) => Some(*c),
                _ => None,
            })
            .collect();

        for letter in letters.chars() {
            assert!(
                mapped.contains(&letter),
                "Letter '{}' not found in keymap",
                letter
            );
        }
    }

    #[test]
    fn test_key_type_name() {
        assert_eq!(KeyType::Character('a').name(), "a");
        assert_eq!(
            KeyType::Arrow(ArrowDirection::Left).name(),
            "arrow:left"
        );
        assert_eq!(KeyType::Function(5).name(), "F5");
    }
}
