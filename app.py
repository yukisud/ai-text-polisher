#!/usr/bin/env python3
"""
AI Text Polisher - Voice input + AI text formatting app for macOS
"""

import rumps
import threading
import time
import json
import subprocess
import tempfile
import os
import numpy as np
import sounddevice as sd
import pyperclip
import urllib.request
import urllib.error
import AppKit

# --- 設定 ---
OLLAMA_URL = "http://localhost:11434/api/generate"
SAMPLE_RATE = 16000

# config.json から設定を読み込む
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
try:
    with open(_CONFIG_PATH) as _f:
        _cfg = json.load(_f)
except Exception:
    _cfg = {}

OLLAMA_MODEL   = _cfg.get("model", "gemma3:4b")
KEEP_ALIVE     = _cfg.get("keep_alive", 300)      # 秒 (0=即解放, -1=永続)
OLLAMA_TIMEOUT = _cfg.get("ollama_timeout", 30)
ICON_IDLE       = "✨"
ICON_RECORDING  = "🎙️"
ICON_PROCESSING = "⏳"

# NSEvent masks / modifier flags
_NSEventMaskKeyDown  = 1 << 10
_NSEventMaskKeyUp    = 1 << 11
_NSCommandKeyMask    = 1 << 20
_NSAlternateKeyMask  = 1 << 19  # Option/Alt key

# --- プロンプト ---
POLISH_PROMPT = """あなたは音声認識テキストの整形専門家です。
以下のルールで整形してください。

1. フィラー除去：「えー」「あの」「その」「えっと」「まあ」「なんか」「あー」「うーん」等を削除
2. 言い直し統合：「AいやB」「AやっぱりB」→ 最後のBのみ採用
3. 重複除去：繰り返しを1つにまとめる
4. 番号付きリスト（1. 2. 3.）はその構造を維持しつつ各項目を自然な文に整形する
5. 英語保持：英語の固有名詞・専門用語・ブランド名はそのまま英語で表記
6. ビジネス敬語（です・ます調）
7. 情報の省略禁止：元の発話に含まれる全内容を保持する
8. 整形後テキストのみ出力（解説・補足・前置き禁止）"""

RESPONSE_PROMPT = """あなたはテキスト処理の専門家です。
「選択テキスト」に対して「音声指示」に従って処理し、結果のみ出力してください。
指示に応じて翻訳・要約・言い換え・フォーマット変更などを行います。
処理結果のテキストのみ出力。解説・補足・前置きは一切禁止。"""


class AudioRecorder:
    """Push-to-Talk 音声録音クラス"""

    def __init__(self):
        self.recording = False
        self.frames = []

    def start(self):
        self.frames = []
        self.recording = True

        def callback(indata, frames, time_info, status):
            if self.recording:
                self.frames.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            callback=callback
        )
        self.stream.start()

    def stop(self):
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        if not self.frames:
            return None
        return np.concatenate(self.frames, axis=0).flatten()

    def save_wav(self, audio):
        import wave
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        with wave.open(tmp.name, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        return tmp.name


class AppleSTT:
    """macOS SFSpeechRecognizer (Siri/Dictation エンジン) を使ったSTTクラス"""

    def __init__(self):
        self.available = False
        self.recognizer = None
        self._setup()

    def _setup(self):
        try:
            from Speech import SFSpeechRecognizer
            import Foundation

            auth_done = threading.Event()
            auth_result = [None]

            def auth_handler(status):
                auth_result[0] = status
                auth_done.set()

            SFSpeechRecognizer.requestAuthorization_(auth_handler)
            auth_done.wait(timeout=10)

            if auth_result[0] == 3:  # Authorized
                locale = Foundation.NSLocale.alloc().initWithLocaleIdentifier_("ja-JP")
                self.recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale)
                self.available = bool(self.recognizer and self.recognizer.isAvailable())
                print(f"[AppleSTT] 初期化完了 available={self.available}")
            else:
                print(f"[AppleSTT] 認証未許可 status={auth_result[0]}")
        except Exception as e:
            print(f"[AppleSTT] 初期化エラー: {e}")

    def transcribe(self, wav_path):
        if not self.available:
            return None
        try:
            from Speech import SFSpeechURLRecognitionRequest
            import Foundation

            result = [None]
            done = threading.Event()

            url = Foundation.NSURL.fileURLWithPath_(wav_path)
            request = SFSpeechURLRecognitionRequest.alloc().initWithURL_(url)
            request.setShouldReportPartialResults_(False)

            def handler(recognition_result, error):
                if error:
                    print(f"[AppleSTT] 認識エラー: {error}")
                if recognition_result:
                    result[0] = recognition_result.bestTranscription().formattedString()
                if error or (recognition_result and recognition_result.isFinal()):
                    done.set()

            self.recognizer.recognitionTaskWithRequest_resultHandler_(request, handler)
            done.wait(timeout=30)

            text = result[0]
            print(f"[STT結果] {text}")
            return text if text else None
        except Exception as e:
            print(f"[AppleSTT] STTエラー: {e}")
            return None


