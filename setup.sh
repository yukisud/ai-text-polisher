#!/bin/bash
# AI Text Polisher セットアップスクリプト

set -e

echo "=== AI Text Polisher セットアップ ==="
echo ""

# Python 3.11 の確認
if ! command -v python3.11 &> /dev/null; then
    echo "[!] Python 3.11 が見つかりません。インストールします..."
    brew install python@3.11
fi
echo "✅ Python: $(python3.11 --version)"

# 1. 依存パッケージのインストール
echo ""
echo "[1/3] Pythonパッケージをインストール中..."
pip3.11 install -r requirements.txt

# 2. Ollama の確認
echo ""
echo "[2/3] Ollamaの確認..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollamaがインストールされていません。"
    echo "   以下のコマンドでインストールしてください:"
    echo "   brew install ollama"
    echo "   または https://ollama.com からダウンロード"
else
    echo "✅ Ollama: $(ollama --version 2>/dev/null || echo 'installed')"
    echo ""
    echo "   モデルをダウンロードしてください（まだの場合）:"
    echo "   ollama pull gemma3:4b"
fi

# 3. 権限案内
echo ""
echo "[3/3] macOS権限の設定"
echo "--------------------------------------"
echo "初回起動前に以下の権限を付与してください:"
echo ""
echo "1. アクセシビリティ権限（ショートカット検知に必要）:"
echo "   システム設定 → プライバシーとセキュリティ → アクセシビリティ"
echo "   → Terminal を ON"
echo ""
echo "2. マイク権限（音声入力に必要）:"
echo "   システム設定 → プライバシーとセキュリティ → マイク"
echo "   → Terminal を ON"
echo ""
echo "3. 音声認識権限（初回起動時にダイアログが表示されます）:"
echo "   「音声認識の使用を許可しますか？」→ 許可"
echo ""
echo "======================================="
echo "セットアップ完了！"
echo ""
echo "起動方法:"
echo "  1. ollama serve  （別ターミナルで起動しておく）"
echo "  2. python3.11 app.py"
echo ""
echo "ショートカット: ⌘⌥K 短押し → クリップボードテキスト整形"
echo "              ⌘⌥K 長押し → 音声入力して整形"
echo "              テキスト選択 + ⌘⌥K 長押し → 選択テキストへの音声指示"
echo "======================================="
