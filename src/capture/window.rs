//! Window context tracking for macOS
//!
//! Tracks the currently active window and process information.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowInfo {
    pub process_name: String,
    pub window_title: String,
    pub geometry: Option<WindowGeometry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowGeometry {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
}

/// Get the currently focused window (macOS implementation)
#[cfg(target_os = "macos")]
pub fn get_active_window() -> Option<WindowInfo> {
    // TODO: Implement using CGWindowListCopyWindowInfo
    // For now, return a placeholder
    Some(WindowInfo {
        process_name: "Unknown".to_string(),
        window_title: "Unknown".to_string(),
        geometry: None,
    })
}

#[cfg(not(target_os = "macos"))]
pub fn get_active_window() -> Option<WindowInfo> {
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_active_window() {
        // Just verify it doesn't crash
        let _ = get_active_window();
    }
}
