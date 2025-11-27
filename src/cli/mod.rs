//! CLI argument parsing using clap

use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "kstrk")]
#[command(about = "Minimalist keystroke tracker for macOS")]
#[command(version)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Start tracking keystrokes (runs as daemon)
    Start {
        /// Time-gap threshold for tokenization (ms)
        #[arg(long, default_value = "500")]
        gap_threshold: u64,

        /// Run in foreground (don't daemonize)
        #[arg(long)]
        foreground: bool,

        /// Don't store actual keystrokes, only counts (like selfspy --no-text)
        #[arg(long)]
        no_text: bool,

        /// Encryption password for keystroke data
        #[arg(short, long)]
        password: Option<String>,
    },

    /// Stop tracking
    Stop,

    /// Show current status with live APM
    Status,

    /// Live watch mode - real-time APM and activity sparkline
    Watch {
        /// Refresh interval in milliseconds
        #[arg(long, default_value = "1000")]
        interval: u64,
    },

    /// Query stored data (inspired by selfstats)
    Query {
        #[command(subcommand)]
        action: QueryAction,
    },

    /// Display keyboard heatmap
    Heatmap {
        /// Time range: today, week, month, all
        #[arg(long, default_value = "today")]
        range: String,

        /// Use ASCII rendering (no TUI)
        #[arg(long)]
        ascii: bool,
    },

    /// Show statistics
    Stats {
        #[arg(long, default_value = "today")]
        range: String,
    },

    /// Show milestones and achievements
    Milestones,

    /// Export data
    Export {
        /// Output path
        #[arg(short, long)]
        output: PathBuf,

        /// Format: json, csv
        #[arg(long, default_value = "json")]
        format: String,
    },

    /// Manage configuration
    Config {
        #[command(subcommand)]
        action: ConfigAction,
    },
}

#[derive(Subcommand)]
pub enum ConfigAction {
    /// Open config in $EDITOR
    Edit,
    /// Show current config
    Show,
    /// Reset to defaults
    Reset,
    /// Show config file path
    Path,
}

/// Query subcommands (inspired by selfspy's selfstats)
#[derive(Subcommand)]
pub enum QueryAction {
    /// Show typing by window title (selfstats --tkeys)
    ByWindow {
        /// Filter by window title regex
        #[arg(short = 'T', long)]
        title: Option<String>,

        /// Filter by process name regex
        #[arg(short = 'P', long)]
        process: Option<String>,

        /// Date range start
        #[arg(short, long)]
        date: Option<String>,

        /// Number of results
        #[arg(short, long, default_value = "20")]
        limit: usize,
    },

    /// Show typing by process (selfstats --pkeys)
    ByProcess {
        #[arg(short, long)]
        date: Option<String>,

        #[arg(short, long, default_value = "20")]
        limit: usize,
    },

    /// Show active periods (selfstats --active)
    Active {
        /// Inactivity threshold in seconds
        #[arg(long, default_value = "180")]
        threshold: u64,

        #[arg(short, long)]
        date: Option<String>,
    },

    /// Show key frequency distribution (selfstats --key-freqs)
    KeyFreqs {
        #[arg(short, long)]
        date: Option<String>,

        /// Show human-readable key names
        #[arg(long)]
        human_readable: bool,
    },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_start_command_defaults() {
        let cli = Cli::parse_from(["kstrk", "start"]);

        match cli.command {
            Commands::Start {
                gap_threshold,
                foreground,
                no_text,
                password,
            } => {
                assert_eq!(gap_threshold, 500);
                assert!(!foreground);
                assert!(!no_text);
                assert!(password.is_none());
            }
            _ => panic!("Expected Start command"),
        }
    }

    #[test]
    fn test_heatmap_command() {
        let cli = Cli::parse_from(["kstrk", "heatmap", "--range", "week", "--ascii"]);

        match cli.command {
            Commands::Heatmap { range, ascii } => {
                assert_eq!(range, "week");
                assert!(ascii);
            }
            _ => panic!("Expected Heatmap command"),
        }
    }
}
