use super::KeyEvent;
use chrono::Utc;
use std::sync::mpsc::Sender;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CaptureError {
    #[error("Accessibility permission not granted")]
    AccessibilityDenied,

    #[error("Failed to create event tap: {0}")]
    EventTapCreation(String),

    #[error("Failed to create runloop source: {0}")]
    RunLoopSource(String),

    #[error("Not supported on this platform")]
    PlatformNotSupported,
}

/// Check if accessibility permissions are granted
#[cfg(target_os = "macos")]
pub fn check_accessibility() -> bool {
    use core_graphics::event_source::CGEventSourceStateID;

    // Try to check if we're trusted
    unsafe {
        let trusted = core_foundation::base::TCFType::wrap_under_get_rule(
            core_graphics::sys::CGPreflightListenEventAccess()
        );
        trusted != 0
    }
}

#[cfg(not(target_os = "macos"))]
pub fn check_accessibility() -> bool {
    false
}

/// Request accessibility permissions
#[cfg(target_os = "macos")]
pub fn request_accessibility() -> Result<(), CaptureError> {
    use std::process::Command;

    Command::new("open")
        .arg("x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
        .spawn()
        .map_err(|e| CaptureError::EventTapCreation(e.to_string()))?;

    Ok(())
}

#[cfg(not(target_os = "macos"))]
pub fn request_accessibility() -> Result<(), CaptureError> {
    Err(CaptureError::PlatformNotSupported)
}

/// Start capturing keyboard events
#[cfg(target_os = "macos")]
pub fn start_capture(tx: Sender<KeyEvent>) -> Result<(), CaptureError> {
    use core_foundation::runloop::{kCFRunLoopCommonModes, CFRunLoop};
    use core_graphics::event::{
        CGEvent, CGEventTap, CGEventTapLocation, CGEventTapOptions, CGEventTapPlacement,
        CGEventType, EventField,
    };

    // Check permissions first
    if !check_accessibility() {
        return Err(CaptureError::AccessibilityDenied);
    }

    // Create event tap
    let tap = CGEventTap::new(
        CGEventTapLocation::HID,
        CGEventTapPlacement::HeadInsertEventTap,
        CGEventTapOptions::ListenOnly,
        vec![CGEventType::KeyDown],
        move |_proxy, _event_type, event: &CGEvent| {
            // Extract keycode and flags
            let keycode = event.get_integer_value_field(EventField::KEYBOARD_EVENT_KEYCODE) as u16;
            let flags = event.get_flags().bits();

            // Create KeyEvent
            let key_event = KeyEvent::new(keycode, Utc::now(), flags);

            // Send to channel (ignore errors if receiver is dropped)
            let _ = tx.send(key_event);

            // Return None to not modify the event
            None
        },
    )
    .map_err(|e| CaptureError::EventTapCreation(format!("{:?}", e)))?;

    // Create runloop source
    unsafe {
        let loop_source = tap
            .mach_port
            .create_runloop_source(0)
            .map_err(|e| CaptureError::RunLoopSource(format!("{:?}", e)))?;

        CFRunLoop::get_current().add_source(&loop_source, kCFRunLoopCommonModes);
        tap.enable();

        CFRunLoop::run_current();
    }

    Ok(())
}

#[cfg(not(target_os = "macos"))]
pub fn start_capture(_tx: Sender<KeyEvent>) -> Result<(), CaptureError> {
    Err(CaptureError::PlatformNotSupported)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_platform_support() {
        #[cfg(target_os = "macos")]
        {
            // On macOS, check_accessibility should return a boolean
            let _result = check_accessibility();
        }

        #[cfg(not(target_os = "macos"))]
        {
            // On other platforms, should return false
            assert!(!check_accessibility());
        }
    }
}
