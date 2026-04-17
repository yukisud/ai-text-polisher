#!/bin/bash
# AI Text Polisher - ログイン時自動起動の設定

PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.aitextpolisher.plist"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3.11)"

if [ -z "$PYTHON" ]; then
    echo "❌ python3.11 が見つかりません。先に setup.sh を実行してください。"
    exit 1
fi

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aitextpolisher</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$APP_DIR/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/ai-text-polisher.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ai-text-polisher.log</string>
</dict>
</plist>
EOF

# 既存のエージェントをリロード
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

echo "✅ 自動起動を設定しました。次回ログイン時から自動で起動します。"
echo "   今すぐ起動するには: python3.11 $APP_DIR/app.py"
echo ""
echo "解除するには: bash $APP_DIR/uninstall_autostart.sh"
