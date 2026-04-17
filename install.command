#!/bin/bash
# AI Text Polisher インストーラー
# このファイルをダブルクリックするだけでインストールできます

cd "$(dirname "$0")"

clear
echo "╔══════════════════════════════════════╗"
echo "║   AI Text Polisher インストーラー    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# エラー時に停止
set -e

# ────────────────────────────
# 1. Homebrew
# ────────────────────────────
echo "【1/5】Homebrew を確認しています..."
if ! command -v brew &>/dev/null; then
    echo "  → Homebrew をインストールします（パスワードを求められる場合があります）"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Apple Silicon の PATH 設定
    eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
    eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true
else
    echo "  → OK（インストール済み）"
fi

# ────────────────────────────
# 2. Python 3.11
# ────────────────────────────
echo ""
echo "【2/5】Python 3.11 を確認しています..."
if ! command -v python3.11 &>/dev/null; then
    echo "  → Python 3.11 をインストールします..."
    brew install python@3.11
else
    echo "  → OK（$(python3.11 --version)）"
fi

# ────────────────────────────
# 3. Ollama
# ────────────────────────────
echo ""
echo "【3/5】Ollama を確認しています..."
if ! command -v ollama &>/dev/null; then
    echo "  → Ollama をインストールします..."
    brew install ollama
else
    echo "  → OK（インストール済み）"
fi

# ────────────────────────────
# 4. Python パッケージ
# ────────────────────────────
echo ""
echo "【4/5】Pythonパッケージをインストールしています..."
python3.11 -m pip install -q -r requirements.txt
echo "  → OK"

# ────────────────────────────
# 5. AIモデル
# ────────────────────────────
echo ""
echo "【5/5】AIモデルをダウンロードしています..."
echo "  （初回のみ・数分かかります）"
# Ollama を一時起動してモデルを取得
ollama serve &>/dev/null &
OLLAMA_PID=$!
sleep 3
ollama pull gemma3:4b
kill $OLLAMA_PID 2>/dev/null || true

# ────────────────────────────
# 自動起動の設定
# ────────────────────────────
echo ""
echo "ログイン時の自動起動を設定しています..."
bash install_autostart.sh
echo "  → OK"

# ────────────────────────────
# 完了
# ────────────────────────────
clear
echo "╔══════════════════════════════════════╗"
echo "║         インストール完了！           ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "最後に、以下の権限を設定してください。"
echo "（自動でシステム設定が開きます）"
echo ""
echo "  1. 「アクセシビリティ」に Terminal を追加"
echo "  2. 「マイク」に Terminal を追加"
echo ""
echo "権限を設定したら、ログアウト→ログインするか"
echo "次のコマンドで今すぐ起動できます："
echo ""
echo "  python3.11 $(pwd)/app.py"
echo ""

# システム設定のプライバシーページを開く
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"

echo "Enterキーを押すと終了します..."
read
