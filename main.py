import sys

from PySide6.QtWidgets import QApplication

from app.db.database import Database
from app.ui.main_window import MainWindow
from app.utils.logging_config import configure_logging


def main() -> int:
    configure_logging()

    app = QApplication(sys.argv)

    database = Database()
    database.initialize()

    window = MainWindow(database)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
