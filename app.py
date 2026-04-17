#!/usr/bin/env python3
"""
AI Text Polisher - Typless-like voice input + AI text formatting app for macOS
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

from pynput import keyboard

# --- 設定 ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"
WHISPER_MODEL = "base"
SAMPLE_RATE = 16000
HOTKEY = {keyboard.Key.cmd, keyboard.KeyCode(char='k'), keyboard.Key.shift}

# --- プロンプト定義 ---
PROMPTS = {
    "Standard": """あなたは最高峰のリアルタイム・エディターです。
以下の【厳格なルール】に従って、入力された崩れた文章を完璧に整形してください。

【厳格なルール】
1. フィラー除去: 「えー、あの、その、えっと、あー」等の意味を持たない言葉はすべて削除。
2. 訂正の優先: 「A、いやB、やっぱりC」という言い直しがある場合、最後の「C」のみを真実として採用し、AとBは完全に無視すること。
3. 重複の統合: 同じ内容の繰り返し（例：「資料の、資料の件で」）は1つにまとめる。
4. 自然な敬語: 相手に失礼のない、かつ簡潔なビジネス敬語（です・ます調）で構成。
5. 出力制限: 解説、挨拶、補足説明（「以下は整形後です」等）は一切禁止。整形後の本文のみを出力すること。""",

    "Summarize": """あなたは議事録の要約専門家です。
入力された文章から「最終的な決定事項・結論のみ」を抽出してください。

【厳格なルール】
1. 言い直しや検討過程（「17日→18日→19日」）は最後の結論（「19日」）のみを残す。
2. フィラーや繰り返しはすべて除去。
3. 簡潔な体言止めまたはです・ます調で出力。
4. 出力は整形後の本文のみ。解説・補足は一切禁止。""",

    "Bullet": """入力された文章を、簡潔な日本語の箇条書きリストに変換してください。
各項目は「・」で始め、重複や言い直しは除去すること。
出力は箇条書きのみ。解説・補足は一切禁止。""",

    "Email": """入力された内容を、ビジネスメールの本文として整形してください。
