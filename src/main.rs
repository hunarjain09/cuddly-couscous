//! kstrk - Minimalist Keystroke Tracker for macOS
//!
//! A CLI binary that tracks keystrokes, generates heatmaps, and tokenizes input patterns.

use clap::Parser;
use kstrk::{
    cli::{Cli, Commands, ConfigAction, QueryAction},
    config::Config,
    daemon::{Client, Daemon},
    query::QueryEngine,
    storage::SqliteStorage,
    viz,
};
use std::process;

fn main() {
    // Parse CLI arguments
    let cli = Cli::parse();

    // Execute command
    if let Err(e) = run(cli) {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}

fn run(cli: Cli) -> Result<(), Box<dyn std::error::Error>> {
    match cli.command {
        Commands::Start {
            gap_threshold,
            foreground,
            no_text,
            password,
        } => {
            // Check macOS accessibility permissions first
            #[cfg(target_os = "macos")]
            {
                use kstrk::capture::{check_accessibility, request_accessibility};

                if !check_accessibility() {
                    eprintln!("⚠️  Accessibility permission required.\n");
                    eprintln!("This app needs permission to monitor keyboard input.");
                    eprintln!("Please grant access in:");
                    eprintln!("System Settings → Privacy & Security → Accessibility\n");
                    eprintln!("Opening settings...");
                    request_accessibility()?;
                    eprintln!("\nAfter granting permission, run this command again.");
                    return Ok(());
                }
            }

            let mut config = Config::load()?;
            config.capture.token_gap_threshold = gap_threshold;

            println!("✓ Starting keystroke tracking...");
            println!("  Gap threshold: {}ms", gap_threshold);
            println!("  Data: {:?}", config.data_dir().join("kstrk.db"));
            if no_text {
                println!("  Privacy: No text mode (counts only)");
            }

            Daemon::start(foreground, config)?;
        }

        Commands::Stop => {
            println!("Stopping kstrk daemon...");
            if !Client::is_running() {
                println!("Daemon is not running.");
            } else {
                println!("TODO: Implement stop via IPC");
            }
        }

        Commands::Status => {
            if !Client::is_running() {
                println!("✗ Daemon is not running");
                println!("\nStart with: kstrk start");
            } else {
                println!("✓ Daemon is running");
                println!("TODO: Show full status via IPC");
            }
        }

        Commands::Watch { interval } => {
            println!("Live watch mode (refresh every {}ms)", interval);
            println!("TODO: Implement live watch");
        }

        Commands::Query { action } => {
            let config = Config::load()?;
            let db_path = config.data_dir().join("kstrk.db");

            if !db_path.exists() {
                eprintln!("No data found. Start tracking first with: kstrk start");
                return Ok(());
            }

            let storage = SqliteStorage::new(&db_path)?;
            let engine = QueryEngine::new(&storage);

            match action {
                QueryAction::ByProcess { date, limit } => {
                    println!("Keystrokes by process:\n");
                    let results = engine.by_process(limit)?;
                    for (process, count) in results {
                        println!("  {:30} {:>10}", process, count);
                    }
                }
                QueryAction::ByWindow {
                    title,
                    process,
                    date,
                    limit,
                } => {
                    println!("Keystrokes by window:\n");
                    let results = engine.by_window(title.as_deref(), process.as_deref(), limit)?;
                    for (process, title, count) in results {
                        println!("  {} / {} : {}", process, title, count);
                    }
                }
                QueryAction::Active { threshold, date } => {
                    println!("Active periods (threshold: {}s):", threshold);
                    println!("TODO: Implement active periods query");
                }
                QueryAction::KeyFreqs {
                    date,
                    human_readable,
                } => {
                    println!("Key frequency distribution:");
                    println!("TODO: Implement key frequency query");
                }
            }
        }

        Commands::Heatmap { range, ascii } => {
            let config = Config::load()?;
            let db_path = config.data_dir().join("kstrk.db");

            if !db_path.exists() {
                eprintln!("No data found. Start tracking first with: kstrk start");
                return Ok(());
            }

            let storage = SqliteStorage::new(&db_path)?;
            let data = storage.get_heatmap_data()?;

            println!("Keyboard Heatmap ({})\n", range);

            if ascii {
                // Convert data to HashMap for visualization
                let mut counts = std::collections::HashMap::new();
                for (key, count) in data {
                    counts.insert(key, count);
                }
                let heatmap = viz::render_ascii_heatmap(&counts);
                println!("{}", heatmap);
                println!("\nLegend: ░ low  ▒ medium  ▓ high  █ very high");
            } else {
                println!("TUI heatmap not yet implemented. Use --ascii for now.");
            }
        }

        Commands::Stats { range } => {
            let config = Config::load()?;
            let db_path = config.data_dir().join("kstrk.db");

            if !db_path.exists() {
                eprintln!("No data found. Start tracking first with: kstrk start");
                return Ok(());
            }

            let storage = SqliteStorage::new(&db_path)?;
            let total = storage.get_total_keystrokes()?;
            let by_process = storage.get_keystrokes_by_process()?;

            println!("Statistics ({})\n", range);
            println!("─────────────────────────");
            println!("Total keystrokes: {}", total);
            println!("\nTop processes:");
            for (i, (process, count)) in by_process.iter().take(10).enumerate() {
                println!("  {}. {:30} {:>10}", i + 1, process, count);
            }
        }

        Commands::Milestones => {
            let config = Config::load()?;
            let db_path = config.data_dir().join("kstrk.db");

            if !db_path.exists() {
                eprintln!("No data found. Start tracking first with: kstrk start");
                return Ok(());
            }

            let storage = SqliteStorage::new(&db_path)?;
            let total = storage.get_total_keystrokes()?;

            println!("🏆 Milestones\n");
            println!("─────────────────────────────────");

            use kstrk::stats::MILESTONES;
            for milestone in MILESTONES {
                if total >= milestone.threshold {
                    println!(
                        "✓ {} {:20} — {:>15}",
                        milestone.emoji, milestone.name, milestone.threshold
                    );
                } else {
                    let remaining = milestone.threshold - total;
                    println!(
                        "○ {} {:20} — {:>15} (need {} more)",
                        milestone.emoji, milestone.name, milestone.threshold, remaining
                    );
                }
            }
        }

        Commands::Export { output, format } => {
            println!("Exporting to {:?} as {}", output, format);
            println!("TODO: Implement export");
        }

        Commands::Config { action } => match action {
            ConfigAction::Edit => {
                if let Some(path) = Config::config_path() {
                    println!("Opening config file: {:?}", path);
                    // Ensure config exists
                    if !path.exists() {
                        Config::default().save()?;
                    }
                    // Open in $EDITOR
                    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vim".to_string());
                    std::process::Command::new(editor).arg(&path).status()?;
                }
            }
            ConfigAction::Show => {
                let config = Config::load()?;
                let toml = toml::to_string_pretty(&config)?;
                println!("{}", toml);
            }
            ConfigAction::Reset => {
                Config::default().save()?;
                println!("✓ Config reset to defaults");
            }
            ConfigAction::Path => {
                if let Some(path) = Config::config_path() {
                    println!("{}", path.display());
                }
            }
        },
    }

    Ok(())
}
