from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QComboBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import Database
from app.models.project import ProjectInput


class GenerationWorker(QObject):
    status = Signal(str)
    finished = Signal(str, str)
    error = Signal(str)

    def __init__(self, project: ProjectInput, database: Database) -> None:
        super().__init__()
        self.project = project
        self.database = database

    @Slot()
    def run(self) -> None:
        try:
            from app.services.video_builder import VideoBuilder

            result = VideoBuilder().build(self.project, status=self.status.emit)
            self.database.save_project(self.project.product_name, result.script, result.output_video_path)
            self.finished.emit(str(result.output_video_path), result.script)
        except Exception as exc:
            details = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self.error.emit(details)


class MainWindow(QMainWindow):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.worker_thread: QThread | None = None
        self.worker: GenerationWorker | None = None

        self.setWindowTitle("AI Affiliate Video Builder")
        self.resize(900, 760)

        self.product_name_input = QLineEdit()
        self.benefits_input = QTextEdit()
        self.benefits_input.setMinimumHeight(90)
        self.target_audience_input = QLineEdit()
        self.video_style_input = QComboBox()
        self.video_style_input.setEditable(True)
        self.video_style_input.addItems(
            [
                "Review chân thật, nhanh gọn",
                "Năng động kiểu TikTok",
                "Sang trọng, đáng tin",
                "Khẩn cấp, tập trung ưu đãi",
            ]
        )
        self.cta_input = QLineEdit("Nhấn vào link để xem ưu đãi hôm nay.")
        self.background_video_input = QLineEdit()
        self.output_folder_input = QLineEdit()

        self.generate_button = QPushButton("Generate Video")
        self.generate_button.clicked.connect(self.generate_video)

        self.status_output = QPlainTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setMinimumHeight(150)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self._build_layout()
        self._apply_styles()

    def _build_layout(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        title = QLabel("AI Affiliate Video Builder")
        title.setObjectName("Title")
        subtitle = QLabel("Create one vertical affiliate video from product info and a background clip.")
        subtitle.setObjectName("Subtitle")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)
        form.addRow("Product name", self.product_name_input)
        form.addRow("Product benefits", self.benefits_input)
        form.addRow("Target audience", self.target_audience_input)
        form.addRow("Video style", self.video_style_input)
        form.addRow("CTA text", self.cta_input)
        form.addRow("Background video", self._file_picker_row(self.background_video_input, self.pick_background_video))
        form.addRow("Output folder", self._file_picker_row(self.output_folder_input, self.pick_output_folder))

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(form)
        root_layout.addWidget(self.generate_button)
        root_layout.addWidget(self.progress_bar)
        root_layout.addWidget(QLabel("Status"))
        root_layout.addWidget(self.status_output)

        self.setCentralWidget(root)

    def _file_picker_row(self, line_edit: QLineEdit, callback) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(callback)

        layout.addWidget(line_edit, 1)
        layout.addWidget(browse_button)
        return widget

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f7f7f8;
            }
            QLabel#Title {
                color: #202124;
                font-size: 26px;
                font-weight: 700;
            }
            QLabel#Subtitle {
                color: #5f6368;
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background: #ffffff;
                border: 1px solid #d7d9df;
                border-radius: 6px;
                padding: 8px;
                color: #202124;
                selection-background-color: #2563eb;
            }
            QPushButton {
                background: #2563eb;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 600;
                padding: 10px 14px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #9ca3af;
            }
            QProgressBar {
                background: #e5e7eb;
                border: none;
                border-radius: 4px;
                min-height: 8px;
            }
            QProgressBar::chunk {
                background: #16a34a;
                border-radius: 4px;
            }
            """
        )

    @Slot()
    def pick_background_video(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select background video",
            str(Path.home()),
            "Video Files (*.mp4 *.mov *.mkv *.avi);;All Files (*)",
        )
        if file_path:
            self.background_video_input.setText(file_path)

    @Slot()
    def pick_output_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Select output folder", str(Path.home()))
        if folder_path:
            self.output_folder_input.setText(folder_path)

    @Slot()
    def generate_video(self) -> None:
        try:
            project = self._collect_project_input()
        except ValueError as exc:
            QMessageBox.warning(self, "Missing information", str(exc))
            return

        self.status_output.clear()
        self._append_status("Starting generation...")
        self._set_busy(True)

        self.worker_thread = QThread(self)
        self.worker = GenerationWorker(project, self.database)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.status.connect(self._append_status)
        self.worker.finished.connect(self._generation_finished)
        self.worker.error.connect(self._generation_failed)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self._generation_thread_finished)

        self.worker_thread.start()

    def _collect_project_input(self) -> ProjectInput:
        product_name = self.product_name_input.text().strip()
        benefits = self.benefits_input.toPlainText().strip()
        target_audience = self.target_audience_input.text().strip()
        video_style = self.video_style_input.currentText().strip()
        cta_text = self.cta_input.text().strip()
        background_video_path = Path(self.background_video_input.text().strip()).expanduser()
        output_folder = Path(self.output_folder_input.text().strip()).expanduser()

        if not product_name:
            raise ValueError("Please enter a product name.")
        if not benefits:
            raise ValueError("Please enter product benefits.")
        if not background_video_path.is_file():
            raise ValueError("Please select a valid background video file.")
        if not output_folder.exists() or not output_folder.is_dir():
            raise ValueError("Please select a valid output folder.")
        try:
            test_file = output_folder / ".aivb_write_test"
            test_file.write_text("", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except OSError as exc:
            raise ValueError("The selected output folder is not writable.") from exc

        return ProjectInput(
            product_name=product_name,
            product_benefits=benefits,
            target_audience=target_audience,
            video_style=video_style,
            cta_text=cta_text,
            background_video_path=background_video_path,
            output_folder=output_folder,
        )

    @Slot(str)
    def _append_status(self, message: str) -> None:
        self.status_output.appendPlainText(message)

    @Slot(str, str)
    def _generation_finished(self, video_path: str, script: str) -> None:
        self._append_status("")
        self._append_status(f"Done: {video_path}")
        self._append_status("")
        self._append_status("Generated script:")
        self._append_status(script)
        QMessageBox.information(self, "Video generated", f"Saved MP4:\n{video_path}")

    @Slot(str)
    def _generation_failed(self, message: str) -> None:
        self._append_status(f"Error: {message}")
        QMessageBox.critical(self, "Generation failed", message)

    def _set_busy(self, busy: bool) -> None:
        self.generate_button.setEnabled(not busy)
        if busy:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)

    @Slot()
    def _generation_thread_finished(self) -> None:
        self._set_busy(False)
        self.worker = None
        self.worker_thread = None

    def closeEvent(self, event) -> None:
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(
                self,
                "Generation in progress",
                "Please wait for the current video generation to finish before closing the app.",
            )
            event.ignore()
            return

        super().closeEvent(event)
