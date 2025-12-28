import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

import lib.video_window as video_window


def main():
    app = QApplication(sys.argv)
    
    # Modern dark theme is now applied via stylesheet in VideoWindow
    player = video_window.VideoWindow()
    
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
