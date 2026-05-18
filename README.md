# AI Text Polisher

macOS向けの音声入力＋AIテキスト整形アプリ。[Typless](https://typless.app)にインスパイアされた、ローカルLLMで動くプライバシー重視のツール。

音声を録音 → macOS標準STT（Siri/Dictationエンジン）で文字起こし → Ollamaで自然な文章に整形 → 自動貼り付け、をショートカット一発で実行します。

## 動作環境

- macOS 13以降（Apple Silicon / M1推奨）
- Python 3.11以降
- [Ollama](https://ollama.com) インストール済み
- RAM: 8GB以上推奨（4GBでも `gemma3:1b` で動作可能）

## セットアップ

### かんたんインストール（推奨）

ターミナルの知識不要。ダブルクリックするだけで全て自動セットアップされます。

1. [ZIPをダウンロード](https://github.com/yukisud/ai-text-polisher/archive/refs/heads/main.zip) して解凍
2. フォルダ内の **`install.command`** をダブルクリック
   - 初回は「開発元を確認できません」と表示される場合があります  
     → 右クリック →「開く」→「開く」をクリック
3. ターミナルが開き、自動でインストールが始まります（数分かかります）
4. 完了後に表示される権限設定（アクセシビリティ・マイク）を行う

次回ログインから **✨** がメニューバーに自動表示されます。

---

### 手動インストール（開発者向け）

<details>
<summary>展開する</summary>

```bash
# 1. Python 3.11
brew install python@3.11

# 2. Ollama + モデル取得
brew install ollama
ollama pull gemma3:4b   # 標準（RAM 8GB以上）
# ollama pull gemma3:1b # 軽量版（RAM 4GB / 低スペック機）

# 3. クローン & パッケージインストール
git clone https://github.com/yukisud/ai-text-polisher.git
cd ai-text-polisher
pip3.11 install -r requirements.txt

# 4. 自動起動設定
bash install_autostart.sh
```

必要な権限：

| 権限 | 設定場所 |
|------|---------|
| アクセシビリティ | システム設定 → プライバシーとセキュリティ → アクセシビリティ |
| マイク | システム設定 → プライバシーとセキュリティ → マイク |

</details>

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
