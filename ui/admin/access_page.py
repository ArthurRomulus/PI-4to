from PyQt5.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from .admin_components import RoundedCard
from database.consultas import obtener_historial_accesos
from ui.i18n import t


class AccessPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 14, 14, 14)

        title = QLabel(t("admin.access.title", default="Registro de acceso"))
        title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700;")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            t("admin.access.table_header_user", default="USUARIO"),
            t("admin.access.table_header_account", default="CUENTA"),
            t("admin.access.table_header_status", default="ESTADO"),
            t("admin.access.table_header_date", default="FECHA"),
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # USUARIO
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)   # CUENTA
        self.table.setColumnWidth(1, 120)  # Ancho fijo para la columna de cuenta
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)   # ESTADO
        self.table.setColumnWidth(2, 120)  # Ancho fijo para la columna de estado
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)   # FECHA
        self.table.setColumnWidth(3, 160)  # Ancho fijo para la columna de fecha
        self.table.setStyleSheet(
            """
            QTableWidget { border: none; background: transparent; font-size: 12px; color: #e2e8f0; }
            QHeaderView::section { background: transparent; color: #93c5fd; border: none; font-size: 11px; font-weight: 700; }
            """
        )

        inner.addWidget(title)
        inner.addWidget(self.table)
        lay.addWidget(card)
        
        # Timer para actualizar el registro de accesos automáticamente
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(2000)  # Actualizar cada 2 segundos
        
        # Cargar datos iniciales
        self.refresh_data()

    def refresh_data(self):
        logs = obtener_historial_accesos(limite=100)
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            # Traducir estados a español
            estado = log.get("status", "")
            if estado == "AUTHORIZED":
                estado_mostrar = "✅ AUTORIZADO"
            elif estado == "DENIED":
                estado_mostrar = "❌ DENEGADO"
            else:
                estado_mostrar = estado
            
            self.table.setItem(row, 0, QTableWidgetItem(str(log.get("nombre", "DESCONOCIDO") or "DESCONOCIDO")))
            self.table.setItem(row, 1, QTableWidgetItem(str(log.get("account_number", "N/A"))))
            self.table.setItem(row, 2, QTableWidgetItem(estado_mostrar))
            self.table.setItem(row, 3, QTableWidgetItem(str(log.get("fecha", ""))))
    
    def showEvent(self, event):
        """Se ejecuta cuando la página se muestra."""
        super().showEvent(event)
        if self.refresh_timer:
            self.refresh_timer.start(2000)
        self.refresh_data()
    
    def hideEvent(self, event):
        """Se ejecuta cuando la página se oculta."""
        super().hideEvent(event)
        if self.refresh_timer:
            self.refresh_timer.stop()
    
    def closeEvent(self, event):
        """Se ejecuta cuando se cierra la página."""
        if self.refresh_timer:
            self.refresh_timer.stop()
        super().closeEvent(event)