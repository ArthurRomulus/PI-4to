import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QFrame, QScrollArea, QSizePolicy,
)
from .admin_components import RoundedCard

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import obtener_lista_usuarios, obtener_conexion


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
    t.setSelectionMode(QTableWidget.NoSelection)
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

        u_title = QLabel("👤  Usuarios registrados")
        u_title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700; border: none;")

        self.user_table = _make_table(["ID", "NOMBRE", "ROL", "FECHA"], stretch_col=1)
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        u_inner.addWidget(u_title)
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

    def _load_admins(self):
        admins = _obtener_admins()
        self.admin_table.setRowCount(len(admins))
        for row, admin in enumerate(admins):
            self.admin_table.setItem(row, 0, QTableWidgetItem(str(admin.get("id_admin", ""))))
            self.admin_table.setItem(row, 1, QTableWidgetItem(str(admin.get("email", ""))))
            # Contraseña siempre enmascarada — nunca mostramos el hash
            self.admin_table.setItem(row, 2, QTableWidgetItem("••••••••••••"))
        self.admin_table.resizeRowsToContents()
