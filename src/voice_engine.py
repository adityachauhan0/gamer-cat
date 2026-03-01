import pyttsx3
import threading
import queue
import subprocess
import os
import sys
import asyncio
import tempfile
import shutil
from faster_whisper import WhisperModel
import pyaudio
import numpy as np
import time
import pythoncom
import winsound  # To test system audio

try:
    import edge_tts
except Exception:
    edge_tts = None

class VoiceEngine:
    def __init__(self, stt_model="tiny", tts_backend="auto", background_listen=True, listen_duration=4):
        self.background_listen = background_listen
        self.listen_duration = listen_duration
        self.stop_event = threading.Event()
        self.transcript_queue = queue.Queue(maxsize=2)
        env_backend = os.getenv("GAMERCAT_TTS_BACKEND", "").strip().lower()
        self.tts_backend = env_backend if env_backend else tts_backend
        self.edge_voice = os.getenv("GAMERCAT_TTS_VOICE", "ja-JP-NanamiNeural")
        self.edge_rate = os.getenv("GAMERCAT_TTS_RATE", "+18%")
        self.edge_pitch = os.getenv("GAMERCAT_TTS_PITCH", "+7Hz")
        self.piper_exe = os.getenv("GAMERCAT_TTS_PIPER_EXE", "piper")
        self.piper_model = os.getenv("GAMERCAT_TTS_PIPER_MODEL", "").strip()
        self.piper_config = os.getenv("GAMERCAT_TTS_PIPER_CONFIG", "").strip()
        self.piper_length_scale = os.getenv("GAMERCAT_TTS_PIPER_LENGTH_SCALE", "0.95")
        self._engine = None
        self._edge_enabled = edge_tts is not None
        self._edge_warned = False

        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        print(f"Loading Whisper model '{stt_model}'...")
        self.stt = WhisperModel(stt_model, device="cpu", compute_type="int8")
        print(f"[TTS] Backend mode: {self.tts_backend}")
        self.listener_thread = None
        if self.background_listen:
            self.listener_thread = threading.Thread(target=self._listen_worker, daemon=True)
            self.listener_thread.start()

    def _speak_powershell(self, text):
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
            )
        finally:
            try:
                os.remove(out_path)
            except OSError:
                pass

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
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass

    def _ensure_tts_engine(self):
        if self._engine is None:
            self._engine = pyttsx3.init("sapi5")
            self._engine.setProperty("rate", 180)
            self._engine.setProperty("volume", 1.0)
            voices = self._engine.getProperty("voices")
            if voices:
                print(f"[TTS] SAPI5 initialized. Voice: {voices[0].name}")

    def _speak_with_backend(self, text):
        preferred = self.tts_backend
        if preferred == "piper":
            self._speak_piper(text)
            return

        if preferred == "edge":
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

        # auto: prefer piper only when explicitly configured, then edge-tts, then Windows SAPI, then pyttsx3
        if self.piper_model:
            try:
                self._speak_piper(text)
                return
            except Exception as e:
                print(f"[TTS Warning] piper unavailable/failed: {e}. Trying edge-tts.")

        if self._edge_enabled:
            try:
                self._speak_edge(text)
                return
            except Exception as e:
                self._edge_enabled = False
                if not self._edge_warned:
                    print(f"[TTS Warning] edge-tts unavailable/failed: {e}. Trying Windows SAPI.")
                    self._edge_warned = True

        if sys.platform == "win32":
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
            raise RuntimeError(f"All TTS backends failed: {e}") from e

    def _tts_worker(self):
        """Dedicated thread for pyttsx3 with SAPI5 explicit init."""
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

                self._speak_with_backend(clean_text)

                self.tts_queue.task_done()
        except Exception as e:
            print(f"[TTS Worker Error] {e}")
        finally:
            if self._engine is not None:
                try:
                    self._engine.stop()
                except Exception:
                    pass
            pythoncom.CoUninitialize()

    def speak(self, text):
        """Adds text to the speech queue."""
        self.tts_queue.put(text)

    def _capture_and_transcribe(self, duration=5):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                if self.stop_event.is_set():
                    break
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()

            if not frames:
                return ""

            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
            segments, info = self.stt.transcribe(audio_data, beam_size=5)
            text = " ".join([segment.text for segment in segments])

            if text.strip() and info.language_probability > 0.4:
                return text.strip()
            return ""
        except Exception as e:
            print(f"[Listen Error] {e}")
            return ""
        finally:
            p.terminate()

    def _listen_worker(self):
        while not self.stop_event.is_set():
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
    winsound.Beep(1000, 200)
    engine.speak("Can you hear this? If not, we might need a different TTS library.")
    time.sleep(5)
    engine.close()
