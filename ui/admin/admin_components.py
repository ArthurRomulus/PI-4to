import os
from PyQt5.QtWidgets import QFrame


def asset_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)


class RoundedCard(QFrame):
    def __init__(self, radius=18, color="#0f172a", border="#1e293b"):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {color};
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
            """
        )
