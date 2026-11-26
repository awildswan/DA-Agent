#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

fn main() {
    tauri::Builder::default()
        .setup(|_app| {
            // 启动 Python sidecar（FastAPI 服务，默认 :8000）
            for bin in ["python", "python3", "py"] {
                let mut cmd = Command::new(bin);
                cmd.args(["-m", "daagent", "web"]);
                if cmd.spawn().is_ok() {
                    break;
                }
            }
            std::thread::sleep(std::time::Duration::from_secs(3));
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
