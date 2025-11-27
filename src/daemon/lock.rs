//! Single-instance lock implementation (like selfspy's LockFile)

use fs2::FileExt;
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
use thiserror::Error;

const LOCK_FILE: &str = "kstrk.lock";

#[derive(Error, Debug)]
pub enum LockError {
    #[error("{lock_path} is locked! PID {pid:?} may be running. If no kstrk process is running, delete the stale lock file.")]
    AlreadyRunning {
        pid: Option<u32>,
        lock_path: PathBuf,
    },

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

pub struct InstanceLock {
    file: File,
    path: PathBuf,
}

impl InstanceLock {
    /// Attempt to acquire exclusive lock (like selfspy's LockFile)
    pub fn acquire(data_dir: &Path) -> Result<Self, LockError> {
        let path = data_dir.join(LOCK_FILE);

        // Create data directory if it doesn't exist
        std::fs::create_dir_all(data_dir)?;

        let file = std::fs::OpenOptions::new()
            .write(true)
            .create(true)
            .open(&path)?;

        // Try to get exclusive lock (non-blocking)
        match file.try_lock_exclusive() {
            Ok(_) => {
                // Write our PID to the lock file
                let mut file_mut = &file;
                file_mut.set_len(0)?;
                writeln!(file_mut, "{}", std::process::id())?;

                Ok(Self { file, path })
            }
            Err(_) => {
                // Read PID from existing lock
                let existing_pid = std::fs::read_to_string(&path)
                    .ok()
                    .and_then(|s| s.trim().parse::<u32>().ok());

                Err(LockError::AlreadyRunning {
                    pid: existing_pid,
                    lock_path: path,
                })
            }
        }
    }
}

impl Drop for InstanceLock {
    fn drop(&mut self) {
        // Release lock and remove file
        let _ = self.file.unlock();
        let _ = std::fs::remove_file(&self.path);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_lock_acquire() {
        let temp_dir = TempDir::new().unwrap();
        let lock = InstanceLock::acquire(temp_dir.path());
        assert!(lock.is_ok());
    }

    #[test]
    fn test_lock_prevents_duplicate() {
        let temp_dir = TempDir::new().unwrap();

        let _lock1 = InstanceLock::acquire(temp_dir.path()).unwrap();
        let lock2 = InstanceLock::acquire(temp_dir.path());
        assert!(lock2.is_err());
    }

    #[test]
    fn test_lock_cleanup_on_drop() {
        let temp_dir = TempDir::new().unwrap();
        let lock_path = temp_dir.path().join(LOCK_FILE);

        {
            let _lock = InstanceLock::acquire(temp_dir.path()).unwrap();
            assert!(lock_path.exists());
        }

        // Lock file should be removed after drop
        assert!(!lock_path.exists());
    }
}
