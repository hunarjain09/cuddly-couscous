//! Tokenization module - space and time-based splitting

use crate::capture::{KeyEvent, KeyType, SpecialKey};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone)]
pub struct TokenizerConfig {
    pub gap_threshold_ms: u64,
    pub min_token_length: usize,
}

impl Default for TokenizerConfig {
    fn default() -> Self {
        Self {
            gap_threshold_ms: 500,
            min_token_length: 2,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Token {
    pub content: String,
    pub started_at: DateTime<Utc>,
    pub ended_at: DateTime<Utc>,
    pub key_count: usize,
}

impl Token {
    /// Check if this token is likely code
    pub fn is_likely_code(&self) -> bool {
        let code_indicators = [
            "fn ", "let ", "if ", "for ", "while ", // Rust
            "def ", "class ", "import ",            // Python
            "function", "const ", "var ",           // JS
            "->", "=>", "::", "||", "&&",           // Operators
            "()", "[]", "{}",                       // Brackets
        ];

        code_indicators
            .iter()
            .any(|ind| self.content.contains(ind))
    }
}

pub struct Tokenizer {
    config: TokenizerConfig,
    buffer: Vec<KeyEvent>,
    last_timestamp: Option<DateTime<Utc>>,
}

impl Tokenizer {
    pub fn new(config: TokenizerConfig) -> Self {
        Self {
            config,
            buffer: Vec::new(),
            last_timestamp: None,
        }
    }

    pub fn process(&mut self, event: KeyEvent) -> Option<Token> {
        // Check for time gap
        if let Some(last) = self.last_timestamp {
            let gap = event
                .timestamp
                .signed_duration_since(last)
                .num_milliseconds();
            if gap > self.config.gap_threshold_ms as i64 {
                let token = self.flush();
                self.buffer.push(event.clone());
                self.last_timestamp = Some(event.timestamp);
                return token;
            }
        }

        // Check for space
        if matches!(event.key_type, KeyType::Special(SpecialKey::Space)) {
            let token = self.flush();
            self.last_timestamp = Some(event.timestamp);
            return token;
        }

        self.buffer.push(event.clone());
        self.last_timestamp = Some(event.timestamp);
        None
    }

    pub fn flush(&mut self) -> Option<Token> {
        if self.buffer.len() < self.config.min_token_length {
            self.buffer.clear();
            return None;
        }

        let content: String = self
            .buffer
            .iter()
            .filter_map(|e| match &e.key_type {
                KeyType::Character(c) => Some(*c),
                _ => None,
            })
            .collect();

        if content.is_empty() {
            self.buffer.clear();
            return None;
        }

        let token = Token {
            content,
            started_at: self.buffer.first()?.timestamp,
            ended_at: self.buffer.last()?.timestamp,
            key_count: self.buffer.len(),
        };

        self.buffer.clear();
        Some(token)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::Modifiers;
    use chrono::Duration;

    fn make_event(c: char, offset_ms: i64) -> KeyEvent {
        KeyEvent {
            keycode: 0,
            key_type: KeyType::Character(c),
            timestamp: Utc::now() + Duration::milliseconds(offset_ms),
            modifiers: Modifiers::default(),
        }
    }

    fn make_space(offset_ms: i64) -> KeyEvent {
        KeyEvent {
            keycode: 49,
            key_type: KeyType::Special(SpecialKey::Space),
            timestamp: Utc::now() + Duration::milliseconds(offset_ms),
            modifiers: Modifiers::default(),
        }
    }

    #[test]
    fn test_space_splits_token() {
        let mut tokenizer = Tokenizer::new(TokenizerConfig::default());

        // Type "hello "
        assert!(tokenizer.process(make_event('h', 0)).is_none());
        assert!(tokenizer.process(make_event('e', 50)).is_none());
        assert!(tokenizer.process(make_event('l', 100)).is_none());
        assert!(tokenizer.process(make_event('l', 150)).is_none());
        assert!(tokenizer.process(make_event('o', 200)).is_none());

        let token = tokenizer.process(make_space(250));
        assert!(token.is_some());
        assert_eq!(token.unwrap().content, "hello");
    }

    #[test]
    fn test_time_gap_splits_token() {
        let config = TokenizerConfig {
            gap_threshold_ms: 500,
            min_token_length: 2,
        };
        let mut tokenizer = Tokenizer::new(config);

        // Type "hi" then pause 600ms then "there"
        assert!(tokenizer.process(make_event('h', 0)).is_none());
        assert!(tokenizer.process(make_event('i', 50)).is_none());

        // Big gap triggers flush
        let token = tokenizer.process(make_event('t', 700));
        assert!(token.is_some());
        assert_eq!(token.unwrap().content, "hi");
    }

    #[test]
    fn test_is_likely_code() {
        let token = Token {
            content: "fn main() {".to_string(),
            started_at: Utc::now(),
            ended_at: Utc::now(),
            key_count: 11,
        };
        assert!(token.is_likely_code());

        let token2 = Token {
            content: "hello world".to_string(),
            started_at: Utc::now(),
            ended_at: Utc::now(),
            key_count: 11,
        };
        assert!(!token2.is_likely_code());
    }
}
