import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from qtmodern.styles import dark
from qtmodern.windows import ModernWindow

import lib.video_window as video_window


def main():
    app = QApplication(sys.argv)
    dark(app)

    player = video_window.VideoWindow()
    # player = ModernWindow(video_window.VideoWindow())
    # player.resize(640, 480)
    if len(sys.argv) > 1:
        # I used replace because os.path.normpath(sys.argv[1]) is not working for some reason
        player.media_info.file_location = Path(sys.argv[1]).absolute().as_posix()
        player.show()
        player.set_media()
    else:
        player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
