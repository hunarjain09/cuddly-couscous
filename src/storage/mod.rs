//! Storage module for persisting keystroke data using SQLite

use crate::capture::KeyEvent;
use chrono::{DateTime, Utc};
use rusqlite::{Connection, Result};
use std::path::Path;

pub struct SqliteStorage {
    conn: Connection,
}

impl SqliteStorage {
    /// Create a new storage instance with the given database path
    pub fn new(path: &Path) -> Result<Self> {
        let conn = Connection::open(path)?;
        let storage = Self { conn };
        storage.init_schema()?;
        Ok(storage)
    }

    /// Create in-memory database for testing
    pub fn in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        let storage = Self { conn };
        storage.init_schema()?;
        Ok(storage)
    }

    /// Initialize database schema
    fn init_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS windows (
                id INTEGER PRIMARY KEY,
                process_id INTEGER NOT NULL REFERENCES processes(id),
                title TEXT NOT NULL,
                UNIQUE(process_id, title)
            );

            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY,
                window_id INTEGER NOT NULL REFERENCES windows(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                key_text TEXT,
                key_count INTEGER NOT NULL,
                started_at TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hourly_stats (
                id INTEGER PRIMARY KEY,
                hour_bucket INTEGER NOT NULL,
                key_type TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                UNIQUE(hour_bucket, key_type)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                key_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_keys_window ON keys(window_id);
            CREATE INDEX IF NOT EXISTS idx_keys_created ON keys(created_at);
            CREATE INDEX IF NOT EXISTS idx_windows_process ON windows(process_id);
            CREATE INDEX IF NOT EXISTS idx_hourly_bucket ON hourly_stats(hour_bucket);
            "#,
        )
    }

    /// Record a keystroke event
    pub fn record_keystroke(
        &self,
        process: &str,
        window: &str,
        key_count: u32,
    ) -> Result<i64> {
        // Get or create process
        self.conn.execute(
            "INSERT OR IGNORE INTO processes (name) VALUES (?1)",
            [process],
        )?;
        let process_id: i64 = self.conn.query_row(
            "SELECT id FROM processes WHERE name = ?1",
            [process],
            |row| row.get(0),
        )?;

        // Get or create window
        self.conn.execute(
            "INSERT OR IGNORE INTO windows (process_id, title) VALUES (?1, ?2)",
            rusqlite::params![process_id, window],
        )?;
        let window_id: i64 = self.conn.query_row(
            "SELECT id FROM windows WHERE process_id = ?1 AND title = ?2",
            rusqlite::params![process_id, window],
            |row| row.get(0),
        )?;

        // Insert key record
        self.conn.execute(
            "INSERT INTO keys (window_id, key_count, started_at) VALUES (?1, ?2, ?3)",
            rusqlite::params![window_id, key_count, Utc::now().to_rfc3339()],
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    /// Get total keystrokes
    pub fn get_total_keystrokes(&self) -> Result<u64> {
        self.conn.query_row(
            "SELECT COALESCE(SUM(key_count), 0) FROM keys",
            [],
            |row| row.get(0),
        )
    }

    /// Get keystrokes by process
    pub fn get_keystrokes_by_process(&self) -> Result<Vec<(String, u64)>> {
        let mut stmt = self.conn.prepare(
            "SELECT p.name, SUM(k.key_count) as total
             FROM keys k
             JOIN windows w ON k.window_id = w.id
             JOIN processes p ON w.process_id = p.id
             GROUP BY p.id
             ORDER BY total DESC",
        )?;

        let rows = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, u64>(1)?))
        })?;

        rows.collect()
    }

    /// Record hourly aggregate for heatmap
    pub fn record_hourly_stat(&self, hour_bucket: i64, key_type: &str) -> Result<()> {
        self.conn.execute(
            "INSERT INTO hourly_stats (hour_bucket, key_type, count) VALUES (?1, ?2, 1)
             ON CONFLICT(hour_bucket, key_type) DO UPDATE SET count = count + 1",
            rusqlite::params![hour_bucket, key_type],
        )?;
        Ok(())
    }

    /// Get heatmap data
    pub fn get_heatmap_data(&self) -> Result<Vec<(String, u64)>> {
        let mut stmt = self.conn.prepare(
            "SELECT key_type, SUM(count) as total
             FROM hourly_stats
             GROUP BY key_type
             ORDER BY total DESC",
        )?;

        let rows = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, u64>(1)?))
        })?;

        rows.collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_in_memory_storage() {
        let storage = SqliteStorage::in_memory().expect("Failed to create in-memory db");
        assert_eq!(storage.get_total_keystrokes().unwrap(), 0);
    }

    #[test]
    fn test_record_keystroke() {
        let storage = SqliteStorage::in_memory().unwrap();

        let id = storage
            .record_keystroke("VSCode", "main.rs - kstrk", 10)
            .unwrap();
        assert!(id > 0);

        assert_eq!(storage.get_total_keystrokes().unwrap(), 10);
    }

    #[test]
    fn test_multiple_keystrokes() {
        let storage = SqliteStorage::in_memory().unwrap();

        storage.record_keystroke("VSCode", "main.rs", 10).unwrap();
        storage.record_keystroke("VSCode", "main.rs", 20).unwrap();
        storage.record_keystroke("Terminal", "zsh", 5).unwrap();

        assert_eq!(storage.get_total_keystrokes().unwrap(), 35);
    }

    #[test]
    fn test_keystrokes_by_process() {
        let storage = SqliteStorage::in_memory().unwrap();

        storage.record_keystroke("VSCode", "main.rs", 100).unwrap();
        storage.record_keystroke("VSCode", "lib.rs", 50).unwrap();
        storage.record_keystroke("Terminal", "zsh", 30).unwrap();

        let by_process = storage.get_keystrokes_by_process().unwrap();

        assert_eq!(by_process.len(), 2);
        assert_eq!(by_process[0], ("VSCode".to_string(), 150));
        assert_eq!(by_process[1], ("Terminal".to_string(), 30));
    }
}
