import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QFrame, QScrollArea, QSizePolicy,
    QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView,
)
from .admin_components import RoundedCard

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import (
    obtener_lista_usuarios, obtener_conexion, eliminar_usuario_por_id
)


def _obtener_admins():
    """Retorna lista de dicts {id_admin, email} de la tabla ADMINS."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute("SELECT id_admin, email FROM ADMINS ORDER BY id_admin")
        rows = cursor.fetchall()
        conn.close()
        return [{"id_admin": r[0], "email": r[1]} for r in rows]
    except Exception as e:
        print(f"[UsersPage] Error cargando admins: {e}")
        return []


def _make_table(columns: list, stretch_col: int = 1) -> QTableWidget:
    t = QTableWidget(0, len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QTableWidget.SingleSelection)
    t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    t.setStyleSheet("""
        QTableWidget {
            border: none;
            background: transparent;
            font-size: 12px;
            color: #e2e8f0;
            gridline-color: #1e293b;
        }
        QHeaderView::section {
            background: transparent;
            color: #93c5fd;
            border: none;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 0;
        }
        QTableWidget::item { padding: 4px 6px; }
        QTableWidget::item:selected {
            background-color: rgba(239, 68, 68, 0.25);
            color: #fca5a5;
        }
    """)
    return t


class UsersPage(QWidget):
    def __init__(self):
        super().__init__()

        # Scroll externo para toda la página
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        lay = QVBoxLayout(container)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(16)

        # ── Tabla de usuarios registrados ────────────────────────────────────
        user_card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        u_inner = QVBoxLayout(user_card)
        u_inner.setContentsMargins(14, 14, 14, 14)
        u_inner.setSpacing(8)

        # Encabezado con título y botón eliminar
        u_header_row = QHBoxLayout()
        u_title = QLabel("👤  Usuarios registrados")
        u_title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700; border: none;")
        u_header_row.addWidget(u_title)
        u_header_row.addStretch()

        self.delete_user_btn = QPushButton("🗑  Eliminar usuario")
        self.delete_user_btn.setCursor(Qt.PointingHandCursor)
        self.delete_user_btn.setFixedHeight(34)
        self.delete_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f1d1d;
                border: 1px solid #ef4444;
                border-radius: 8px;
                color: #fca5a5;
                font-size: 12px;
                font-weight: 700;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #991b1b;
                color: #ffffff;
                border-color: #f87171;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                border-color: #334155;
                color: #475569;
            }
        """)
        self.delete_user_btn.setEnabled(False)
        self.delete_user_btn.clicked.connect(self._confirmar_eliminar_usuario)
        u_header_row.addWidget(self.delete_user_btn)

        self.user_table = _make_table(["ID", "NOMBRE", "ROL", "FECHA"], stretch_col=1)
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.user_table.itemSelectionChanged.connect(self._on_user_selection_changed)

        u_inner.addLayout(u_header_row)
        u_inner.addWidget(self.user_table)
        lay.addWidget(user_card)

        # ── Tabla de administradores ─────────────────────────────────────────
        admin_card = RoundedCard(radius=20, color="#111827", border="#1e3a8a")
        a_inner = QVBoxLayout(admin_card)
        a_inner.setContentsMargins(14, 14, 14, 14)
        a_inner.setSpacing(8)

        a_title = QLabel("🔑  Administradores del sistema")
        a_title.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: 700; border: none;")

        a_desc = QLabel("Las contraseñas nunca se almacenan en texto plano — se muestran enmascaradas.")
        a_desc.setWordWrap(True)
        a_desc.setStyleSheet("color: #64748b; font-size: 11px; border: none;")

        self.admin_table = _make_table(["ID", "CORREO", "CONTRASEÑA"], stretch_col=1)
        self.admin_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        a_inner.addWidget(a_title)
        a_inner.addWidget(a_desc)
        a_inner.addWidget(self.admin_table)
        lay.addWidget(admin_card)

        lay.addStretch()

    # ── Selección ────────────────────────────────────────────────────────────
    def _on_user_selection_changed(self):
        selected = self.user_table.selectedItems()
        self.delete_user_btn.setEnabled(bool(selected))

    # ── Eliminar usuario ─────────────────────────────────────────────────────
    def _confirmar_eliminar_usuario(self):
        row = self.user_table.currentRow()
        if row < 0:
            return

        id_item     = self.user_table.item(row, 0)
        nombre_item = self.user_table.item(row, 1)
        if not id_item or not nombre_item:
            return

        user_id  = int(id_item.text())
        nombre   = nombre_item.text()

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText(f"¿Eliminar al usuario <b>{nombre}</b> (ID: {user_id})?")
        msg.setInformativeText(
            "Se eliminarán también sus registros faciales e historial de accesos.\n"
            "Esta acción no se puede deshacer."
        )
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText("Eliminar")
        msg.button(QMessageBox.Cancel).setText("Cancelar")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QPushButton {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #334155; }
        """)

        reply = msg.exec_()
        if reply == QMessageBox.Yes:
            self._eliminar_usuario(user_id, nombre)

    def _eliminar_usuario(self, user_id: int, nombre: str):
        exito = eliminar_usuario_por_id(user_id)
        if exito:
            self._mostrar_notificacion(f"✅  Usuario «{nombre}» eliminado correctamente.", ok=True)
            self.refresh_data()
        else:
            self._mostrar_notificacion(f"❌  No se pudo eliminar a «{nombre}».", ok=False)

    def _mostrar_notificacion(self, texto: str, ok: bool):
        msg = QMessageBox(self)
        msg.setWindowTitle("Resultado")
        msg.setText(texto)
        msg.setIcon(QMessageBox.Information if ok else QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox { background-color: #0f172a; color: #e2e8f0; }
            QLabel { color: #e2e8f0; font-size: 13px; }
            QPushButton {
                background-color: #1e293b; color: #e2e8f0;
                border: 1px solid #334155; border-radius: 6px;
                padding: 6px 18px; font-weight: bold;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        msg.exec_()

    # ── Actualización de datos ────────────────────────────────────────────────
    def refresh_data(self):
        self._load_users()
        self._load_admins()

    def _load_users(self):
        users = obtener_lista_usuarios()
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user.get("id", ""))))
            self.user_table.setItem(row, 1, QTableWidgetItem(str(user.get("nombre", ""))))
            self.user_table.setItem(row, 2, QTableWidgetItem(str(user.get("tipo_usuario", ""))))
            self.user_table.setItem(row, 3, QTableWidgetItem(str(user.get("fecha_registro", ""))))
        self.user_table.resizeRowsToContents()
        self.delete_user_btn.setEnabled(False)

    def _load_admins(self):
        admins = _obtener_admins()
        self.admin_table.setRowCount(len(admins))
        for row, admin in enumerate(admins):
            self.admin_table.setItem(row, 0, QTableWidgetItem(str(admin.get("id_admin", ""))))
            self.admin_table.setItem(row, 1, QTableWidgetItem(str(admin.get("email", ""))))
            # Contraseña siempre enmascarada — nunca mostramos el hash
            self.admin_table.setItem(row, 2, QTableWidgetItem("••••••••••••"))
        self.admin_table.resizeRowsToContents()
