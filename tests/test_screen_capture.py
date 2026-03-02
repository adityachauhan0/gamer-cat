import pytest

import screen_capture as sc


def test_detect_backends_wayland(monkeypatch):
    monkeypatch.setenv("GAMERCAT_CAPTURE_BACKEND", "auto")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert sc.detect_capture_backends() == ["wayland"]


def test_detect_backends_wayland_with_x11_fallback(monkeypatch):
    monkeypatch.setenv("GAMERCAT_CAPTURE_BACKEND", "auto")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("GAMERCAT_ALLOW_X11_ON_WAYLAND", "1")
    assert sc.detect_capture_backends() == ["wayland", "x11"]


def test_invalid_capture_backend(monkeypatch):
    monkeypatch.setenv("GAMERCAT_CAPTURE_BACKEND", "invalid")
    with pytest.raises(ValueError):
        sc.detect_capture_backends()


def test_capture_fallback_chain(monkeypatch):
    monkeypatch.setenv("GAMERCAT_CAPTURE_BACKEND", "auto")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("GAMERCAT_ALLOW_X11_ON_WAYLAND", "1")
    order = []

    def fail_wayland():
        order.append("wayland")
        raise RuntimeError("wayland failed")

    def fail_x11():
        order.append("x11")
        raise RuntimeError("x11 failed")

    monkeypatch.setattr(sc, "_capture_wayland", fail_wayland)
    monkeypatch.setattr(sc, "_capture_x11", fail_x11)

    with pytest.raises(RuntimeError):
        sc.capture_screen()
    assert order == ["wayland", "x11"]
