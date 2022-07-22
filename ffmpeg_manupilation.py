import sys
from PyQt5.QtWidgets import QApplication

import lib.video_window as video_window


def main():
    app = QApplication(sys.argv)

    player = video_window.VideoWindow(app)
    # player.resize(640, 480)
    if len(sys.argv) > 1:
        player.media_info.file_location = sys.argv[1]
        player.set_media()
    print(player.media_info.file_location)
    player.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