def _preformat_numbered_list(text):
    """「1つ目〜2点目〜3軒目」等のパターンをOllama送信前に番号リスト形式に変換
    STTの誤認識（つ目→軒目/点目/件目 等）も含めて対応"""
    import re
    # 「つ個番点軒件本枚個」などSTTが誤認識しやすい助数詞を全てカバー
    result = re.sub(
        r'(?:まず\s*)?([1-9１-９])[つ個番点軒件本枚ケヶ]目(?:[がはにでは、：: ]*)',
        lambda m: f'\n{int(m.group(1))}. ',
        text
    )
    return result.strip()


class OllamaClient:
    """Ollama API クライアント"""

    def check_connection(self):
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(self, system_prompt, user_text):
        prompt = f"""{system_prompt}

【入力テキスト】
{user_text}

【出力】
"""
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "keep_alive": KEEP_ALIVE,
            "options": {"temperature": 0.1},
        }).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                response = result.get("response", "").strip()
                # 重複出力を除去
                paragraphs = [p.strip() for p in response.split('\n') if p.strip()]
                if len(paragraphs) >= 2 and paragraphs[0] == paragraphs[-1]:
                    response = paragraphs[0]
                elif len(response) > 20:
                    half = len(response) // 2
                    if response[:half].strip() == response[half:].strip():
                        response = response[:half].strip()
                print(f"[Ollama結果] {response}")
                return response
        except urllib.error.URLError:
            return None
        except Exception as e:
            print(f"Ollama エラー: {e}")
            return None


