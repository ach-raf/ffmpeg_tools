import sys
from PySide6.QtWidgets import QApplication

import lib.video_window as video_window


def main():
    app = QApplication(sys.argv)

    player = video_window.VideoWindow(app)
    # player.resize(640, 480)
    if len(sys.argv) > 1:
        # I used replace because os.path.normpath is not working for some reason
        _clean_path = sys.argv[1].replace("\\", "/")
        player.media_info.file_location = _clean_path
        player.show()
        player.set_media()
    else:
        player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
