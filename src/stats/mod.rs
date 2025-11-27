//! Live statistics tracking with APM and milestones

mod milestones;

pub use milestones::{Milestone, MILESTONES};

use chrono::{DateTime, NaiveDate, Utc};
use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// Rolling window for APM calculation
pub struct LiveStats {
    // Circular buffer of timestamps (last N seconds)
    recent_events: VecDeque<Instant>,
    window_duration: Duration,

    // Cumulative stats
    total_keystrokes: u64,
    session_start: Instant,

    // Streak tracking
    current_streak: u32,
    last_active_date: Option<NaiveDate>,

    // Milestones
    milestones_reached: Vec<Milestone>,
}

impl LiveStats {
    pub fn new(window_secs: u64) -> Self {
        Self {
            recent_events: VecDeque::with_capacity(1000),
            window_duration: Duration::from_secs(window_secs),
            total_keystrokes: 0,
            session_start: Instant::now(),
            current_streak: 0,
            last_active_date: None,
            milestones_reached: MILESTONES.to_vec(),
        }
    }

    /// Record a keystroke and check for milestones
    pub fn record(&mut self) -> Option<&Milestone> {
        let now = Instant::now();
        self.recent_events.push_back(now);
        self.total_keystrokes += 1;

        // Prune old events outside window
        let cutoff = now - self.window_duration;
        while self.recent_events.front().is_some_and(|&t| t < cutoff) {
            self.recent_events.pop_front();
        }

        // Update streak
        let today = Utc::now().date_naive();
        if let Some(last_date) = self.last_active_date {
            if today != last_date {
                let days_diff = (today - last_date).num_days();
                if days_diff == 1 {
                    self.current_streak += 1;
                } else if days_diff > 1 {
                    self.current_streak = 1;
                }
            }
        } else {
            self.current_streak = 1;
        }
        self.last_active_date = Some(today);

        // Check milestones
        self.milestones_reached
            .iter_mut()
            .find(|m| m.reached_at.is_none() && self.total_keystrokes >= m.threshold)
            .map(|m| {
                m.reached_at = Some(Utc::now());
                &*m
            })
    }

    /// Actions Per Minute (rolling window)
    pub fn apm(&self) -> f64 {
        let count = self.recent_events.len() as f64;
        let window_mins = self.window_duration.as_secs_f64() / 60.0;
        count / window_mins
    }

    /// Keys per second (instantaneous, last 5 seconds)
    pub fn kps(&self) -> f64 {
        let now = Instant::now();
        let cutoff = now - Duration::from_secs(5);
        let recent = self.recent_events.iter().filter(|&&t| t >= cutoff).count();
        recent as f64 / 5.0
    }

    /// Session duration
    pub fn session_duration(&self) -> Duration {
        self.session_start.elapsed()
    }

    /// Total keystrokes
    pub fn total(&self) -> u64 {
        self.total_keystrokes
    }

    /// Events in current window
    pub fn events_in_window(&self) -> usize {
        self.recent_events.len()
    }

    /// Current streak in days
    pub fn streak(&self) -> u32 {
        self.current_streak
    }

    /// Get all milestones
    pub fn milestones(&self) -> &[Milestone] {
        &self.milestones_reached
    }

    /// Get latest reached milestone
    pub fn latest_milestone(&self) -> Option<&Milestone> {
        self.milestones_reached
            .iter()
            .filter(|m| m.reached_at.is_some())
            .max_by_key(|m| m.reached_at)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_initial_state() {
        let stats = LiveStats::new(60);
        assert_eq!(stats.total(), 0);
        assert_eq!(stats.events_in_window(), 0);
        assert_eq!(stats.apm(), 0.0);
    }

    #[test]
    fn test_record_increments_total() {
        let mut stats = LiveStats::new(60);
        stats.record();
        stats.record();
        stats.record();
        assert_eq!(stats.total(), 3);
    }

    #[test]
    fn test_apm_calculation() {
        let mut stats = LiveStats::new(60); // 60 second window

        // Record 60 events
        for _ in 0..60 {
            stats.record();
        }

        // 60 events in 60 second window = 60 APM
        assert_eq!(stats.apm(), 60.0);
    }

    #[test]
    fn test_window_pruning() {
        // Use a very short window for testing
        let mut stats = LiveStats::new(1); // 1 second window

        stats.record();
        assert_eq!(stats.events_in_window(), 1);

        // Wait for events to expire
        thread::sleep(Duration::from_millis(1100));

        // Record new event to trigger pruning
        stats.record();

        // Only the new event should be in window
        assert_eq!(stats.events_in_window(), 1);
        // But total should be 2
        assert_eq!(stats.total(), 2);
    }

    #[test]
    fn test_milestone_detection() {
        let mut stats = LiveStats::new(60);

        // Record enough keystrokes to hit first milestone (1000)
        for _ in 0..1000 {
            stats.record();
        }

        let latest = stats.latest_milestone();
        assert!(latest.is_some());
        assert_eq!(latest.unwrap().threshold, 1000);
    }
}
