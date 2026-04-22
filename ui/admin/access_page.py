from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHeaderView, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QPushButton,
)
from .admin_components import RoundedCard
from database.consultas import obtener_historial_accesos


class AccessPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(0)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 14, 14, 14)
        inner.setSpacing(8)

        # ── Encabezado ────────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        title = QLabel("🔓  Registro de acceso")
        title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700; border: none;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.refresh_btn = QPushButton("🔄  Actualizar")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0c4a6e;
                border: 1px solid #38bdf8;
                border-radius: 8px;
                color: #7dd3fc;
                font-size: 12px;
                font-weight: 700;
                padding: 0 14px;
            }
            QPushButton:hover { background-color: #0369a1; color: #ffffff; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(self.refresh_btn)

        # ── Tabla ─────────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "USUARIO", "ESTADO", "FECHA / HORA"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none; background: transparent;
                font-size: 12px; color: #e2e8f0; gridline-color: #1e293b;
            }
            QHeaderView::section {
                background: transparent; color: #93c5fd; border: none;
                font-size: 11px; font-weight: 700; padding: 4px 0;
            }
            QTableWidget::item { padding: 4px 8px; }
        """)

        inner.addLayout(header_row)
        inner.addWidget(self.table)
        lay.addWidget(card)

    def refresh_data(self):
        logs = obtener_historial_accesos(limite=200)
        self.table.setRowCount(0)
        for row_idx, log in enumerate(logs):
            self.table.insertRow(row_idx)
            status = str(log.get("status", ""))
            nombre = str(log.get("nombre") or "Desconocido")

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(log.get("id", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(nombre))

            # Estado coloreado
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if status == "AUTHORIZED":
                status_item.setForeground(
                    __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#22c55e")
                )
                status_item.setText("✅ AUTORIZADO")
            else:
                status_item.setForeground(
                    __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#f87171")
                )
                status_item.setText("❌ DENEGADO")
            self.table.setItem(row_idx, 2, status_item)

            self.table.setItem(row_idx, 3, QTableWidgetItem(str(log.get("fecha", ""))))

        self.table.resizeRowsToContents()
