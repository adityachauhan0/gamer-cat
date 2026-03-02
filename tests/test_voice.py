import voice_engine as ve


class DummyWhisperModel:
    def __init__(self, *_args, **_kwargs):
        pass


def _new_voice_engine(monkeypatch):
    monkeypatch.setattr(ve, "WhisperModel", DummyWhisperModel)
    return ve.VoiceEngine(background_listen=False)


def test_voice_engine_imports_cross_platform():
    assert ve is not None


def test_auto_backend_prefers_piper_when_configured(monkeypatch):
    engine = _new_voice_engine(monkeypatch)
    try:
        engine.piper_model = "/tmp/fake-model.onnx"
        called = []

        def mark_piper(_text):
            called.append("piper")

        monkeypatch.setattr(engine, "_speak_piper", mark_piper)
        monkeypatch.setattr(engine, "_speak_edge", lambda _text: called.append("edge"))
        monkeypatch.setattr(engine, "_ensure_tts_engine", lambda: called.append("pyttsx3"))
        engine._speak_with_backend("hello")
        assert called[0] == "piper"
    finally:
        engine.close()
