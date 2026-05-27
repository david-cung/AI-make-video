from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QComboBox,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import Database
from app.models.project import ProjectInput
from app.services.templates import get_template, template_names
from app.utils.logging_config import current_log_file


logger = logging.getLogger(__name__)


class GenerationWorker(QObject):
    status = Signal(str)
    progress = Signal(int)
    script_ready = Signal(str)
    finished = Signal(str, str, str)
    error = Signal(str)

    def __init__(self, project: ProjectInput, database: Database) -> None:
        super().__init__()
        self.project = project
        self.database = database

    @Slot()
    def run(self) -> None:
        try:
            from app.services.video_builder import VideoBuilder

            result = VideoBuilder().build(
                self.project,
                status=self.status.emit,
                progress=self.progress.emit,
                script_ready=self.script_ready.emit,
            )

            self.status.emit("Saving project")
            self.progress.emit(95)
            self.database.save_project(self.project.product_name, result.script, result.output_video_path)

            self.status.emit("Done")
            self.progress.emit(100)
            self.finished.emit(str(result.output_video_path), str(result.project_folder), result.script)
        except Exception as exc:
            logger.exception("Generation failed")
            self.error.emit(self._friendly_error(exc))

    def _friendly_error(self, exc: Exception) -> str:
        message = str(exc).strip() or "Generation failed unexpectedly."
        return f"{message}\n\nTechnical details were saved to:\n{current_log_file()}"


