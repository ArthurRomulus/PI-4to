from PyQt5.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from .admin_components import RoundedCard
from database.consultas import obtener_lista_usuarios


class UsersPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 14, 14, 14)

        title = QLabel("Historial de usuarios")
        title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700;")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "USUARIO", "TIPO", "FECHA"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet(
            """
            QTableWidget { border: none; background: transparent; font-size: 12px; color: #e2e8f0; }
            QHeaderView::section { background: transparent; color: #93c5fd; border: none; font-size: 11px; font-weight: 700; }
            """
        )

        inner.addWidget(title)
        inner.addWidget(self.table)
        lay.addWidget(card)

    def refresh_data(self):
        users = obtener_lista_usuarios()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(user.get("nombre", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(user.get("tipo_usuario", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(user.get("fecha_registro", ""))))
