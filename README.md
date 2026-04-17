# AI Text Polisher

macOS向けの音声入力＋AIテキスト整形アプリ。[Typless](https://typless.app)にインスパイアされた、ローカルLLMで動くプライバシー重視のツール。

音声を録音 → Whisperで文字起こし → Ollamaで自然な文章に整形 → 自動貼り付け、をショートカット一発で実行します。

## 動作環境

- macOS (Apple Silicon / M1以降)
- Python 3.9+
- RAM 8GB以上
- [Ollama](https://ollama.com) インストール済み

## セットアップ

### 1. Ollamaのインストールとモデル取得

```bash
# Ollamaをインストール（https://ollama.com からDLも可）
brew install ollama

# Ollamaを起動（別ターミナルで）
ollama serve

# LLMモデルをダウンロード
ollama pull gemma3:4b
```

### 2. このリポジトリをクローン

```bash
git clone https://github.com/yukisud/ai-text-polisher.git
cd ai-text-polisher
```

### 3. Pythonパッケージをインストール

```bash
pip3 install -r requirements.txt
```

### 4. macOS権限を付与

アプリ起動前に以下の権限が必要です：

| 権限 | 設定場所 | 用途 |
|------|---------|------|
| アクセシビリティ | システム設定 → プライバシーとセキュリティ → アクセシビリティ | グローバルショートカット検知・自動ペースト |
| マイク | システム設定 → プライバシーとセキュリティ → マイク | 音声入力 |

→ Terminal（またはPython）を許可リストに追加してください。

### 5. 起動

```bash
python3 app.py
```

メニューバーに **✏️** アイコンが表示されれば起動成功です。

## 使い方

| 操作 | 動作 |
|------|------|
| `⌘ + Shift + K` **短押し** | クリップボードのテキストを整形して貼り付け |
| `⌘ + Shift + K` **長押し（0.5秒以上）** | 音声録音開始 → 離すとSTT→整形→貼り付け |
| メニューバーアイコンをクリック | モード切り替えなど |

### 整形モード

| モード | 説明 |
|--------|------|
| **Standard** | フィラー除去・言い直し統合・ビジネス敬語に整形 |
| **Summarize** | 最終的な決定事項・結論のみ抽出 |
| **Bullet** | 箇条書きリストに変換 |
| **Email** | ビジネスメール本文として整形 |

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| GUI / メニューバー | rumps |
| グローバルショートカット | pynput |
| 音声録音 | sounddevice + numpy |
| STT | pywhispercpp (whisper.cpp / Metal加速) |
| LLM整形 | Ollama REST API (gemma3:4b) |
| クリップボード | pyperclip |

## パフォーマンス目標（M1 Mac 8GB）

- STT処理（5秒の発話）: 1〜2秒
- LLM整形（短文）: 3〜5秒
- 合計（音声入力→貼り付け）: 10秒以内

## ライセンス

MIT