class AITextPolisher(rumps.App):
    """メインアプリケーション"""

    def __init__(self):
        super().__init__(ICON_IDLE, quit_button=None)

        self.recorder = AudioRecorder()
        self.stt = None
        self.ollama = OllamaClient()
        self.is_processing = False
        self.hotkey_pressed = False
        self._context_text = None  # 選択テキスト（音声指示モード用）

        self._build_menu()
        self._start_keyboard_listener()
        threading.Thread(target=self._init_stt, daemon=True).start()
        threading.Thread(target=self._ensure_ollama, daemon=True).start()

    def _build_menu(self):
        self.menu = [
            rumps.MenuItem(f"AI Text Polisher  ({OLLAMA_MODEL})", callback=None),
            None,
            rumps.MenuItem("クリップボードを整形", callback=self._on_polish_clipboard),
            None,
            rumps.MenuItem("⌘⌥K 短押し: 整形  長押し: 音声入力", callback=None),
            rumps.MenuItem("テキスト選択 + 長押し: 選択テキストへの指示", callback=None),
            None,
            rumps.MenuItem("終了", callback=rumps.quit_application),
        ]

    def _ensure_ollama(self):
        """Ollamaが起動していなければ自動起動する"""
        if self.ollama.check_connection():
            return
        try:
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # 起動待ち（最大10秒）
            for _ in range(10):
                time.sleep(1)
                if self.ollama.check_connection():
                    print("[Ollama] 自動起動完了")
                    return
            print("[Ollama] 起動タイムアウト")
        except FileNotFoundError:
            rumps.notification("AI Text Polisher", "Ollama未インストール",
                               "https://ollama.com からインストールしてください")

    def _init_stt(self):
        self.stt = AppleSTT()
        if self.stt.available:
            rumps.notification("AI Text Polisher", "準備完了", "音声入力が使用できます")
        else:
            rumps.notification("AI Text Polisher", "注意", "音声認識を初期化できませんでした")

    def _capture_selected_text(self):
        """現在選択中のテキストをCmd+Cで取得"""
        try:
            old_clip = pyperclip.paste()
            subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to keystroke "c" using command down'],
                check=False, timeout=1
            )
            time.sleep(0.08)
            new_clip = pyperclip.paste()
            if new_clip and new_clip != old_clip:
                pyperclip.copy(old_clip)  # 元のクリップボードを復元
                return new_clip.strip()
        except Exception:
            pass
        return None

    def _start_keyboard_listener(self):
        self._press_time = None

        def on_key_down(event):
            try:
                flags = event.modifierFlags()
                has_cmd = bool(flags & _NSCommandKeyMask)
                has_opt = bool(flags & _NSAlternateKeyMask)
                chars = event.charactersIgnoringModifiers() or ''
                has_k = chars.lower() == 'k'
                if has_cmd and has_opt and has_k and not self.hotkey_pressed and not self.is_processing:
                    self._context_text = self._capture_selected_text()
                    self.hotkey_pressed = True
                    self._press_time = time.time()
                    threading.Timer(0.5, self._on_long_press_check).start()
            except Exception:
                pass

        def on_key_up(event):
            try:
                if not self.hotkey_pressed:
                    return
                chars = event.charactersIgnoringModifiers() or ''
                if chars.lower() == 'k':
                    self.hotkey_pressed = False
                    hold_time = time.time() - (self._press_time or time.time())
                    if hold_time >= 0.5:
                        self._on_voice_stop()
                    else:
                        threading.Thread(target=self._on_polish_clipboard, daemon=True).start()
            except Exception:
                pass

        self._key_down_monitor = AppKit.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            _NSEventMaskKeyDown, on_key_down
        )
        self._key_up_monitor = AppKit.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            _NSEventMaskKeyUp, on_key_up
        )

    def _on_long_press_check(self):
        if self.hotkey_pressed and not self.is_processing:
            self.title = ICON_RECORDING
            self.recorder.start()

    def _on_voice_stop(self):
        audio = self.recorder.stop()
        if audio is None or len(audio) < SAMPLE_RATE * 0.3:
            self.title = ICON_IDLE
            return
        threading.Thread(target=self._process_voice, args=(audio,), daemon=True).start()

    def _process_voice(self, audio):
        self.is_processing = True
        self.title = ICON_PROCESSING
        wav_path = None
        try:
            wav_path = self.recorder.save_wav(audio)

            if self.stt is None or not self.stt.available:
                rumps.notification("AI Text Polisher", "エラー", "音声認識が利用できません")
                return

            voice_text = self.stt.transcribe(wav_path)
            if not voice_text:
                rumps.notification("AI Text Polisher", "エラー", "音声を認識できませんでした")
                return

            if self._context_text:
                # 選択テキストへの指示モード
                self._respond_to_selection(self._context_text, voice_text)
            else:
                # 通常整形モード
                self._polish_text(voice_text)
        finally:
            if wav_path and os.path.exists(wav_path):
                os.unlink(wav_path)
            self._context_text = None
            self.is_processing = False
            self.title = ICON_IDLE

    def _on_polish_clipboard(self, sender=None):
        if self.is_processing:
            return
        text = pyperclip.paste()
        if not text or not text.strip():
            rumps.notification("AI Text Polisher", "エラー", "クリップボードにテキストがありません")
            return
        threading.Thread(target=self._polish_and_paste, args=(text,), daemon=True).start()

    def _polish_and_paste(self, text):
        self.is_processing = True
        self.title = ICON_PROCESSING
        try:
            self._polish_text(text)
        finally:
            self.is_processing = False
            self.title = ICON_IDLE

    def _polish_text(self, text):
        if not self.ollama.check_connection():
            rumps.notification("AI Text Polisher", "Ollama未起動",
                               "ターミナルで `ollama serve` を実行してください")
            return
        text = _preformat_numbered_list(text)
        result = self.ollama.generate(POLISH_PROMPT, text)
        if result is None:
            rumps.notification("AI Text Polisher", "エラー", "整形に失敗しました")
            return
        self._output(result, label="整形完了")

    def _respond_to_selection(self, selected_text, voice_instruction):
        if not self.ollama.check_connection():
            rumps.notification("AI Text Polisher", "Ollama未起動",
                               "ターミナルで `ollama serve` を実行してください")
            return
        combined = f"選択テキスト：\n{selected_text}\n\n音声指示：{voice_instruction}"
        result = self.ollama.generate(RESPONSE_PROMPT, combined)
        if result is None:
            rumps.notification("AI Text Polisher", "エラー", "処理に失敗しました")
            return
        self._output(result, label="指示実行完了")

    def _output(self, text, label="完了"):
        pyperclip.copy(text)
        try:
            time.sleep(0.1)
            subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to keystroke "v" using command down'],
                check=False
            )
        except Exception:
            pass
        preview = text[:60] + "..." if len(text) > 60 else text
        rumps.notification(f"✨ {label}", "", preview)


def main():
    app = AITextPolisher()
    app.run()


if __name__ == "__main__":
    main()
