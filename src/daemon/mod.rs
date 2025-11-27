//! Daemon module for background operation

mod ipc;
mod lock;

pub use ipc::{Client, Request, Response, StatusInfo};
pub use lock::{InstanceLock, LockError};

use crate::capture::{start_capture, KeyEvent};
use crate::config::Config;
use crate::stats::LiveStats;
use crate::storage::SqliteStorage;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc};
use std::time::Duration;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DaemonError {
    #[error("Failed to daemonize: {0}")]
    DaemonizeFailed(String),

    #[error("Invalid PID file")]
    InvalidPidFile,

    #[error("Lock error: {0}")]
    Lock(#[from] LockError),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Capture error: {0}")]
    Capture(String),
}

pub const PID_FILE: &str = "/tmp/kstrk.pid";

pub struct Daemon {
    config: Config,
    storage: SqliteStorage,
    stats: LiveStats,
    running: Arc<AtomicBool>,
}

impl Daemon {
    pub fn new(config: Config) -> Result<Self, DaemonError> {
        let data_dir = config.data_dir();
        std::fs::create_dir_all(&data_dir)?;

        let db_path = data_dir.join("kstrk.db");
        let storage = SqliteStorage::new(&db_path)
            .map_err(|e| DaemonError::Capture(e.to_string()))?;

        let stats = LiveStats::new(config.stats.apm_window_secs);

        Ok(Self {
            config,
            storage,
            stats,
            running: Arc::new(AtomicBool::new(true)),
        })
    }

    pub fn start(foreground: bool, config: Config) -> Result<(), DaemonError> {
        // Acquire instance lock FIRST
        let data_dir = config.data_dir();
        let _lock = InstanceLock::acquire(&data_dir)?;

        if foreground {
            Self::run_foreground(config, _lock)
        } else {
            // For now, just run in foreground
            // Full daemonization can be added later
            Self::run_foreground(config, _lock)
        }
    }

    fn run_foreground(config: Config, _lock: InstanceLock) -> Result<(), DaemonError> {
        println!("Starting kstrk in foreground mode...");
        println!("Press Ctrl+C to stop.");

        let mut daemon = Daemon::new(config)?;

        // Setup signal handler
        let running = daemon.running.clone();
        ctrlc::set_handler(move || {
            println!("\nShutting down...");
            running.store(false, Ordering::SeqCst);
        })
        .map_err(|e| DaemonError::Capture(e.to_string()))?;

        // Start capture in separate thread
        let (tx, rx) = mpsc::channel::<KeyEvent>();
        let capture_thread = std::thread::spawn(move || start_capture(tx));

        // Main loop
        while daemon.running.load(Ordering::SeqCst) {
            // Process incoming keystrokes
            while let Ok(event) = rx.try_recv() {
                daemon.process_event(event);
            }

            std::thread::sleep(Duration::from_millis(10));
        }

        println!("Daemon stopped.");
        Ok(())
    }

    fn process_event(&mut self, event: KeyEvent) {
        // Update live stats
        if let Some(milestone) = self.stats.record() {
            println!("{} Milestone reached: {}", milestone.emoji, milestone.name);
        }

        // Record to storage (with default window for now)
        let _ = self.storage.record_keystroke("Unknown", "Unknown", 1);

        // Record hourly stat for heatmap
        let hour_bucket = event.timestamp.timestamp() / 3600;
        let _ = self
            .storage
            .record_hourly_stat(hour_bucket, &event.key_type.name());
    }

    pub fn is_running() -> bool {
        if !std::path::Path::new(PID_FILE).exists() {
            return false;
        }
        // Verify process is actually alive
        if let Ok(pid) = Self::read_pid() {
            unsafe { libc::kill(pid as i32, 0) == 0 }
        } else {
            false
        }
    }

    pub fn read_pid() -> Result<u32, DaemonError> {
        std::fs::read_to_string(PID_FILE)?
            .trim()
            .parse()
            .map_err(|_| DaemonError::InvalidPidFile)
    }
}
