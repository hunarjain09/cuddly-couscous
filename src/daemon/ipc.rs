//! IPC module for daemon communication

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum IpcError {
    #[error("Daemon not running")]
    NotRunning,

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

#[derive(Serialize, Deserialize)]
#[serde(tag = "method")]
pub enum Request {
    Status,
    Stop,
    GetStats { range: String },
    GetHeatmap { range: String },
    GetMilestones,
    Ping,
}

#[derive(Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Response {
    Status(StatusInfo),
    Stats(StatsInfo),
    Heatmap(HeatmapInfo),
    Milestones(Vec<String>),
    Pong,
    Ok,
    Error { message: String },
}

#[derive(Serialize, Deserialize)]
pub struct StatusInfo {
    pub pid: u32,
    pub uptime_secs: u64,
    pub apm: f64,
    pub today_count: u64,
    pub total_count: u64,
    pub streak_days: u32,
}

#[derive(Serialize, Deserialize)]
pub struct StatsInfo {
    pub total_keystrokes: u64,
    pub by_process: Vec<(String, u64)>,
}

#[derive(Serialize, Deserialize)]
pub struct HeatmapInfo {
    pub data: Vec<(String, u64)>,
}

pub struct Client;

impl Client {
    pub fn send(_request: Request) -> Result<Response, IpcError> {
        // TODO: Implement Unix socket communication
        // For now, return NotRunning
        Err(IpcError::NotRunning)
    }

    pub fn is_running() -> bool {
        // Check if daemon is running by checking PID file
        super::Daemon::is_running()
    }
}
