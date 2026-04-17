# AI Text Polisher

macOS向けの音声入力＋AIテキスト整形アプリ。[Typless](https://typless.app)にインスパイアされた、ローカルLLMで動くプライバシー重視のツール。

音声を録音 → macOS標準STT（Siri/Dictationエンジン）で文字起こし → Ollamaで自然な文章に整形 → 自動貼り付け、をショートカット一発で実行します。

## 動作環境

- macOS 13以降（Apple Silicon / M1推奨）
- Python 3.11以降
- [Ollama](https://ollama.com) インストール済み

## セットアップ

### 1. Python 3.11のインストール

```bash
brew install python@3.11
```

### 2. Ollamaのインストールとモデル取得

```bash
# Ollamaをインストール（https://ollama.com からDLも可）
brew install ollama

# LLMモデルをダウンロード
ollama pull gemma3:4b
```

### 3. このリポジトリをクローン

```bash
git clone https://github.com/yukisud/ai-text-polisher.git
cd ai-text-polisher
```

### 4. Pythonパッケージをインストール

```bash
pip3.11 install -r requirements.txt
```

または付属のセットアップスクリプトを使用：

```bash
bash setup.sh
```

### 5. macOS権限を付与

| 権限 | 設定場所 | 用途 |
|------|---------|------|
| アクセシビリティ | システム設定 → プライバシーとセキュリティ → アクセシビリティ | グローバルショートカット検知・自動ペースト |
| マイク | システム設定 → プライバシーとセキュリティ → マイク | 音声入力 |
| 音声認識 | 初回起動時にダイアログが表示される | STT |

Terminal（またはPython）を許可リストに追加してください。

### 6. 起動

```bash
# 別ターミナルでOllamaを起動しておく
ollama serve

# アプリを起動
python3.11 app.py
```

メニューバーに **✨** アイコンが表示されれば起動成功です。

## 使い方

| 操作 | 動作 |
|------|------|
| `⌘ + Option + K` **短押し** | クリップボードのテキストを整形して貼り付け |
| `⌘ + Option + K` **長押し（0.5秒以上）** | 音声録音開始 → 離すとSTT→整形→貼り付け |
| **テキスト選択** + `⌘ + Option + K` **長押し** | 選択中テキストに対して音声で指示（翻訳・要約・言い換え等） |

### 整形機能

- フィラー除去（「えー」「あの」「えっと」等）
- 言い直し統合（最後の言い直しのみ採用）
- 重複除去
- 番号列挙の自動箇条書き変換（「1つ目〜2つ目〜3つ目」→ 番号付きリスト）
- 英語の固有名詞・専門用語はそのまま英語で保持
- 自然なビジネス敬語（です・ます調）

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| GUI / メニューバー | rumps |
| グローバルショートカット | NSEvent（PyObjC）|
| 音声録音 | sounddevice + numpy |
| STT | macOS SFSpeechRecognizer（Siri/Dictationエンジン）|
| LLM整形 | Ollama REST API（gemma3:4b）|
| クリップボード | pyperclip |

## ライセンス

MIT
