import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from database.consultas import (
    contar_accesos_hoy,
    contar_usuarios_registrados,
    obtener_historial_accesos,
)
from .admin_components import RoundedCard, asset_path


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 16)
        root.setSpacing(14)

        banner = RoundedCard(radius=20, color="#4E8EF7", border="#4E8EF7")
        banner.setFixedHeight(96)

        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(22, 14, 18, 14)
        banner_layout.setSpacing(4)

        title = QLabel("Bienvenido al panel de administrador")
        title.setStyleSheet(
            """
            color: white;
            font-size: 16px;
            font-weight: 800;
            border: none;
            background: transparent;
            """
        )

        subtitle = QLabel("Aqui puedes administrar usuarios y revisar accesos")
        subtitle.setStyleSheet(
            """
            color: rgba(255,255,255,0.95);
            font-size: 11px;
            font-weight: 500;
            border: none;
            background: transparent;
            """
        )

        banner_layout.addWidget(title)
        banner_layout.addWidget(subtitle)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.detected_card = self.stat_card("face_id.png", "Rostros Detectados", "0")
        self.users_card = self.stat_card("user_add.png", "Nuevos Registros", "0")
        self.detected_value = self.detected_card.findChild(QLabel, "value_label")
        self.users_value = self.users_card.findChild(QLabel, "value_label")

        stats_row.addWidget(self.detected_card)
        stats_row.addWidget(self.users_card)

        recent_card = RoundedCard(radius=18, color="#111827", border="#1f2937")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(14, 10, 14, 12)
        recent_layout.setSpacing(8)

        left_hdr = QLabel("ACCESOS\nRECIENTES")
        left_hdr.setStyleSheet(
            """
            color: #93c5fd;
            font-size: 10px;
            font-weight: 800;
            border: none;
            background: transparent;
            """
        )

        recent_layout.addWidget(left_hdr)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["USUARIO", "ESTADO", "HORA"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMinimumHeight(250)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background: transparent;
                border: none;
                font-size: 11px;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background: transparent;
                border: none;
                color: #93c5fd;
                font-size: 10px;
                font-weight: 800;
                padding: 8px 4px;
            }
            """
        )

        recent_layout.addWidget(self.table)

        root.addWidget(banner)
        root.addLayout(stats_row)
        root.addWidget(recent_card)

    def stat_card(self, icon_file, title, value):
        card = RoundedCard(radius=16, color="#111827", border="#1f2937")
        card.setFixedHeight(138)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        icon_box = QLabel()
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet(
            """
            background: #0b1736;
            border: 1px solid #1e3a8a;
            border-radius: 12px;
            """
        )

        icon_full_path = asset_path(icon_file)
        if os.path.exists(icon_full_path):
            pix = QPixmap(icon_full_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            white_icon = QPixmap(pix.size())
            white_icon.fill(Qt.transparent)
            painter = QPainter(white_icon)
            painter.drawPixmap(0, 0, pix)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(white_icon.rect(), Qt.white)
            painter.end()
            icon_box.setPixmap(white_icon)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color: #93c5fd; font-size: 11px; font-weight: 600; border: none; background: transparent;"
        )

        value_lbl = QLabel(value)
        value_lbl.setObjectName("value_label")
        value_lbl.setStyleSheet(
            "color: #f8fafc; font-size: 24px; font-weight: 800; border: none; background: transparent;"
        )

        top_row.addWidget(icon_box, alignment=Qt.AlignLeft)
        top_row.addStretch()

        lay.addLayout(top_row)
        lay.addWidget(title_lbl)
        lay.addStretch()
        lay.addWidget(value_lbl, alignment=Qt.AlignLeft | Qt.AlignBottom)

        return card

    def refresh_data(self):
        self.users_value.setText(str(contar_usuarios_registrados()))
        self.detected_value.setText(str(contar_accesos_hoy()))

        logs = obtener_historial_accesos(limite=6)
        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            nombre = str(log.get("nombre", ""))
            estado = str(log.get("status", ""))
            fecha = str(log.get("fecha", ""))
            hora = fecha.split(" ")[-1] if " " in fecha else fecha

            self.table.setItem(row, 0, QTableWidgetItem(nombre))
            self.table.setItem(row, 1, QTableWidgetItem(estado))
            self.table.setItem(row, 2, QTableWidgetItem(hora))
