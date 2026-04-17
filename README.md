# AI Text Polisher

macOS向けの音声入力＋AIテキスト整形アプリ。[Typless](https://typless.app)にインスパイアされた、ローカルLLMで動くプライバシー重視のツール。

音声を録音 → macOS標準STT（Siri/Dictationエンジン）で文字起こし → Ollamaで自然な文章に整形 → 自動貼り付け、をショートカット一発で実行します。

## 動作環境

- macOS 13以降（Apple Silicon / M1推奨）
- Python 3.11以降
- [Ollama](https://ollama.com) インストール済み
- RAM: 8GB以上推奨（4GBでも `gemma3:1b` で動作可能）

## セットアップ

### 1. Python 3.11のインストール

```bash
brew install python@3.11
```

### 2. Ollamaのインストールとモデル取得

```bash
# Ollamaをインストール
brew install ollama

# LLMモデルをダウンロード（スペックに応じて選択）
ollama pull gemma3:4b   # 標準（RAM 8GB以上推奨）
ollama pull gemma3:1b   # 軽量版（RAM 4GB / 低スペック機向け）
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

### 6. 起動（通常）

```bash
python3.11 app.py
```

Ollamaが起動していない場合は自動で起動します。  
メニューバーに **✨** アイコンが表示されれば起動成功です。

### 7. ログイン時に自動起動する（推奨）

```bash
bash install_autostart.sh
```

以降はログインするだけでメニューバーに自動表示されます。ターミナルは不要です。

解除する場合：

```bash
bash uninstall_autostart.sh
```

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

## 設定のカスタマイズ（config.json）

`config.json` を編集することでモデルや動作を変更できます：

```json
{
  "model": "gemma3:4b",
  "keep_alive": 300,
  "ollama_timeout": 30
}
```

| キー | 説明 | 推奨値 |
|------|------|--------|
| `model` | 使用するOllamaモデル | `gemma3:1b`（軽量）/ `gemma3:4b`（標準） |
| `keep_alive` | モデルをRAMに保持する秒数 | `300`（5分）/ `0`（即解放）/ `-1`（永続） |
| `ollama_timeout` | API タイムアウト秒数 | `30` |

### スペック別おすすめ設定

| 環境 | model | keep_alive |
|------|-------|------------|
| M1 / 8GB以上 | `gemma3:4b` | `300` |
| 4GB / 低スペック | `gemma3:1b` | `0` |

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| GUI / メニューバー | rumps |
| グローバルショートカット | NSEvent（PyObjC）|
| 音声録音 | sounddevice + numpy |
| STT | macOS SFSpeechRecognizer（Siri/Dictationエンジン）|
| LLM整形 | Ollama REST API |
| クリップボード | pyperclip |
| 自動起動 | launchd（LaunchAgent）|

## ライセンス

MIT
