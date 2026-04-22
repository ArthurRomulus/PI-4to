import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QFrame, QScrollArea, QSizePolicy,
    QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
)
from .admin_components import RoundedCard

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import (
    obtener_lista_usuarios, obtener_lista_admins,
    eliminar_usuario_por_id, eliminar_admin,
    dar_de_baja_usuario, reactivar_usuario, editar_usuario,
)

# ── Estilos compartidos ──────────────────────────────────────────────────────
_BTN_BASE = """
    QPushButton {{
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 6px;
        color: {fg};
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        min-width: 72px;
    }}
    QPushButton:hover {{ background-color: {hover}; color: #ffffff; }}
    QPushButton:disabled {{ background-color: #1e293b; border-color: #334155; color: #475569; }}
"""

BTN_DELETE = _BTN_BASE.format(bg="#7f1d1d", border="#ef4444", fg="#fca5a5", hover="#991b1b")
BTN_EDIT   = _BTN_BASE.format(bg="#1e3a5f", border="#3b82f6", fg="#93c5fd", hover="#1d4ed8")
BTN_BAJA   = _BTN_BASE.format(bg="#78350f", border="#f59e0b", fg="#fcd34d", hover="#b45309")
BTN_REACT  = _BTN_BASE.format(bg="#14532d", border="#22c55e", fg="#86efac", hover="#15803d")

MSG_STYLE = """
    QMessageBox { background-color: #0f172a; color: #e2e8f0; }
    QLabel { color: #e2e8f0; font-size: 13px; }
    QPushButton {
        background-color: #1e293b; color: #e2e8f0;
        border: 1px solid #334155; border-radius: 6px;
        padding: 6px 18px; font-weight: bold;
    }
    QPushButton:hover { background-color: #334155; }
"""

TABLE_STYLE = """
    QTableWidget {
        border: none; background: transparent;
        font-size: 12px; color: #e2e8f0; gridline-color: #1e293b;
    }
    QHeaderView::section {
        background: transparent; color: #93c5fd; border: none;
        font-size: 11px; font-weight: 700; padding: 4px 0;
    }
    QTableWidget::item { padding: 4px 6px; }
    QTableWidget::item:selected { background-color: rgba(59,130,246,0.2); color: #bfdbfe; }
"""


