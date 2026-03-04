"""Claude Code 完了通知サウンド（Windows 用）.

Stop イベントで呼び出され、短いビープ音を鳴らす。
環境変数 CLAUDE_NOTIFY_SOUND=0 で無効化可能。
"""

import os
import sys


def main() -> None:
    if os.environ.get("CLAUDE_NOTIFY_SOUND") == "0":
        sys.exit(0)

    try:
        import winsound

        winsound.Beep(880, 200)  # A5, 200ms
    except Exception:
        # winsound が使えない環境（WSL等）では無視
        pass


if __name__ == "__main__":
    main()
