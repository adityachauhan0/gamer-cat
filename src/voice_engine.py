import asyncio
import ctypes
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np
import pyaudio
import pyttsx3
from faster_whisper import WhisperModel

pythoncom = None
winsound = None
if sys.platform == "win32":
    try:
        import pythoncom as _pythoncom  # type: ignore

        pythoncom = _pythoncom
    except Exception:
        pythoncom = None
    try:
        import winsound as _winsound  # type: ignore

        winsound = _winsound
    except Exception:
        winsound = None

try:
    import edge_tts
except Exception:
    edge_tts = None

# Silence ALSA library stderr noise on Linux (common with PipeWire/ALSA bridge setups).
_ALSA_HANDLER = None
if sys.platform.startswith("linux"):
    try:
        _ALSA_ERROR_HANDLER = ctypes.CFUNCTYPE(
            None,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
        )

        def _alsa_error_handler(_filename, _line, _function, _err, _fmt):
            return

        _ALSA_HANDLER = _ALSA_ERROR_HANDLER(_alsa_error_handler)
        ctypes.cdll.LoadLibrary("libasound.so").snd_lib_error_set_handler(_ALSA_HANDLER)
    except Exception:
        _ALSA_HANDLER = None

class VoiceEngine:
    def __init__(self, stt_model="tiny", tts_backend="auto", background_listen=False, listen_duration=4):
        self.is_windows = sys.platform == "win32"
        self.local_only = os.getenv("GAMERCAT_LOCAL_ONLY", "1").strip() != "0"
        self.background_listen = background_listen
        listen_duration_env = os.getenv("GAMERCAT_LISTEN_DURATION", "").strip()
        if listen_duration_env:
            try:
                self.listen_duration = max(1.0, float(listen_duration_env))
            except ValueError:
                self.listen_duration = float(listen_duration)
        else:
            self.listen_duration = float(listen_duration)
        self.listen_resume_delay = float(os.getenv("GAMERCAT_LISTEN_RESUME_DELAY", "15.0"))
        self._listen_block_until = 0.0
        self.stop_event = threading.Event()
        self.transcript_queue = queue.Queue(maxsize=2)
        env_backend = os.getenv("GAMERCAT_TTS_BACKEND", "").strip().lower()
        self.tts_backend = env_backend if env_backend else tts_backend
        self.edge_voice = os.getenv("GAMERCAT_TTS_VOICE", "en-US-AnaNeural")
        self.edge_rate = os.getenv("GAMERCAT_TTS_RATE", "+10%")
        self.edge_pitch = os.getenv("GAMERCAT_TTS_PITCH", "+12Hz")
        self.stt_model_name = os.getenv("GAMERCAT_STT_MODEL", stt_model).strip() or stt_model
        self.stt_language = os.getenv("GAMERCAT_STT_LANGUAGE", "en").strip().lower()
        self.stt_language_threshold = float(os.getenv("GAMERCAT_STT_LANGUAGE_THRESHOLD", "0.4"))
        self.enforce_stt_language = os.getenv("GAMERCAT_STT_ENFORCE_LANGUAGE", "1").strip() != "0"
        self.piper_exe = os.getenv("GAMERCAT_TTS_PIPER_EXE", "piper")
        self.piper_model = os.getenv("GAMERCAT_TTS_PIPER_MODEL", "").strip()
        self.piper_config = os.getenv("GAMERCAT_TTS_PIPER_CONFIG", "").strip()
        self.piper_length_scale = os.getenv("GAMERCAT_TTS_PIPER_LENGTH_SCALE", "0.95")
        self._engine = None
        self._edge_enabled = edge_tts is not None and not self.local_only
        self._edge_warned = False
        self._piper_warned = False
        self._local_tts_warned = False
        self.tts_disabled = False
        self._tts_disabled_warned = False
        self.speaking_event = threading.Event()
        self.speech_pending_event = threading.Event()
        self.listening_event = threading.Event()
        self._record_lock = threading.Lock()
        self._speech_lock = threading.Lock()
        self._speech_pending_count = 0

        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        print(f"Loading Whisper model '{self.stt_model_name}'...")
        self.stt = WhisperModel(self.stt_model_name, device="cpu", compute_type="int8")
        print(f"[TTS] Backend mode: {self.tts_backend}")
        self.listener_thread = None
        if self.background_listen:
            self.listener_thread = threading.Thread(target=self._listen_worker, daemon=True)
            self.listener_thread.start()

    def _mark_speech_queued(self):
        with self._speech_lock:
            self._speech_pending_count += 1
            self.speech_pending_event.set()

    def _mark_speech_finished(self):
        with self._speech_lock:
            if self._speech_pending_count > 0:
                self._speech_pending_count -= 1
            if self._speech_pending_count == 0:
                self.speech_pending_event.clear()

    def _tts_active(self):
        return self.speaking_event.is_set() or self.speech_pending_event.is_set()

    def _select_english_voice(self):
        if self._engine is None:
            return
        try:
            voices = self._engine.getProperty("voices") or []
        except Exception:
            return
        if not voices:
            return

        def score_voice(voice):
            attrs = [
                str(getattr(voice, "name", "") or "").lower(),
                str(getattr(voice, "id", "") or "").lower(),
                str(getattr(voice, "languages", "") or "").lower(),
            ]
            combined = " ".join(attrs)
            score = 0
            if "english" in combined:
                score += 3
            if "en-us" in combined or "en_us" in combined:
                score += 3
            elif "en-gb" in combined or "en_gb" in combined:
                score += 2
            elif "en" in combined:
                score += 1
            if "afrikaans" in combined:
                score -= 2
            return score

        best_voice = max(voices, key=score_voice)
        if score_voice(best_voice) > 0:
            try:
                self._engine.setProperty("voice", best_voice.id)
            except Exception:
                pass

    def _speak_powershell(self, text):
        if not self.is_windows:
            raise RuntimeError("PowerShell TTS backend is only available on Windows.")
        escaped = text.replace("'", "''")
        cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Volume=100; "
            f"$s.Speak('{escaped}')"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            check=True,
            timeout=30,
        )

    async def _edge_save(self, text, out_path):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.edge_voice,
            rate=self.edge_rate,
            pitch=self.edge_pitch,
        )
        await communicate.save(out_path)

    def _speak_edge(self, text):
        if not self._edge_enabled or edge_tts is None:
            raise RuntimeError("edge-tts is not installed.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            out_path = tmp.name

        try:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._edge_save(text, out_path))
            finally:
                loop.close()
                asyncio.set_event_loop(None)
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", out_path],
                check=True,
                timeout=45,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            try:
                os.remove(out_path)
            except OSError:
                pass

    def _play_audio_file(self, path):
        if self.is_windows and winsound is not None:
            winsound.PlaySound(path, winsound.SND_FILENAME)
            return

        players = [
            (["pw-play", path], "pw-play"),
            (["paplay", path], "paplay"),
            (["aplay", path], "aplay"),
            (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path], "ffplay"),
            (["play", "-q", path], "play"),
        ]
        for command, binary in players:
            if shutil.which(binary) is None:
                continue
            subprocess.run(
                command,
                check=True,
                timeout=45,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        raise RuntimeError(
            "No audio player found. Install ffmpeg (ffplay) or alsa-utils (aplay)."
        )

    def _speak_piper(self, text):
        if not self.piper_model:
            raise RuntimeError("GAMERCAT_TTS_PIPER_MODEL is not set.")
        if not os.path.exists(self.piper_model):
            raise RuntimeError(f"Piper model not found: {self.piper_model}")
        if shutil.which(self.piper_exe) is None and not os.path.exists(self.piper_exe):
            raise RuntimeError(f"Piper executable not found: {self.piper_exe}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            wav_path = tmp.name

        cmd = [
            self.piper_exe,
            "--model",
            self.piper_model,
            "--output_file",
            wav_path,
            "--length_scale",
            self.piper_length_scale,
        ]
        if self.piper_config:
            cmd.extend(["--config", self.piper_config])

        try:
            subprocess.run(cmd, input=text, text=True, check=True, timeout=45)
            self._play_audio_file(wav_path)
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass

    def _ensure_tts_engine(self):
        if self._engine is None:
            if self.is_windows:
                self._engine = pyttsx3.init("sapi5")
            else:
                self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 180)
            self._engine.setProperty("volume", 1.0)
            self._select_english_voice()
            voices = self._engine.getProperty("voices")
            if voices:
                current_voice = self._engine.getProperty("voice")
                selected = None
                for voice in voices:
                    if str(getattr(voice, "id", "")) == str(current_voice):
                        selected = voice
                        break
                if selected is None:
                    selected = voices[0]
                print(f"[TTS] pyttsx3 initialized. Voice: {selected.name}")

    def _speak_with_backend(self, text):
        preferred = self.tts_backend
        if preferred == "piper":
            self._speak_piper(text)
            return

        if preferred == "edge":
            if self.local_only:
                raise RuntimeError("edge backend is disabled when GAMERCAT_LOCAL_ONLY=1")
            try:
                self._speak_edge(text)
                return
            except Exception as e:
                raise RuntimeError(f"edge backend failed: {e}") from e

        if preferred == "powershell":
            self._speak_powershell(text)
            return

        if preferred == "pyttsx3":
            try:
                self._ensure_tts_engine()
                self._engine.say(text)
                self._engine.runAndWait()
                return
            except Exception as e:
                raise RuntimeError(f"pyttsx3 failed: {e}") from e

        if self.piper_model:
            try:
                self._speak_piper(text)
                return
            except Exception as e:
                next_backend = "pyttsx3" if self.local_only else "edge-tts"
                print(f"[TTS Warning] piper unavailable/failed: {e}. Trying {next_backend}.")
        elif not self.is_windows:
            if not self._piper_warned:
                print("[TTS Warning] GAMERCAT_TTS_PIPER_MODEL is not set. Falling back from piper.")
                self._piper_warned = True

        if self._edge_enabled:
            try:
                self._speak_edge(text)
                return
            except Exception as e:
                self._edge_enabled = False
                if not self._edge_warned:
                    next_backend = "Windows SAPI" if self.is_windows else "pyttsx3"
                    print(f"[TTS Warning] edge-tts unavailable/failed: {e}. Trying {next_backend}.")
                    self._edge_warned = True

        if self.is_windows:
            try:
                self._speak_powershell(text)
                return
            except Exception as e:
                print(f"[TTS Warning] PowerShell SAPI failed: {e}. Trying pyttsx3.")

        try:
            self._ensure_tts_engine()
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            if self.local_only and not self._local_tts_warned:
                print("[TTS Warning] Local TTS failed. Install espeak-ng or configure Piper model.")
                self._local_tts_warned = True
            raise RuntimeError(f"All TTS backends failed: {e}") from e

    def _tts_worker(self):
        """Dedicated worker thread for TTS playback."""
        if pythoncom is not None:
            pythoncom.CoInitialize()

        try:
            while True:
                text = self.tts_queue.get()
                if text is None:
                    self.tts_queue.task_done()
                    break

                clean_text = text

                # Diagnostic: Beep before speaking
                # winsound.Beep(440, 100) # 440Hz for 100ms

                print(f"GamerCat (Speaking): {clean_text}")
                try:
                    self.speaking_event.set()
                    self._speak_with_backend(clean_text)
                except Exception as e:
                    print(f"[TTS Warning] {e}")
                    if not self.tts_disabled:
                        self.tts_disabled = True
                        print("[TTS Warning] Disabling speech output until TTS is configured.")
                finally:
                    self.speaking_event.clear()
                    self._listen_block_until = time.time() + max(0.0, self.listen_resume_delay)
                    self._mark_speech_finished()
                    self.tts_queue.task_done()
        finally:
            if self._engine is not None:
                try:
                    self._engine.stop()
                except Exception:
                    pass
            if pythoncom is not None:
                pythoncom.CoUninitialize()

    def speak(self, text):
        """Adds text to the speech queue."""
        if self.tts_disabled:
            if not self._tts_disabled_warned:
                print("[TTS Warning] Speech output is disabled. Configure Piper or install espeak-ng.")
                self._tts_disabled_warned = True
            return
        self._mark_speech_queued()
        self.tts_queue.put(text)

    def _capture_and_transcribe(self, duration=5):
        if self._tts_active() or time.time() < self._listen_block_until:
            return ""
        if not self._record_lock.acquire(blocking=False):
            return ""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = None
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            self.listening_event.set()
            print(f"[Listen] Started recording user input ({duration:.1f}s window).")
            frames = []
            interrupted_by_tts = False
            for _ in range(0, int(RATE / CHUNK * duration)):
                if self.stop_event.is_set():
                    break
                # Abort current recording window if assistant starts speaking,
                # so we do not transcribe our own TTS output.
                if self._tts_active() or time.time() < self._listen_block_until:
                    interrupted_by_tts = True
                    break
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            print("[Listen] Stopped recording user input.")

            if interrupted_by_tts:
                return ""

            if not frames:
                return ""

            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
            transcribe_kwargs = {"beam_size": 5}
            if self.stt_language:
                transcribe_kwargs["language"] = self.stt_language
            segments, info = self.stt.transcribe(audio_data, **transcribe_kwargs)
            text = " ".join([segment.text for segment in segments])

            if not text.strip():
                return ""

            detected_language = (getattr(info, "language", "") or "").strip().lower()
            if (
                self.enforce_stt_language
                and self.stt_language
                and detected_language
                and detected_language != self.stt_language
            ):
                return ""

            if info.language_probability > self.stt_language_threshold:
                return text.strip()
            return ""
        except Exception as e:
            print(f"[Listen Error] {e}")
            return ""
        finally:
            self.listening_event.clear()
            if p is not None:
                try:
                    p.terminate()
                except Exception:
                    pass
            self._record_lock.release()

    def _listen_worker(self):
        while not self.stop_event.is_set():
            if self._tts_active() or time.time() < self._listen_block_until:
                time.sleep(0.2)
                continue
            text = self._capture_and_transcribe(duration=self.listen_duration)
            if text:
                if self.transcript_queue.full():
                    try:
                        self.transcript_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.transcript_queue.put_nowait(text)

    def poll_transcript(self):
        try:
            return self.transcript_queue.get_nowait()
        except queue.Empty:
            return ""

    def has_pending_transcript(self):
        return not self.transcript_queue.empty()

    def is_listening(self):
        return self.listening_event.is_set()

    def is_tts_busy(self):
        return self._tts_active()

    def listen_cooldown_remaining(self):
        return max(0.0, self._listen_block_until - time.time())

    def wait_until_tts_idle(self, timeout=None):
        if timeout is None:
            self.tts_queue.join()
            return True
        deadline = time.time() + max(0.0, float(timeout))
        while time.time() < deadline:
            if self.tts_queue.unfinished_tasks == 0 and not self.is_tts_busy():
                return True
            time.sleep(0.05)
        return False

    def listen(self, duration=5):
        """Listens for a specific duration and returns transcription."""
        return self._capture_and_transcribe(duration=duration)

    def close(self):
        self.stop_event.set()
        self.tts_queue.put(None)
        if self.listener_thread is not None:
            self.listener_thread.join(timeout=1)
        self.tts_thread.join(timeout=1)

if __name__ == "__main__":
    engine = VoiceEngine(background_listen=False)
    print("Testing audio...")
    if winsound is not None:
        winsound.Beep(1000, 200)
    engine.speak("Can you hear this? If not, we might need a different TTS library.")
    time.sleep(5)
    engine.close()
