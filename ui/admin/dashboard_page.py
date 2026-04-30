import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap, QColor, QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)

from database.consultas import (
    contar_accesos_hoy,
    contar_usuarios_registrados,
    obtener_historial_accesos,
)

from .admin_components import asset_path


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("DashboardPage")
        self.setStyleSheet("""
            QWidget#DashboardPage {
                background: #0b1220;
            }

            QLabel {
                background: transparent;
                border: none;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 18)
        root.setSpacing(14)

        # =====================================================
        # BANNER SUPERIOR
        # =====================================================
        banner = QFrame()
        banner.setObjectName("WelcomeBanner")
        banner.setFixedHeight(118)
        banner.setStyleSheet("""
            QFrame#WelcomeBanner {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:1,
                    stop:0 #053d3a,
                    stop:0.45 #06342f,
                    stop:1 #081821
                );
                border: 1px solid rgba(0, 240, 220, 0.28);
                border-radius: 16px;
            }
        """)

        banner_shadow = QGraphicsDropShadowEffect()
        banner_shadow.setBlurRadius(24)
        banner_shadow.setOffset(0, 10)
        banner_shadow.setColor(QColor(0, 0, 0, 120))
        banner.setGraphicsEffect(banner_shadow)

        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(20, 16, 20, 14)
        banner_layout.setSpacing(6)

        title = QLabel("Bienvenido al panel de\nadministrador")
        title.setWordWrap(True)
        title.setStyleSheet("""
            QLabel {
                color: #00f0e6;
                font-size: 18px;
                font-weight: 900;
                line-height: 24px;
            }
        """)

        subtitle = QLabel("aquí puedes administrar usuarios y revisar accesos")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            QLabel {
                color: #d3e2ea;
                font-size: 12px;
                font-weight: 700;
            }
        """)

        banner_layout.addWidget(title)
        banner_layout.addWidget(subtitle)
        banner_layout.addStretch()

        # =====================================================
        # CARDS DE ESTADÍSTICAS
        # =====================================================
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.detected_card = self.stat_card(
            icon_file="face_id.png",
            title="ROSTROS DETECTADOS",
            value="0"
        )

        self.users_card = self.stat_card(
            icon_file="user_add.png",
            title="NUEVOS REGISTROS",
            value="0"
        )

        self.detected_value = self.detected_card.findChild(QLabel, "value_label")
        self.users_value = self.users_card.findChild(QLabel, "value_label")

        stats_row.addWidget(self.detected_card)
        stats_row.addWidget(self.users_card)

        # =====================================================
        # ACCESOS RECIENTES
        # =====================================================
        recent_card = QFrame()
        recent_card.setObjectName("RecentCard")
        recent_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        recent_card.setStyleSheet("""
            QFrame#RecentCard {
                background: #111827;
                border: 1px solid #223044;
                border-radius: 16px;
            }
        """)

        recent_shadow = QGraphicsDropShadowEffect()
        recent_shadow.setBlurRadius(24)
        recent_shadow.setOffset(0, 12)
        recent_shadow.setColor(QColor(0, 0, 0, 100))
        recent_card.setGraphicsEffect(recent_shadow)

        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(14, 12, 14, 14)
        recent_layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        left_hdr = QLabel("Accesos Recientes")
        left_hdr.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 900;
            }
        """)

        see_all = QLabel("▣ Ver registros completos")
        see_all.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        see_all.setStyleSheet("""
            QLabel {
                color: #00f0e6;
                font-size: 10px;
                font-weight: 900;
            }
        """)

        header_row.addWidget(left_hdr)
        header_row.addStretch()
        header_row.addWidget(see_all)

        recent_layout.addLayout(header_row)

        # =====================================================
        # TABLA PREMIUM
        # =====================================================
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["USUARIO", "STATUS", "FECHA"])

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)

        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.table.setColumnWidth(1, 105)
        self.table.setColumnWidth(2, 110)

        self.table.setMinimumHeight(315)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.table.setStyleSheet("""
            QTableWidget {
                background: #0f1724;
                border: 1px solid #223044;
                border-radius: 14px;
                color: #dbeafe;
                font-size: 11px;
                font-weight: 800;
                outline: none;
            }

            QHeaderView::section {
                background: #1d2732;
                color: #9fc7ff;
                border: none;
                border-bottom: 1px solid #2b3a4d;
                font-size: 10px;
                font-weight: 900;
                padding: 12px 8px;
            }

            QTableWidget::item {
                background: #111b28;
                border-bottom: 1px solid #1f2b3d;
                padding-left: 8px;
                padding-right: 8px;
            }

            QTableWidget::item:selected {
                background: #111b28;
                color: #dbeafe;
            }
        """)

        recent_layout.addWidget(self.table)

        root.addWidget(banner)
        root.addLayout(stats_row)
        root.addWidget(recent_card)

    # =========================================================
    # CARD ESTADÍSTICA
    # =========================================================
    def stat_card(self, icon_file, title, value):
        card = QFrame()
        card.setObjectName("StatCard")
        card.setFixedHeight(106)
        card.setStyleSheet("""
            QFrame#StatCard {
                background: #111827;
                border: 1px solid #223044;
                border-radius: 12px;
            }

            QFrame#StatCard:hover {
                background: #121d2a;
                border: 1px solid rgba(0, 240, 230, 0.45);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 90))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(13, 10, 13, 10)
        lay.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        icon_box = QLabel()
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(31, 31)
        icon_box.setStyleSheet("""
            QLabel {
                background: rgba(0, 240, 230, 0.08);
                border: 1px solid rgba(0, 240, 230, 0.35);
                border-radius: 15px;
            }
        """)

        icon_full_path = asset_path(icon_file)

        if os.path.exists(icon_full_path):
            pix = QPixmap(icon_full_path).scaled(
                17,
                17,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            cyan_icon = QPixmap(pix.size())
            cyan_icon.fill(Qt.transparent)

            painter = QPainter(cyan_icon)
            painter.drawPixmap(0, 0, pix)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(cyan_icon.rect(), QColor("#00f0e6"))
            painter.end()

            icon_box.setPixmap(cyan_icon)

        dot = QLabel()
        dot.setFixedSize(13, 13)
        dot.setStyleSheet("""
            QLabel {
                background: rgba(0, 240, 230, 0.16);
                border-radius: 6px;
            }
        """)

        top_row.addWidget(icon_box, alignment=Qt.AlignLeft)
        top_row.addStretch()
        top_row.addWidget(dot, alignment=Qt.AlignRight)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            QLabel {
                color: #7e8b9c;
                font-size: 8px;
                font-weight: 900;
                letter-spacing: 0.8px;
            }
        """)

        value_lbl = QLabel(value)
        value_lbl.setObjectName("value_label")
        value_lbl.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 23px;
                font-weight: 900;
            }
        """)

        lay.addLayout(top_row)
        lay.addSpacing(2)
        lay.addWidget(title_lbl)
        lay.addWidget(value_lbl)

        return card

    # =========================================================
    # REFRESCAR DATOS
    # =========================================================
    def refresh_data(self):
        self.users_value.setText(str(contar_usuarios_registrados()))
        self.detected_value.setText(str(contar_accesos_hoy()))

        logs = obtener_historial_accesos(limite=8)
        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            nombre = str(log.get("nombre", "")).strip()
            estado = str(log.get("status", "")).strip()
            fecha = str(log.get("fecha", "")).strip()

            if not nombre:
                nombre = "Desconocido"

            estado_texto = self.format_status(estado)
            fecha_texto = self.format_fecha(fecha)

            user_item = QTableWidgetItem(nombre)
            status_item = QTableWidgetItem(estado_texto)
            fecha_item = QTableWidgetItem(fecha_texto)

            user_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            status_item.setTextAlignment(Qt.AlignCenter)
            fecha_item.setTextAlignment(Qt.AlignCenter)

            user_item.setForeground(QColor("#dbeafe"))
            fecha_item.setForeground(QColor("#94a3b8"))

            if estado_texto == "AUTHORIZED":
                status_item.setForeground(QColor("#00f0e6"))
            elif estado_texto == "DENIED":
                status_item.setForeground(QColor("#ff7b8a"))
            else:
                status_item.setForeground(QColor("#fbbf24"))

            font_bold = QFont()
            font_bold.setBold(True)
            font_bold.setPointSize(9)

            user_item.setFont(font_bold)
            status_item.setFont(font_bold)
            fecha_item.setFont(font_bold)

            self.table.setItem(row, 0, user_item)
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, fecha_item)
            self.table.setRowHeight(row, 42)

        if len(logs) == 0:
            self.show_empty_state()

    # =========================================================
    # ESTADO VACÍO
    # =========================================================
    def show_empty_state(self):
        self.table.setRowCount(1)

        empty_user = QTableWidgetItem("Sin registros todavía")
        empty_status = QTableWidgetItem("—")
        empty_fecha = QTableWidgetItem("—")

        empty_user.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        empty_status.setTextAlignment(Qt.AlignCenter)
        empty_fecha.setTextAlignment(Qt.AlignCenter)

        empty_user.setForeground(QColor("#64748b"))
        empty_status.setForeground(QColor("#64748b"))
        empty_fecha.setForeground(QColor("#64748b"))

        self.table.setItem(0, 0, empty_user)
        self.table.setItem(0, 1, empty_status)
        self.table.setItem(0, 2, empty_fecha)
        self.table.setRowHeight(0, 48)

    # =========================================================
    # HELPERS
    # =========================================================
    def format_status(self, estado):
        estado = estado.lower().strip()

        if estado in ["autorizado", "authorized", "permitido", "ok", "success"]:
            return "AUTHORIZED"

        if estado in ["denegado", "denied", "rechazado", "error", "fail"]:
            return "DENIED"

        if not estado:
            return "UNKNOWN"

        return estado.upper()

    def format_fecha(self, fecha):
        if not fecha:
            return "--"

        if " " in fecha:
            parts = fecha.split(" ")
            date_part = parts[0]
            time_part = parts[1][:5] if len(parts) > 1 else ""

            return f"{date_part}\n{time_part}"

        return fecha