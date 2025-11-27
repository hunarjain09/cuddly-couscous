//! Milestone definitions and tracking

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Milestone {
    pub threshold: u64,
    pub name: &'static str,
    pub emoji: &'static str,
    pub reached_at: Option<DateTime<Utc>>,
}

pub const MILESTONES: &[Milestone] = &[
    Milestone {
        threshold: 1_000,
        name: "First Thousand",
        emoji: "🎯",
        reached_at: None,
    },
    Milestone {
        threshold: 10_000,
        name: "Ten Thousand Club",
        emoji: "🎖️",
        reached_at: None,
    },
    Milestone {
        threshold: 100_000,
        name: "Centurion",
        emoji: "💯",
        reached_at: None,
    },
    Milestone {
        threshold: 1_000_000,
        name: "Millionaire",
        emoji: "🏆",
        reached_at: None,
    },
    Milestone {
        threshold: 10_000_000,
        name: "Legend",
        emoji: "👑",
        reached_at: None,
    },
];

impl Milestone {
    pub fn progress(&self, current: u64) -> f64 {
        if current >= self.threshold {
            1.0
        } else {
            current as f64 / self.threshold as f64
        }
    }

    pub fn remaining(&self, current: u64) -> u64 {
        if current >= self.threshold {
            0
        } else {
            self.threshold - current
        }
    }
}
