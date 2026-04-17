#!/bin/bash
# AI Text Polisher セットアップスクリプト

set -e

echo "=== AI Text Polisher セットアップ ==="
echo ""

# 1. 依存パッケージのインストール
echo "[1/3] Pythonパッケージをインストール中..."
pip3 install rumps pynput sounddevice pyperclip pywhispercpp numpy

echo ""
echo "[2/3] Ollamaの確認..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollamaがインストールされていません。"
    echo "   以下のコマンドでインストールしてください:"
    echo "   brew install ollama"
    echo "   または https://ollama.com からダウンロード"
else
    echo "✅ Ollamaが見つかりました: $(ollama --version 2>/dev/null || echo 'installed')"
    echo ""
    echo "   Ollamaを起動してモデルをダウンロードしてください:"
    echo "   ollama serve  (別ターミナルで)"
    echo "   ollama pull gemma3:4b"
fi

echo ""
echo "[3/3] macOS権限の設定について"
echo "--------------------------------------"
echo "アプリを起動する前に以下の権限が必要です:"
echo ""
echo "1. アクセシビリティ権限:"
echo "   システム設定 → プライバシーとセキュリティ → アクセシビリティ"
echo "   → Terminal（またはPython）をONにする"
echo ""
echo "2. マイク権限:"
echo "   システム設定 → プライバシーとセキュリティ → マイク"
echo "   → Terminal（またはPython）をONにする"
echo ""
echo "======================================="
echo "セットアップ完了！"
echo ""
echo "起動方法: python3 app.py"
echo "ショートカット: ⌘⇧K を短押し → クリップボードテキスト整形"
echo "              ⌘⇧K を長押し → 音声入力して整形"
echo "======================================="
