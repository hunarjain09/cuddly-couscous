//! Configuration management for kstrk

use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub capture: CaptureConfig,
    pub stats: StatsConfig,
    pub storage: StorageConfig,
    pub heatmap: HeatmapConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaptureConfig {
    #[serde(default = "default_ignore_keys")]
    pub ignore_keys: Vec<String>,
    #[serde(default = "default_true")]
    pub ignore_lone_modifiers: bool,
    #[serde(default = "default_gap_threshold")]
    pub token_gap_threshold: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatsConfig {
    #[serde(default = "default_apm_window")]
    pub apm_window_secs: u64,
    #[serde(default = "default_true")]
    pub milestones_enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    pub data_dir: Option<PathBuf>,
    #[serde(default = "default_retention_days")]
    pub retention_days: u32,
    #[serde(default = "default_aggregate_days")]
    pub aggregate_after_days: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeatmapConfig {
    #[serde(default = "default_color_scheme")]
    pub color_scheme: String,
    #[serde(default = "default_true")]
    pub show_labels: bool,
}

fn default_ignore_keys() -> Vec<String> {
    vec![
        "CapsLock".to_string(),
        "NumLock".to_string(),
        "ScrollLock".to_string(),
    ]
}

fn default_true() -> bool {
    true
}

fn default_gap_threshold() -> u64 {
    500
}

fn default_apm_window() -> u64 {
    60
}

fn default_retention_days() -> u32 {
    365
}

fn default_aggregate_days() -> u32 {
    30
}

fn default_color_scheme() -> String {
    "heat".to_string()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            capture: CaptureConfig {
                ignore_keys: default_ignore_keys(),
                ignore_lone_modifiers: true,
                token_gap_threshold: default_gap_threshold(),
            },
            stats: StatsConfig {
                apm_window_secs: default_apm_window(),
                milestones_enabled: true,
            },
            storage: StorageConfig {
                data_dir: None,
                retention_days: default_retention_days(),
                aggregate_after_days: default_aggregate_days(),
            },
            heatmap: HeatmapConfig {
                color_scheme: default_color_scheme(),
                show_labels: true,
            },
        }
    }
}

impl Config {
    /// Get the configuration file path
    pub fn config_path() -> Option<PathBuf> {
        ProjectDirs::from("com", "kstrk", "kstrk")
            .map(|dirs| dirs.config_dir().join("config.toml"))
    }

    /// Get the data directory path
    pub fn data_dir(&self) -> PathBuf {
        self.storage.data_dir.clone().unwrap_or_else(|| {
            ProjectDirs::from("com", "kstrk", "kstrk")
                .map(|dirs| dirs.data_dir().to_path_buf())
                .unwrap_or_else(|| PathBuf::from("."))
        })
    }

    /// Load configuration from file
    pub fn load() -> Result<Self, crate::Error> {
        if let Some(path) = Self::config_path() {
            if path.exists() {
                let content = std::fs::read_to_string(&path)?;
                let config: Config = toml::from_str(&content)
                    .map_err(|e| crate::Error::Config(e.to_string()))?;
                return Ok(config);
            }
        }
        Ok(Config::default())
    }

    /// Save configuration to file
    pub fn save(&self) -> Result<(), crate::Error> {
        if let Some(path) = Self::config_path() {
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            let content = toml::to_string_pretty(self)
                .map_err(|e| crate::Error::Config(e.to_string()))?;
            std::fs::write(&path, content)?;
        }
        Ok(())
    }
}

/// Filter for ignoring certain keys
pub struct IgnoreFilter {
    ignored_keys: HashSet<String>,
    ignore_lone_modifiers: bool,
}

impl IgnoreFilter {
    pub fn from_config(config: &Config) -> Self {
        Self {
            ignored_keys: config.capture.ignore_keys.iter().cloned().collect(),
            ignore_lone_modifiers: config.capture.ignore_lone_modifiers,
        }
    }

    pub fn should_ignore(&self, event: &crate::capture::KeyEvent) -> bool {
        use crate::capture::KeyType;

        // Check explicit ignore list
        let key_name = event.key_type.name();
        if self.ignored_keys.contains(&key_name) {
            return true;
        }

        // Check lone modifier
        if self.ignore_lone_modifiers {
            if let KeyType::Modifier(_) = event.key_type {
                return true;
            }
        }

        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.capture.token_gap_threshold, 500);
        assert_eq!(config.stats.apm_window_secs, 60);
        assert!(config.stats.milestones_enabled);
    }

    #[test]
    fn test_config_serialization() {
        let config = Config::default();
        let serialized = toml::to_string(&config).unwrap();
        let deserialized: Config = toml::from_str(&serialized).unwrap();
        assert_eq!(config.capture.token_gap_threshold, deserialized.capture.token_gap_threshold);
    }
}
