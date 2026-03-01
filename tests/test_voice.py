from src.voice_engine import VoiceEngine
import time

def test_voice_loop():
    print("--- Voice Engine Test ---")
    engine = VoiceEngine(stt_model="tiny", background_listen=False) # Using 'tiny' for speed during testing
    
    # Test Speak
    test_phrase = "Testing voice output. Can you hear me?"
    print(f"Should say: {test_phrase}")
    engine.speak(test_phrase)
    
    # Wait for speech to finish (as it's in a thread)
    time.sleep(4)
    
    # Test Listen
    print("\n--- Listen Test ---")
    print("Please say 'Hello Gamer Cat' clearly.")
    transcription = engine.listen(duration=5)
    print(f"Transcribed: {transcription}")
    
    if "hello" in transcription.lower():
        print("SUCCESS: Transcription matches expected phrase.")
        engine.speak("I heard you loud and clear!")
    else:
        print("FAILURE: Transcription did not match.")
        engine.speak(f"I heard {transcription}, but I was expecting hello.")
    engine.close()

if __name__ == "__main__":
    test_voice_loop()
