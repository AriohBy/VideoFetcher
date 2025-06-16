from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QGridLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QDialog,
    QDialogButtonBox,
    QProgressBar,
    QGraphicsOpacityEffect,
    QMessageBox,
    QTextEdit,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, Slot
import requests
from io import BytesIO
import certifi
from app.database import Database
from app.api import get_movies
import asyncio


class LoaderThread(QThread):
    progress = Signal(int)
    data_loaded = Signal(list)

    def __init__(self, page):
        super().__init__()
        self.page = page

    def run(self):
        movies = asyncio.run(get_movies(self.page))
        loaded_movies = []
        total = len(movies)
        for idx, movie in enumerate(movies, 1):
            if movie["poster_url"]:
                try:
                    response = requests.get(movie["poster_url"], verify=certifi.where())
                    pixmap = QPixmap()
                    pixmap.loadFromData(BytesIO(response.content).read())
                    movie["pixmap"] = pixmap
                except:
                    movie["pixmap"] = None
            else:
                movie["pixmap"] = None
            loaded_movies.append(movie)
            percent = int((idx / total) * 100)
            self.progress.emit(percent)
        self.data_loaded.emit(loaded_movies)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoFetcher")
        self.setGeometry(100, 100, 1000, 800)
        self.db = Database()
        self.page = 1
        self.is_favorites = False
        self.movies = []
        self.dark_mode = True

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Прогресс-бар с анимацией
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.hide()
        self.progress.setStyleSheet(
            """
            QProgressBar {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                width: 20px;
            }
        """
        )
        self.layout.addWidget(self.progress)

        self.opacity_effect = QGraphicsOpacityEffect(self.progress)
        self.progress.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.finished.connect(self.progress.hide)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_prev = QPushButton("← Предыдущая")
        self.btn_next = QPushButton("Следующая →")
        self.btn_fav = QPushButton("⭐ Избранное")
        self.btn_movies = QPushButton("🎬 Фильмы")
        self.btn_theme = QPushButton("🌙/☀ Тема")

        for btn in [
            self.btn_prev,
            self.btn_next,
            self.btn_fav,
            self.btn_movies,
            self.btn_theme,
        ]:
            btn.setStyleSheet("padding: 5px; border-radius: 5px;")

        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        self.btn_fav.clicked.connect(self.show_favorites)
        self.btn_movies.clicked.connect(self.show_movies)
        self.btn_theme.clicked.connect(self.toggle_theme)

        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_next)
        btn_layout.addWidget(self.btn_fav)
        btn_layout.addWidget(self.btn_movies)
        btn_layout.addWidget(self.btn_theme)
        self.layout.addLayout(btn_layout)

        self.apply_theme()
        self.load_movies()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(
                """
                QWidget { background-color: #121212; color: #eeeeee; }
                QPushButton {
                    background-color: #1f1f1f;
                    color: #eeeeee;
                    border: 1px solid #444;
                }
                QPushButton:hover { background-color: #333333; }
                QLabel { color: #eeeeee; }
            """
            )
        else:
            self.setStyleSheet(
                """
                QWidget { background-color: #ffffff; color: #000000; }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #000000;
                    border: 1px solid #aaa;
                }
                QPushButton:hover { background-color: #cccccc; }
                QLabel { color: #000000; }
            """
            )

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def load_movies(self):
        self.progress.show()
        self.opacity_effect.setOpacity(1.0)
        self.progress.setValue(0)
        self.is_favorites = False
        self.loader = LoaderThread(self.page)
        self.loader.progress.connect(self.progress.setValue)
        self.loader.data_loaded.connect(self.on_movies_loaded)
        self.loader.start()

    @Slot(list)
    def on_movies_loaded(self, movies):
        self.movies = movies
        self.refresh_grid()
        self.fade_out_progress()

    def fade_out_progress(self):
        self.fade_animation.stop()
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()

    def refresh_grid(self):
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        row = 0
        col = 0
        for movie in self.movies:
            box = QVBoxLayout()
            container = QWidget()
            poster_label = QLabel()

            if movie["pixmap"]:
                poster_label.setPixmap(
                    movie["pixmap"].scaled(150, 225, Qt.KeepAspectRatio)
                )
            else:
                poster_label.setText("Нет постера")

            poster_label.mousePressEvent = (
                lambda event, m=movie: self.show_description_popup(m)
            )

            box.addWidget(poster_label)
            title_lbl = QLabel(movie["title"])
            title_lbl.setStyleSheet("font-weight: bold; padding: 2px;")
            box.addWidget(title_lbl)

            btn_add = QPushButton("⭐ Добавить")
            btn_add.clicked.connect(lambda _, m=movie: self.add_fav_dialog(m))
            box.addWidget(btn_add)

            container.setLayout(box)
            self.grid.addWidget(container, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def add_fav_dialog(self, movie):
        note, ok = self.get_note_input()
        if ok:
            self.db.add_favorite(
                movie["id"],
                movie["title"],
                movie["description"],
                movie["poster_url"],
                note,
            )
            QMessageBox.information(
                self, "Добавлено", f"{movie['title']} добавлен в избранное."
            )

    def get_note_input(self):
        note_edit = QTextEdit()
        note_edit.setPlaceholderText("Введите комментарий...")
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Комментарий")
        dialog.setText("Добавить фильм в избранное?")
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = dialog.exec()
        if result == QMessageBox.Yes:
            return note_edit.toPlainText(), True
        return "", False

    def show_description_popup(self, movie):
        favs = self.db.get_favorites()
        user_note = None
        in_favorites = False

        for f in favs:
            if f[0] == movie["id"]:
                in_favorites = True
                user_note = f[4]
                break

        dialog = QDialog(self)
        dialog.setWindowTitle(movie["title"])
        layout = QVBoxLayout()

        desc_label = QLabel(movie["description"] or "Описание отсутствует.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(desc_label)

        if user_note:
            note_label = QLabel(f"Комментарий: {user_note}")
            note_label.setWordWrap(True)
            note_label.setStyleSheet("font-size: 12px; color: gray; padding: 5px;")
            layout.addWidget(note_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        if in_favorites:
            btn_remove = QPushButton("Удалить из избранного")
            btn_remove.clicked.connect(
                lambda: self.remove_from_favorites(movie["id"], dialog)
            )
            buttons.addButton(btn_remove, QDialogButtonBox.ActionRole)

        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec()

    def remove_from_favorites(self, movie_id, dialog):
        self.db.remove_favorite(movie_id)
        QMessageBox.information(self, "Удалено", "Фильм удалён из избранного.")
        dialog.accept()
        if self.is_favorites:
            self.show_favorites()

    def show_favorites(self):
        self.set_loading(False)
        self.is_favorites = True
        self.movies = []
        favs = self.db.get_favorites()
        for f in favs:
            self.movies.append(
                {
                    "id": f[0],
                    "title": f[1],
                    "description": f[2],
                    "poster_url": f[3],
                    "user_note": f[4],
                }
            )
        self.refresh_grid()

    def show_movies(self):
        self.load_movies()

    def next_page(self):
        if not self.is_favorites:
            self.page += 1
            self.load_movies()

    def prev_page(self):
        if not self.is_favorites and self.page > 1:
            self.page -= 1
            self.load_movies()