# ── Diálogo edición ──────────────────────────────────────────────────────────
class EditUserDialog(QDialog):
    """Diálogo para editar nombre y número de cuenta de un usuario."""

    def __init__(self, nombre_actual: str, account_actual: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar usuario")
        self.setFixedWidth(360)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #e2e8f0; }
            QLabel { color: #94a3b8; font-size: 12px; }
            QLineEdit {
                background-color: #1e293b; color: #e2e8f0;
                border: 1px solid #334155; border-radius: 6px;
                padding: 6px 10px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #3b82f6; }
            QPushButton {
                background-color: #1e3a5f; color: #93c5fd;
                border: 1px solid #3b82f6; border-radius: 6px;
                padding: 7px 18px; font-weight: 700;
            }
            QPushButton:hover { background-color: #1d4ed8; color: #ffffff; }
        """)

        form = QFormLayout(self)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        self.nombre_edit = QLineEdit(nombre_actual)
        self.account_edit = QLineEdit(account_actual)

        form.addRow("Nombre:", self.nombre_edit)
        form.addRow("N° de cuenta:", self.account_edit)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText("Guardar")
        btns.button(QDialogButtonBox.Cancel).setText("Cancelar")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    @property
    def nuevo_nombre(self):
        return self.nombre_edit.text().strip()

    @property
    def nuevo_account(self):
        return self.account_edit.text().strip() or None


# ── Helpers ──────────────────────────────────────────────────────────────────
def _make_btn(text: str, style: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(style)
    return btn


def _make_table(columns: list, stretch_col: int = 1) -> QTableWidget:
    t = QTableWidget(0, len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QTableWidget.SingleSelection)
    t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    t.setStyleSheet(TABLE_STYLE)
    return t


# ── Página principal ─────────────────────────────────────────────────────────
class UsersPage(QWidget):
    def __init__(self):
        super().__init__()

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

        # ── Tabla Usuarios registrados ────────────────────────────────────────
        user_card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        u_inner = QVBoxLayout(user_card)
        u_inner.setContentsMargins(14, 14, 14, 14)
        u_inner.setSpacing(8)

        u_title = QLabel("👤  Usuarios registrados")
        u_title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700; border: none;")

        # columnas: ID | NOMBRE | ROL | FECHA | ESTADO | ACCIONES
        self.user_table = _make_table(
            ["ID", "NOMBRE", "ROL", "FECHA REGISTRO", "ESTADO", "ACCIONES"],
            stretch_col=1,
        )
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.user_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        u_inner.addWidget(u_title)
        u_inner.addWidget(self.user_table)
        lay.addWidget(user_card)

        # ── Tabla Administradores ─────────────────────────────────────────────
        admin_card = RoundedCard(radius=20, color="#111827", border="#1e3a8a")
        a_inner = QVBoxLayout(admin_card)
        a_inner.setContentsMargins(14, 14, 14, 14)
        a_inner.setSpacing(8)

        a_title = QLabel("🔑  Administradores del sistema")
        a_title.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: 700; border: none;")

        a_desc = QLabel(
            "Las contraseñas nunca se muestran en texto plano.  "
            "admin@local no puede eliminarse."
        )
        a_desc.setWordWrap(True)
        a_desc.setStyleSheet("color: #64748b; font-size: 11px; border: none;")

        # columnas: ID | CORREO | CONTRASEÑA | ACCIONES
        self.admin_table = _make_table(["ID", "CORREO", "CONTRASEÑA", "ACCIONES"], stretch_col=1)
        self.admin_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.admin_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.admin_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        a_inner.addWidget(a_title)
        a_inner.addWidget(a_desc)
        a_inner.addWidget(self.admin_table)
        lay.addWidget(admin_card)

        lay.addStretch()

    # ── Notificación ─────────────────────────────────────────────────────────
    def _notif(self, texto: str, ok: bool):
        msg = QMessageBox(self)
        msg.setWindowTitle("Resultado")
        msg.setText(texto)
        msg.setIcon(QMessageBox.Information if ok else QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet(MSG_STYLE)
        msg.exec_()

    # ── Confirmación genérica ─────────────────────────────────────────────────
    def _confirmar(self, titulo: str, texto: str, info: str = "") -> bool:
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        if info:
            msg.setInformativeText(info)
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText("Confirmar")
        msg.button(QMessageBox.Cancel).setText("Cancelar")
        msg.setStyleSheet(MSG_STYLE)
        return msg.exec_() == QMessageBox.Yes

    # ── Acciones sobre usuarios ───────────────────────────────────────────────
    def _accion_eliminar_usuario(self, user_id: int, nombre: str):
        if not self._confirmar(
            "Eliminar usuario",
            f"¿Eliminar a <b>{nombre}</b> (ID: {user_id})?",
            "Se eliminarán sus datos faciales e historial. Esta acción no se puede deshacer."
        ):
            return
        ok = eliminar_usuario_por_id(user_id)
        self._notif(
            f"✅  Usuario «{nombre}» eliminado." if ok else f"❌  No se pudo eliminar «{nombre}».",
            ok
        )
        if ok:
            self._load_users()

    def _accion_editar_usuario(self, user_id: int, nombre_actual: str, account_actual: str):
        dlg = EditUserDialog(nombre_actual, account_actual or "", self)
        if dlg.exec_() != QDialog.Accepted:
            return
        nuevo_nombre = dlg.nuevo_nombre
        nuevo_account = dlg.nuevo_account
        if not nuevo_nombre:
            self._notif("❌  El nombre no puede estar vacío.", False)
            return
        ok = editar_usuario(user_id, nuevo_nombre, nuevo_account)
        self._notif(
            f"✅  Usuario «{nuevo_nombre}» actualizado." if ok else "❌  No se pudo actualizar.",
            ok
        )
        if ok:
            self._load_users()

    def _accion_baja_usuario(self, user_id: int, nombre: str, activo: bool):
        if activo:
            if not self._confirmar(
                "Dar de baja",
                f"¿Dar de baja a <b>{nombre}</b>?",
                "El usuario quedará inactivo pero sus datos se conservarán."
            ):
                return
            ok = dar_de_baja_usuario(user_id)
            self._notif(
                f"🔴  Usuario «{nombre}» dado de baja." if ok else "❌  No se pudo dar de baja.",
                ok
            )
        else:
            if not self._confirmar(
                "Reactivar usuario",
                f"¿Reactivar a <b>{nombre}</b>?",
            ):
                return
            ok = reactivar_usuario(user_id)
            self._notif(
                f"✅  Usuario «{nombre}» reactivado." if ok else "❌  No se pudo reactivar.",
                ok
            )
        if ok:
            self._load_users()

    # ── Acciones sobre admins ─────────────────────────────────────────────────
    def _accion_eliminar_admin(self, id_admin: int, email: str):
        if not self._confirmar(
            "Eliminar administrador",
            f"¿Eliminar al administrador <b>{email}</b>?",
            "Esta acción no se puede deshacer."
        ):
            return
        ok, msg = eliminar_admin(id_admin)
        self._notif(
            f"✅  Admin «{email}» eliminado." if ok else f"❌  {msg}",
            ok
        )
        if ok:
            self._load_admins()

    # ── Carga de datos ────────────────────────────────────────────────────────
    def refresh_data(self):
        self._load_users()
        self._load_admins()

    def _load_users(self):
        users = obtener_lista_usuarios()
        self.user_table.setRowCount(0)

        for row_idx, user in enumerate(users):
            self.user_table.insertRow(row_idx)
            uid        = user.get("id", "")
            nombre     = user.get("nombre", "")
            rol        = user.get("tipo_usuario", "")
            fecha      = str(user.get("fecha_registro", ""))
            activo     = user.get("activo", True)
            account    = user.get("account_number", "")

            # Color de fila: gris si está de baja
            row_color = "#e2e8f0" if activo else "#475569"

            for col, txt in enumerate([str(uid), nombre, rol, fecha]):
                item = QTableWidgetItem(txt)
                item.setForeground(
                    __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor(row_color)
                )
                self.user_table.setItem(row_idx, col, item)

            # Estado
            estado_item = QTableWidgetItem("✅ Activo" if activo else "🔴 Baja")
            estado_item.setTextAlignment(Qt.AlignCenter)
            estado_item.setForeground(
                __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor(
                    "#22c55e" if activo else "#f87171"
                )
            )
            self.user_table.setItem(row_idx, 4, estado_item)

            # Celda de acciones
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            btn_del  = _make_btn("🗑 Eliminar", BTN_DELETE)
            btn_edit = _make_btn("✏️ Editar", BTN_EDIT)
            btn_baja = _make_btn(
                "✅ Reactivar" if not activo else "🔴 Dar de baja",
                BTN_REACT if not activo else BTN_BAJA,
            )

            # Captura de variables en closures
            def _on_del(_, _uid=uid, _nombre=nombre):
                self._accion_eliminar_usuario(_uid, _nombre)

            def _on_edit(_, _uid=uid, _nombre=nombre, _account=account):
                self._accion_editar_usuario(_uid, _nombre, _account)

            def _on_baja(_, _uid=uid, _nombre=nombre, _activo=activo):
                self._accion_baja_usuario(_uid, _nombre, _activo)

            btn_del.clicked.connect(_on_del)
            btn_edit.clicked.connect(_on_edit)
            btn_baja.clicked.connect(_on_baja)

            actions_layout.addWidget(btn_del)
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_baja)
            actions_layout.addStretch()

            self.user_table.setCellWidget(row_idx, 5, actions_widget)

        self.user_table.resizeRowsToContents()

    def _load_admins(self):
        admins = obtener_lista_admins()
        self.admin_table.setRowCount(0)

        for row_idx, admin in enumerate(admins):
            self.admin_table.insertRow(row_idx)
            id_admin = admin.get("id_admin", "")
            email    = admin.get("email", "")
            es_local = (email == "admin@local")

            self.admin_table.setItem(row_idx, 0, QTableWidgetItem(str(id_admin)))
            self.admin_table.setItem(row_idx, 1, QTableWidgetItem(email))
            self.admin_table.setItem(row_idx, 2, QTableWidgetItem("••••••••••••"))

            # Celda de acciones
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            if es_local:
                protected = QLabel("🔒 Protegido")
                protected.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
                actions_layout.addWidget(protected)
            else:
                btn_del = _make_btn("🗑 Eliminar", BTN_DELETE)

                def _on_admin_del(_, _id=id_admin, _email=email):
                    self._accion_eliminar_admin(_id, _email)

                btn_del.clicked.connect(_on_admin_del)
                actions_layout.addWidget(btn_del)

            actions_layout.addStretch()
            self.admin_table.setCellWidget(row_idx, 3, actions_widget)

        self.admin_table.resizeRowsToContents()
