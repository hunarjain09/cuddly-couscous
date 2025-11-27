//! Query module for data analysis (inspired by selfspy's selfstats)

use crate::storage::SqliteStorage;

pub struct QueryEngine<'a> {
    storage: &'a SqliteStorage,
}

impl<'a> QueryEngine<'a> {
    pub fn new(storage: &'a SqliteStorage) -> Self {
        Self { storage }
    }

    /// Query keystrokes by process
    pub fn by_process(&self, limit: usize) -> Result<Vec<(String, u64)>, rusqlite::Error> {
        let mut results = self.storage.get_keystrokes_by_process()?;
        results.truncate(limit);
        Ok(results)
    }

    /// Query keystrokes by window
    pub fn by_window(
        &self,
        _title_pattern: Option<&str>,
        _process_pattern: Option<&str>,
        limit: usize,
    ) -> Result<Vec<(String, String, u64)>, rusqlite::Error> {
        // TODO: Implement window-based query with regex filtering
        // For now, return empty
        Ok(Vec::new())
    }

    /// Get total keystrokes
    pub fn total_keystrokes(&self) -> Result<u64, rusqlite::Error> {
        self.storage.get_total_keystrokes()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_query_engine() {
        let storage = SqliteStorage::in_memory().unwrap();
        let engine = QueryEngine::new(&storage);

        let total = engine.total_keystrokes().unwrap();
        assert_eq!(total, 0);
    }
}
