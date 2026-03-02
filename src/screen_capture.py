import base64
import io
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageGrab

SUPPORTED_BACKENDS = {"auto", "wayland", "x11", "pil"}
AUTO_DISABLED_BACKENDS = set()


def _encode_image(image):
    max_dim_raw = os.getenv("GAMERCAT_CAPTURE_MAX_DIM", "1280").strip()
    try:
        max_dim = max(256, int(max_dim_raw))
    except ValueError:
        max_dim = 1280
    if max(image.size) > max_dim:
        image = image.copy()
        image.thumbnail((max_dim, max_dim))
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=80)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def _looks_uniform(image):
    sample = image.convert("RGB").resize((64, 64))
    extrema = sample.getextrema()
    return all(channel_min == channel_max for channel_min, channel_max in extrema)


def _capture_from_command(command):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image_path = tmp.name
    try:
        completed = subprocess.run(
            command + [image_path],
            check=True,
            timeout=12,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        with Image.open(image_path) as img:
            converted = img.convert("RGB")
            if _looks_uniform(converted):
                raise RuntimeError(
                    "Captured a uniform image (likely blocked by compositor capture permissions)."
                )
            return converted
    except subprocess.CalledProcessError as err:
        stderr = (err.stderr or "").strip()
        stdout = (err.stdout or "").strip()
        detail = stderr or stdout or str(err)
        raise RuntimeError(detail) from err
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass


def _capture_wayland():
    desktop = os.getenv("XDG_CURRENT_DESKTOP", "").lower()
    if "kde" in desktop:
        commands = [["spectacle", "-b", "-n", "-o"], ["gnome-screenshot", "-f"], ["grim"]]
    elif "gnome" in desktop:
        commands = [["gnome-screenshot", "-f"], ["grim"], ["spectacle", "-b", "-n", "-o"]]
    else:
        commands = [["grim"], ["gnome-screenshot", "-f"], ["spectacle", "-b", "-n", "-o"]]
    last_error = None
    for command in commands:
        if shutil.which(command[0]) is None:
            continue
        try:
            return _capture_from_command(command)
        except Exception as err:
            last_error = err
    if last_error is not None:
        raise RuntimeError(f"Wayland capture failed: {last_error}") from last_error
    raise RuntimeError("No Wayland capture tool found. Install grim or gnome-screenshot.")


def _capture_x11():
    if not os.getenv("DISPLAY"):
        raise RuntimeError("DISPLAY is not set; X11 capture is unavailable in this session.")
    commands = [
        ["maim"],
        ["import", "-window", "root"],
        ["scrot"],
    ]
    last_error = None
    for command in commands:
        if shutil.which(command[0]) is None:
            continue
        try:
            return _capture_from_command(command)
        except Exception as err:
            last_error = err
    if last_error is not None:
        raise RuntimeError(f"X11 capture failed: {last_error}") from last_error
    raise RuntimeError("No X11 capture tool found. Install maim, imagemagick, or scrot.")


def _capture_pil():
    return ImageGrab.grab()


def detect_capture_backends():
    configured = os.getenv("GAMERCAT_CAPTURE_BACKEND", "auto").strip().lower()
    if configured not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"Invalid GAMERCAT_CAPTURE_BACKEND={configured!r}. "
            "Expected one of: auto, wayland, x11, pil."
        )

    if configured != "auto":
        return [configured]

    session = os.getenv("XDG_SESSION_TYPE", "").strip().lower()
    if session == "wayland" or os.getenv("WAYLAND_DISPLAY"):
        if os.getenv("GAMERCAT_ALLOW_X11_ON_WAYLAND", "").strip() == "1":
            return ["wayland", "x11"]
        return ["wayland"]
    if session == "x11" or os.getenv("DISPLAY"):
        return ["x11", "pil", "wayland"]
    return ["wayland", "x11", "pil"]


def capture_screen():
    """Capture the active screen and return it as base64 JPEG."""
    handlers = {
        "wayland": _capture_wayland,
        "x11": _capture_x11,
        "pil": _capture_pil,
    }
    backends = detect_capture_backends()
    configured = os.getenv("GAMERCAT_CAPTURE_BACKEND", "auto").strip().lower()
    if configured == "auto":
        backends = [b for b in backends if b not in AUTO_DISABLED_BACKENDS]
        if not backends:
            raise RuntimeError(
                "All auto-detected screen capture backends are disabled due to repeated failures. "
                "Set GAMERCAT_CAPTURE_BACKEND explicitly after installing a compatible backend."
            )
    errors = []
    for backend in backends:
        try:
            screenshot = handlers[backend]()
            return _encode_image(screenshot)
        except Exception as err:
            detail = f"{backend}: {err}"
            errors.append(detail)
            message = str(err).lower()
            if configured == "auto" and (
                "not set" in message
                or "unsupported" in message
                or "no wayland capture tool found" in message
                or "no x11 capture tool found" in message
                or "compositor doesn't support the screen capture protocol" in message
                or "missing an image filename" in message
                or "cannot identify image file" in message
                or "uniform image" in message
            ):
                AUTO_DISABLED_BACKENDS.add(backend)

    details = "; ".join(errors)
    raise RuntimeError(
        "Screen capture failed across all backends. "
        f"Tried: {', '.join(backends)}. Errors: {details}"
    )


if __name__ == "__main__":
    print("Testing screen capture...")
    img_b64 = capture_screen()
    print(f"Captured screen, base64 length: {len(img_b64)}")
