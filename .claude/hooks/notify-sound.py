"""Claude Code 通知サウンド（Windows 用）.

Stop / Notification イベントで呼び出され、wav を増幅再生する。
- Stop（完了）: tada.wav
- Notification（承認待ち）: Windows Exclamation.wav
環境変数 CLAUDE_NOTIFY_SOUND=0 で無効化可能。
"""

import contextlib
import os
import struct
import sys
import tempfile
import wave

_MEDIA_DIR = os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "Media")
SOUNDS = {
    "stop": os.path.join(_MEDIA_DIR, "tada.wav"),
    "notification": os.path.join(_MEDIA_DIR, "Windows Exclamation.wav"),
}
GAIN = 4.0
DEFAULT_EVENT = "stop"


def _play_amplified(src: str, gain: float = GAIN) -> None:
    import winsound

    with wave.open(src, "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())

    # 16bit (sampwidth=2) のみ増幅、それ以外はそのまま再生
    if params.sampwidth != 2:
        winsound.PlaySound(src, winsound.SND_FILENAME)
        return

    samples = struct.unpack(f"<{len(frames) // 2}h", frames)
    amplified = struct.pack(
        f"<{len(samples)}h",
        *[max(-32768, min(32767, int(s * gain))) for s in samples],
    )

    fd, tmp = tempfile.mkstemp(suffix=".wav")
    try:
        os.close(fd)
        with wave.open(tmp, "wb") as w:
            w.setparams(params)
            w.writeframes(amplified)
        winsound.PlaySound(tmp, winsound.SND_FILENAME)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)


def main() -> None:
    if os.environ.get("CLAUDE_NOTIFY_SOUND") == "0":
        sys.exit(0)

    event = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EVENT
    src = SOUNDS.get(event, SOUNDS[DEFAULT_EVENT])

    with contextlib.suppress(Exception):
        _play_amplified(src)


if __name__ == "__main__":
    main()