適切な敬語を使用し、冒頭の挨拶（「お世話になっております。」）と末尾の締め（「よろしくお願いいたします。」）を付けること。
フィラー・言い直しは除去。出力はメール本文のみ。""",
}


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

        audio = np.concatenate(self.frames, axis=0).flatten()
        return audio

    def save_wav(self, audio):
        """音声データをWAVファイルとして保存"""
        import wave
        import struct

        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        with wave.open(tmp.name, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            audio_int16 = (audio * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        return tmp.name


class WhisperSTT:
    """whisper.cpp を使ったSTTクラス"""

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from pywhispercpp.model import Model
            self.model = Model(WHISPER_MODEL, print_realtime=False, print_progress=False)
        except Exception as e:
            print(f"Whisper モデルのロードに失敗: {e}")
            self.model = None

    def transcribe(self, wav_path):
        if self.model is None:
            return None
        try:
            segments = self.model.transcribe(wav_path)
            text = "".join([s.text for s in segments]).strip()
            return text if text else None
        except Exception as e:
            print(f"STT エラー: {e}")
            return None


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
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": user_text,
            "system": system_prompt,
            "stream": False,
            "keep_alive": -1,
        }).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except urllib.error.URLError:
            return None
        except Exception as e:
            print(f"Ollama エラー: {e}")
            return None


class AITextPolisher(rumps.App):
    """メインアプリケーション"""

    def __init__(self):
        super().__init__(
            "✏️",
            quit_button=None,
        )

        self.current_mode = "Standard"
        self.recorder = AudioRecorder()
        self.stt = None  # 遅延初期化
        self.ollama = OllamaClient()
        self.is_processing = False
        self.hotkey_pressed = False
        self._pressed_keys = set()

        self._build_menu()
        self._start_keyboard_listener()

        # Whisperモデルをバックグラウンドでロード
        threading.Thread(target=self._init_whisper, daemon=True).start()

    def _build_menu(self):
        # モード選択
        mode_items = []
        for mode in PROMPTS.keys():
            item = rumps.MenuItem(mode, callback=self._on_mode_change)
            if mode == self.current_mode:
                item.state = 1
            mode_items.append(item)

        self.menu = [
            rumps.MenuItem("AI Text Polisher", callback=None),
            None,  # セパレーター
            rumps.MenuItem("モード", callback=None),
            *mode_items,
            None,
            rumps.MenuItem("テキスト整形（クリップボード）", callback=self._on_polish_clipboard),
            None,
            rumps.MenuItem("ショートカット: ⌘⇧K (長押し=音声)", callback=None),
            None,
            rumps.MenuItem("終了", callback=rumps.quit_application),
        ]

    def _init_whisper(self):
        """バックグラウンドでWhisperをロード"""
        self.stt = WhisperSTT()
        if self.stt.model:
            rumps.notification("AI Text Polisher", "準備完了", "音声入力が使用できます")
        else:
            rumps.notification("AI Text Polisher", "注意", "Whisperのロードに失敗。テキスト整形モードのみ使用できます")

    def _on_mode_change(self, sender):
        for item in self.menu.values():
            if hasattr(item, 'state'):
                item.state = 0
        sender.state = 1
        self.current_mode = sender.title
        rumps.notification("AI Text Polisher", f"モード変更", f"{self.current_mode} に切り替えました")

    def _start_keyboard_listener(self):
        """グローバルショートカットリスナーを開始"""
        self._press_time = None

        def on_press(key):
            self._pressed_keys.add(key)
            if self._is_hotkey() and not self.hotkey_pressed and not self.is_processing:
                self.hotkey_pressed = True
                self._press_time = time.time()
                # 長押し判定用タイマー
                threading.Timer(0.5, self._on_long_press_check).start()

        def on_release(key):
            if key in self._pressed_keys:
                self._pressed_keys.discard(key)

            if self.hotkey_pressed:
                self.hotkey_pressed = False
                hold_time = time.time() - (self._press_time or time.time())
                if hold_time >= 0.5:
                    # 長押し → 録音停止してSTT処理
                    self._on_voice_stop()
                else:
                    # 短押し → テキスト整形
                    threading.Thread(target=self._on_polish_clipboard, daemon=True).start()

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def _is_hotkey(self):
        """Cmd + Shift + K が押されているか判定"""
        has_cmd = keyboard.Key.cmd in self._pressed_keys or keyboard.Key.cmd_l in self._pressed_keys or keyboard.Key.cmd_r in self._pressed_keys
        has_shift = keyboard.Key.shift in self._pressed_keys or keyboard.Key.shift_l in self._pressed_keys or keyboard.Key.shift_r in self._pressed_keys
        has_k = any(
            getattr(k, 'char', None) == 'k'
            for k in self._pressed_keys
        )
        return has_cmd and has_shift and has_k

    def _on_long_press_check(self):
        """長押し判定後に録音開始"""
        if self.hotkey_pressed and not self.is_processing:
            self.title = "🎙️"
            self.recorder.start()

    def _on_voice_stop(self):
        """録音停止 → STT → Ollama整形"""
        audio = self.recorder.stop()
        if audio is None or len(audio) < SAMPLE_RATE * 0.3:
            self.title = "✏️"
            return

        threading.Thread(
            target=self._process_voice,
            args=(audio,),
            daemon=True
        ).start()

    def _process_voice(self, audio):
        self.is_processing = True
        self.title = "⏳"

        wav_path = None
        try:
            # WAV保存
            wav_path = self.recorder.save_wav(audio)

            # STT
            if self.stt is None or self.stt.model is None:
                rumps.notification("AI Text Polisher", "エラー", "Whisperが利用できません")
                return

            text = self.stt.transcribe(wav_path)
            if not text:
                rumps.notification("AI Text Polisher", "エラー", "音声を認識できませんでした")
                return

            # Ollama整形
            self._polish_text(text)

        finally:
            if wav_path and os.path.exists(wav_path):
                os.unlink(wav_path)
            self.is_processing = False
            self.title = "✏️"

    def _on_polish_clipboard(self, sender=None):
        """クリップボードのテキストを整形"""
        if self.is_processing:
            return

        text = pyperclip.paste()
        if not text or not text.strip():
            rumps.notification("AI Text Polisher", "エラー", "クリップボードにテキストがありません")
            return

        threading.Thread(
            target=self._polish_and_paste,
            args=(text,),
            daemon=True
        ).start()

    def _polish_and_paste(self, text):
        self.is_processing = True
        self.title = "⏳"
        try:
            self._polish_text(text)
        finally:
            self.is_processing = False
            self.title = "✏️"

    def _polish_text(self, text):
        """Ollamaでテキスト整形 → クリップボードに書き戻す"""
        if not self.ollama.check_connection():
            rumps.notification(
                "AI Text Polisher", "Ollama未起動",
                "ターミナルで `ollama serve` を実行してください"
            )
            return

        system_prompt = PROMPTS[self.current_mode]
        result = self.ollama.generate(system_prompt, text)

        if result is None:
            rumps.notification("AI Text Polisher", "エラー", "整形に失敗しました")
            return

        # クリップボードに書き込み
        pyperclip.copy(result)

        # 自動ペースト（Cmd+V）
        try:
            from pynput.keyboard import Controller, Key
            ctrl = Controller()
            time.sleep(0.1)
            with ctrl.pressed(Key.cmd):
                ctrl.press('v')
                ctrl.release('v')
        except Exception:
            pass

        # 通知（プレビュー）
        preview = result[:60] + "..." if len(result) > 60 else result
        rumps.notification("AI Text Polisher ✓", f"[{self.current_mode}]", preview)


def main():
    app = AITextPolisher()
    app.run()


if __name__ == "__main__":
    main()
