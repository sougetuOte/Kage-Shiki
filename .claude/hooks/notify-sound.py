"""Claude Code 通知サウンド（Windows 用）.

Stop / Notification イベントで呼び出され、wav を増幅再生する。
- Stop（完了）: tada.wav
- Notification（承認待ち）: Windows Exclamation.wav
環境変数 CLAUDE_NOTIFY_SOUND=0 で無効化可能。
"""

import os
import struct
import sys
import tempfile
import wave

SOUNDS = {
    "stop": r"C:\Windows\Media\tada.wav",
    "notification": r"C:\Windows\Media\Windows Exclamation.wav",
}
GAIN = 4.0


def _play_amplified(src: str, gain: float = GAIN) -> None:
    import winsound

    with wave.open(src, "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())

    samples = struct.unpack(f"<{len(frames) // 2}h", frames)
    amplified = struct.pack(
        f"<{len(samples)}h",
        *[max(-32768, min(32767, int(s * gain))) for s in samples],
    )

    tmp = os.path.join(tempfile.gettempdir(), "claude_notify.wav")
    with wave.open(tmp, "wb") as w:
        w.setparams(params)
        w.writeframes(amplified)

    winsound.PlaySound(tmp, winsound.SND_FILENAME)


def main() -> None:
    if os.environ.get("CLAUDE_NOTIFY_SOUND") == "0":
        sys.exit(0)

    event = sys.argv[1] if len(sys.argv) > 1 else "stop"
    src = SOUNDS.get(event, SOUNDS["stop"])

    try:
        _play_amplified(src)
    except Exception:
        pass


if __name__ == "__main__":
    main()
