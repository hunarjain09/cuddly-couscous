//! # kstrk - Minimalist Keystroke Tracker
//!
//! A CLI binary for macOS that tracks keystrokes, generates heatmaps,
//! and tokenizes input patterns.
//!
//! Inspired by:
//! - [jpv-os/Keylogger](https://github.com/jpv-os/Keylogger)
//! - [selfspy/selfspy](https://github.com/selfspy/selfspy)

pub mod capture;
pub mod cli;
pub mod config;
pub mod daemon;
pub mod query;
pub mod stats;
pub mod storage;
pub mod tokenize;
pub mod viz;

pub use capture::{KeyEvent, KeyType};
pub use config::Config;
pub use storage::SqliteStorage;

/// Result type alias for kstrk operations
pub type Result<T> = std::result::Result<T, Error>;

/// Main error type for kstrk
#[derive(thiserror::Error, Debug)]
pub enum Error {
    #[error("Accessibility permission not granted")]
    AccessibilityDenied,

    #[error("Failed to create event tap: {0}")]
    EventTapFailed(String),

    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),

    #[error("Already running (PID: {0})")]
    AlreadyRunning(u32),

    #[error("Not running")]
    NotRunning,

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Daemon error: {0}")]
    Daemon(String),
}
