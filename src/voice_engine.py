import pyttsx3
import threading
import queue
from faster_whisper import WhisperModel
import pyaudio
import numpy as np
import time
import pythoncom
import winsound # To test system audio

class VoiceEngine:
    def __init__(self, stt_model="tiny"):
        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        print(f"Loading Whisper model '{stt_model}'...")
        self.stt = WhisperModel(stt_model, device="cpu", compute_type="int8")

    def _tts_worker(self):
        """Dedicated thread for pyttsx3 with SAPI5 explicit init."""
        pythoncom.CoInitialize()
        
        try:
            # Explicitly use sapi5 engine for Windows
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', 180) 
            engine.setProperty('volume', 1.0)
            
            voices = engine.getProperty('voices')
            if voices:
                print(f"[TTS] SAPI5 initialized. Voice: {voices[0].name}")
            
            while True:
                text = self.tts_queue.get()
                if text is None: break
                
                clean_text = text.replace('"', '').replace("'", "")
                
                # Diagnostic: Beep before speaking
                # winsound.Beep(440, 100) # 440Hz for 100ms
                
                print(f"GamerCat (Speaking): {clean_text}")
                
                # Some Windows systems need the engine to be re-initialized 
                # or run in a very specific way. We'll try a small wait.
                engine.say(clean_text)
                engine.runAndWait()
                
                self.tts_queue.task_done()
        except Exception as e:
            print(f"[TTS Worker Error] {e}")
        finally:
            pythoncom.CoUninitialize()

    def speak(self, text):
        """Adds text to the speech queue."""
        self.tts_queue.put(text)

    def listen(self, duration=5):
        """Listens for a specific duration and returns transcription."""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
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

if __name__ == "__main__":
    engine = VoiceEngine()
    print("Testing audio...")
    winsound.Beep(1000, 200)
    engine.speak("Can you hear this? If not, we might need a different TTS library.")
    time.sleep(5)
