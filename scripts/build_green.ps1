# 绿色版打包脚本（CI 与本地共用）
# 规则：排除 eval 依赖（datasets/pandas/pyarrow/huggingface_hub），不内置 .env（用户自备）
$ErrorActionPreference = "Stop"

Write-Host "[1/4] PyInstaller 打包独立 server ..."
uv run pyinstaller --onedir --name daagent-server `
  --add-data "src/daagent/web/static;daagent/web/static" `
  --add-data "src/daagent/prompts;daagent/prompts" `
  --collect-submodules uvicorn `
  --exclude-module datasets `
  --exclude-module pandas `
  --exclude-module pyarrow `
  --exclude-module huggingface_hub `
  --noconfirm `
  scripts/server_entry.py

Write-Host "[2/4] Tauri 编译 release ..."
Push-Location src-tauri
try { cargo build --release } finally { Pop-Location }

Write-Host "[3/4] 组装绿色目录 ..."
$green = "dist/green/daagent"
Remove-Item -Recurse -Force "dist/green" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $green | Out-Null
Copy-Item "src-tauri/target/release/daagent-desktop.exe" $green
Copy-Item -Recurse "dist/daagent-server" $green
Copy-Item "packaging/README.txt" $green
Copy-Item "packaging/.env.example" $green

Write-Host "[4/4] 打 ZIP ..."
Compress-Archive -Path "$green/*" -DestinationPath "dist/daagent-standalone-win64.zip" -Force
Write-Host "完成: dist/daagent-standalone-win64.zip"
