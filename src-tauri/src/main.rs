#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

fn main() {
    tauri::Builder::default()
        .setup(|_app| {
            if let Ok(exe) = std::env::current_exe() {
                if let Some(dir) = exe.parent() {
                    // 就近找 PyInstaller sidecar（onedir 子目录或同目录 onefile）
                    let candidates = [
                        dir.join("daagent-server").join("daagent-server.exe"),
                        dir.join("daagent-server.exe"),
                    ];
                    for c in candidates {
                        if c.exists() {
                            let _ = Command::new(&c).spawn();
                            break;
                        }
                    }
                    // 等 sidecar 起来再加载 UI
                    std::thread::sleep(std::time::Duration::from_secs(5));
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