class MainWindow(QMainWindow):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.worker_thread: QThread | None = None
        self.worker: GenerationWorker | None = None
        self.active_template_name = ""

        self.setWindowTitle("AI Affiliate Video Builder")
        self.resize(980, 920)

        self.product_name_input = QLineEdit()
        self.benefits_input = QTextEdit()
        self.benefits_input.setMinimumHeight(96)
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
        self.video_template_input = QComboBox()
        self.video_template_input.addItems(template_names())
        self.cta_input = QLineEdit("Nhấn vào link để xem ưu đãi hôm nay.")

        self.background_video_input = QLineEdit()
        self.output_folder_input = QLineEdit()

        self.generate_button = QPushButton("Generate Video")
        self.generate_button.clicked.connect(self.generate_video)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")

        self.script_preview = QPlainTextEdit()
        self.script_preview.setReadOnly(True)
        self.script_preview.setMinimumHeight(120)
        self.script_preview.setPlaceholderText("Generated script will appear here after the script step finishes.")

        self.status_output = QPlainTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setMinimumHeight(120)
        self.status_output.setPlaceholderText("Step-by-step generation messages will appear here.")

        self._build_layout()
        self._apply_styles()

    def _build_layout(self) -> None:
        content = QWidget()
        root_layout = QVBoxLayout(content)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        title = QLabel("AI Affiliate Video Builder")
        title.setObjectName("Title")
        subtitle = QLabel("Generate one vertical affiliate video from product info and a background clip.")
        subtitle.setObjectName("Subtitle")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(self._product_info_section())
        root_layout.addWidget(self._video_settings_section())
        root_layout.addWidget(self._files_section())
        root_layout.addWidget(self._generation_status_section())

        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        self.setCentralWidget(scroll_area)

    def _product_info_section(self) -> QGroupBox:
        form = self._section_form()
        form.addRow("Product name", self.product_name_input)
        form.addRow("Product benefits", self.benefits_input)
        form.addRow("Target audience", self.target_audience_input)
        return self._section("Product Info", form)

    def _video_settings_section(self) -> QGroupBox:
        form = self._section_form()
        form.addRow("Video Template", self.video_template_input)
        form.addRow("Video style", self.video_style_input)
        form.addRow("CTA text", self.cta_input)
        return self._section("Video Settings", form)

    def _files_section(self) -> QGroupBox:
        layout = self._section_form()
        layout.addRow("Background video", self._file_picker_row(self.background_video_input, self.pick_background_video))
        layout.addRow("Output folder", self._file_picker_row(self.output_folder_input, self.pick_output_folder))
        layout.addRow("", self.generate_button)
        return self._section("Files", layout)

    def _generation_status_section(self) -> QGroupBox:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("Script Preview"))
        layout.addWidget(self.script_preview)
        layout.addWidget(QLabel("Generation Status"))
        layout.addWidget(self.status_output)

        return self._section("Generation Status", layout)

    def _section_form(self) -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)
        return form

    def _section(self, title: str, layout) -> QGroupBox:
        group = QGroupBox(title)
        group.setLayout(layout)
        return group

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
                background: #f6f7f9;
            }
            QScrollArea {
                background: #f6f7f9;
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
            QLabel#StatusLabel {
                color: #111827;
                font-size: 15px;
                font-weight: 700;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #dde1e7;
                border-radius: 8px;
                color: #202124;
                font-size: 14px;
                font-weight: 700;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                background: #ffffff;
                border: 1px solid #d7d9df;
                border-radius: 6px;
                padding: 8px;
                color: #202124;
                font-weight: 400;
                selection-background-color: #2563eb;
            }
            QPlainTextEdit {
                font-family: Menlo, Consolas, monospace;
                font-size: 12px;
            }
            QPushButton {
                background: #2563eb;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 700;
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
                color: #111827;
                font-weight: 700;
                min-height: 18px;
                text-align: center;
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
        if self.worker_thread and self.worker_thread.isRunning():
            return

        try:
            project = self._collect_project_input()
        except ValueError as exc:
            self.status_label.setText("Input needs attention")
            QMessageBox.warning(self, "Invalid input", str(exc))
            return

        self.status_output.clear()
        self.script_preview.clear()
        self.progress_bar.setValue(0)
        self.active_template_name = project.video_template
        self._set_status("Starting generation")
        self._set_busy(True)

        self.worker_thread = QThread(self)
        self.worker = GenerationWorker(project, self.database)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.status.connect(self._set_status)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.script_ready.connect(self._script_ready)
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
        video_template = self.video_template_input.currentText().strip()
        cta_text = self.cta_input.text().strip()
        background_raw = self.background_video_input.text().strip()
        output_raw = self.output_folder_input.text().strip()

        if not product_name:
            raise ValueError("Please enter a product name.")
        if not benefits:
            raise ValueError("Please enter product benefits.")
        if not cta_text:
            raise ValueError("Please enter CTA text.")
        if not background_raw:
            raise ValueError("Please select a background video file.")
        if not output_raw:
            raise ValueError("Please select an output folder.")

        background_video_path = Path(background_raw).expanduser()
        output_folder = Path(output_raw).expanduser()

        if not background_video_path.is_file():
            raise ValueError("The selected background video file does not exist.")
        if not output_folder.exists() or not output_folder.is_dir():
            raise ValueError("The selected output folder does not exist.")
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
            video_template=video_template,
        )

    @Slot(str)
    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_output.appendPlainText(message)

    @Slot(str)
    def _script_ready(self, script: str) -> None:
        self.script_preview.setPlainText(self._format_script_preview(script))

    @Slot(str, str, str)
    def _generation_finished(self, video_path: str, project_folder: str, script: str) -> None:
        self.script_preview.setPlainText(self._format_script_preview(script))
        self.progress_bar.setValue(100)
        self._set_status("Done")
        self.status_output.appendPlainText("")
        self.status_output.appendPlainText(f"Project folder: {project_folder}")
        self.status_output.appendPlainText(f"Output video: {video_path}")
        QMessageBox.information(self, "Video generated", f"Saved MP4:\n{video_path}")

    @Slot(str)
    def _generation_failed(self, message: str) -> None:
        self.status_label.setText("Generation failed")
        self.status_output.appendPlainText("")
        self.status_output.appendPlainText(f"Error: {message}")
        QMessageBox.critical(self, "Generation failed", message)

    def _set_busy(self, busy: bool) -> None:
        self.generate_button.setEnabled(not busy)

    def _format_script_preview(self, script: str) -> str:
        template = get_template(self.active_template_name)
        return (
            f"Video Template: {template.name}\n"
            f"Template Structure: {template.structure_text}\n\n"
            f"{script}"
        )

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
