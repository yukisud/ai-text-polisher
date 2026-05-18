#!/bin/bash
# AI Text Polisher - 自動起動の解除

PLIST_FILE="$HOME/Library/LaunchAgents/com.aitextpolisher.plist"

if [ -f "$PLIST_FILE" ]; then
    launchctl unload "$PLIST_FILE"
    rm "$PLIST_FILE"
    echo "✅ 自動起動を解除しました。"
else
    echo "自動起動は設定されていません。"
fi
