import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QFrame, QScrollArea, QSizePolicy,
    QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
)
from .admin_components import RoundedCard

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import (
    obtener_lista_usuarios, obtener_conexion, eliminar_usuario_por_id,
    dar_de_baja_usuario, reactivar_usuario, modificar_usuario,
    obtener_lista_admins, dar_de_baja_admin, reactivar_admin,
    modificar_admin, eliminar_admin_por_id,
)
from ui.i18n import t

# ── Estilos compartidos ───────────────────────────────────────────────────────

_DIALOG_STYLE = """
    QDialog {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    QLabel {
        color: #94a3b8;
        font-size: 12px;
    }
    QLineEdit {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #e2e8f0;
        font-size: 13px;
        padding: 6px 10px;
    }
    QLineEdit:focus { border-color: #38bdf8; }
    QDialogButtonBox QPushButton {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 6px 20px;
        font-weight: bold;
    }
    QDialogButtonBox QPushButton:hover { background-color: #334155; }
"""

_MSG_STYLE = """
    QMessageBox { background-color: #0f172a; color: #e2e8f0; }
    QLabel { color: #e2e8f0; font-size: 13px; }
    QPushButton {
        background-color: #1e293b; color: #e2e8f0;
        border: 1px solid #334155; border-radius: 6px;
        padding: 6px 18px; font-weight: bold;
    }
    QPushButton:hover { background-color: #334155; }
"""

_BTN_DELETE = """
    QPushButton {
        background-color: #7f1d1d; border: 1px solid #ef4444;
        border-radius: 8px; color: #fca5a5;
        font-size: 11px; font-weight: 700; padding: 0 12px;
    }
    QPushButton:hover { background-color: #991b1b; color: #fff; border-color: #f87171; }
    QPushButton:disabled { background-color: #1e293b; border-color: #334155; color: #475569; }
"""

_BTN_BAJA = """
    QPushButton {
        background-color: #78350f; border: 1px solid #f59e0b;
        border-radius: 8px; color: #fde68a;
        font-size: 11px; font-weight: 700; padding: 0 12px;
    }
    QPushButton:hover { background-color: #92400e; color: #fff; border-color: #fbbf24; }
    QPushButton:disabled { background-color: #1e293b; border-color: #334155; color: #475569; }
"""

_BTN_MODIFY = """
    QPushButton {
        background-color: #1e3a5f; border: 1px solid #38bdf8;
        border-radius: 8px; color: #7dd3fc;
        font-size: 11px; font-weight: 700; padding: 0 12px;
    }
    QPushButton:hover { background-color: #1e4d7a; color: #fff; border-color: #7dd3fc; }
    QPushButton:disabled { background-color: #1e293b; border-color: #334155; color: #475569; }
"""


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


def _make_btn(label: str, style: str, height: int = 32) -> QPushButton:
    btn = QPushButton(label)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(height)
    btn.setStyleSheet(style)
    btn.setEnabled(False)
    return btn


# ── Diálogos de modificación ──────────────────────────────────────────────────

class ModificarUsuarioDialog(QDialog):
    """Ventana para editar nombre y número de cuenta de un usuario."""

    def __init__(self, nombre_actual: str, cuenta_actual: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("users_page.dialog_modify_user_title", default="Modificar usuario"))
        self.setMinimumWidth(380)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel(t("users_page.dialog_modify_user_heading", default="✏️  Editar datos del usuario"))
        titulo.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 700;")
        layout.addWidget(titulo)

        form = QFormLayout()
        form.setSpacing(10)

        self.nombre_edit = QLineEdit(nombre_actual or "")
        self.cuenta_edit = QLineEdit(cuenta_actual or "")

        form.addRow(t("users_page.dialog_label_name", default="Nombre:"), self.nombre_edit)
        form.addRow(t("users_page.dialog_label_account_number", default="Número de cuenta:"), self.cuenta_edit)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(t("users_page.dialog_button_save", default="Guardar"))
        btns.button(QDialogButtonBox.Cancel).setText(t("users_page.dialog_button_cancel", default="Cancelar"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_datos(self):
        return self.nombre_edit.text().strip(), self.cuenta_edit.text().strip()


class ModificarAdminDialog(QDialog):
    """Ventana para editar el numero de cuenta de un administrador."""

    def __init__(self, email_actual: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("users_page.dialog_modify_admin_title", default="Modificar administrador"))
        self.setMinimumWidth(380)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel(t("users_page.dialog_modify_admin_heading", default="✏️  Editar nombre del administrador"))
        titulo.setStyleSheet("color: #f59e0b; font-size: 15px; font-weight: 700;")
        layout.addWidget(titulo)

        form = QFormLayout()
        form.setSpacing(10)
        self.nombre_edit = QLineEdit(email_actual or "")
        form.addRow(t("users_page.dialog_label_name", default="Nombre:"), self.nombre_edit)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(t("users_page.dialog_button_save", default="Guardar"))
        btns.button(QDialogButtonBox.Cancel).setText(t("users_page.dialog_button_cancel", default="Cancelar"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_nombre(self):
        return self.nombre_edit.text().strip()


# ── Página principal ──────────────────────────────────────────────────────────

class UsersPage(QWidget):
    def __init__(self):
        super().__init__()

        # Datos completos para filtrado
        self._all_users = []
        self._all_admins = []

        # ── Layout externo con scroll ────────────────────────────────────────
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

        u_title = QLabel(t("users_page.users_title", default="👤  Usuarios registrados"))
        u_title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700; border: none;")
        u_inner.addWidget(u_title)



        # ── Campo de búsqueda de usuarios ────────────────────────────────────────
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText(t("users_page.search_placeholder", default="🔍  Buscar por nombre, ID o cuenta..."))
        self.user_search.setClearButtonEnabled(True)
        self.user_search.setFixedHeight(32)
        self.user_search.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 12px;
                padding: 0 10px;
            }
            QLineEdit:focus { border-color: #38bdf8; }
        """)
        self.user_search.textChanged.connect(self._filter_users)
        u_inner.addWidget(self.user_search)

        # Tabla usuarios: ID, Nombre, Cuenta, Rol, Estado, Fecha, Acciones
        self.user_table = _make_table([
            t("users_page.table_header_id", default="ID"),
            t("users_page.table_header_name", default="NOMBRE"),
            t("users_page.table_header_account", default="CUENTA"),
            t("users_page.table_header_role", default="ROL"),
            t("users_page.table_header_status", default="ESTADO"),
            t("users_page.table_header_date", default="FECHA"),
            t("users_page.table_header_actions", default="ACCIONES"),
        ], stretch_col=1)
        self.user_table.setColumnHidden(0, True)
        self.user_table.setColumnWidth(2, 70)
        self.user_table.setColumnWidth(3, 50)
        self.user_table.setColumnWidth(4, 55)
        self.user_table.setColumnWidth(5, 90)
        self.user_table.setColumnWidth(6, 90)
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.user_table.setMaximumHeight(320)
        self.user_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.user_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.user_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.user_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        u_inner.addWidget(self.user_table)
        lay.addWidget(user_card)

        # ── Tabla de administradores ─────────────────────────────────────────
        admin_card = RoundedCard(radius=20, color="#111827", border="#1e3a8a")
        a_inner = QVBoxLayout(admin_card)
        a_inner.setContentsMargins(14, 14, 14, 14)
        a_inner.setSpacing(8)

        a_title = QLabel(t("users_page.admins_title", default="🔑  Administradores del sistema"))
        a_title.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: 700; border: none;")

        a_desc = QLabel(t("users_page.admins_description", default="Las contraseñas nunca se almacenan en texto plano — se muestran enmascaradas."))
        a_desc.setWordWrap(True)
        a_desc.setStyleSheet("color: #64748b; font-size: 11px; border: none;")

        a_inner.addWidget(a_title)
        a_inner.addWidget(a_desc)



        # ── Campo de búsqueda de admins ─────────────────────────────────────────
        self.admin_search = QLineEdit()
        self.admin_search.setPlaceholderText(t("users_page.search_placeholder", default="🔍  Buscar por nombre, ID o cuenta..."))
        self.admin_search.setClearButtonEnabled(True)
        self.admin_search.setFixedHeight(32)
        self.admin_search.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 12px;
                padding: 0 10px;
            }
            QLineEdit:focus { border-color: #f59e0b; }
        """)
        self.admin_search.textChanged.connect(self._filter_admins)
        a_inner.addWidget(self.admin_search)

        # Tabla admins: ID, Nombre, Cuenta, Contraseña, Estado, Fecha, Acciones
        self.admin_table = _make_table([
            t("users_page.table_header_id", default="ID"),
            t("users_page.table_header_name", default="NOMBRE"),
            t("users_page.table_header_account", default="CUENTA"),
            t("users_page.table_header_password", default="CONTRASEÑA"),
            t("users_page.table_header_status", default="ESTADO"),
            t("users_page.table_header_date", default="FECHA"),
            t("users_page.table_header_actions", default="ACCIONES"),
        ], stretch_col=1)
        self.admin_table.setColumnHidden(0, True)
        self.admin_table.setColumnWidth(2, 70)
        self.admin_table.setColumnWidth(3, 60)
        self.admin_table.setColumnWidth(4, 55)
        self.admin_table.setColumnWidth(5, 90)
        self.admin_table.setColumnWidth(6, 90)
        self.admin_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.admin_table.setMaximumHeight(280)
        self.admin_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.admin_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.admin_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.admin_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        a_inner.addWidget(self.admin_table)
        lay.addWidget(admin_card)

        lay.addStretch()

    # ── Helpers de estado ─────────────────────────────────────────────────────

    def _get_selected_user(self):
        """Devuelve (row, id_user, nombre, is_active) del usuario seleccionado o None."""
        row = self.user_table.currentRow()
        if row < 0:
            return None
        id_item     = self.user_table.item(row, 0)
        nombre_item = self.user_table.item(row, 1)
        estado_item = self.user_table.item(row, 4)
        if not id_item:
            return None
        active_text = estado_item.text() if estado_item else t("users_page.status_active", default="Activo")
        return (
            row,
            int(id_item.text()),
            nombre_item.text() if nombre_item else "",
            active_text == t("users_page.status_active", default="Activo"),
        )

    def _get_selected_admin(self):
        """Devuelve (row, id_admin, nombre, is_active) del admin seleccionado o None."""
        row = self.admin_table.currentRow()
        if row < 0:
            return None
        id_item     = self.admin_table.item(row, 0)
        nombre_item = self.admin_table.item(row, 1)
        estado_item = self.admin_table.item(row, 4)
        if not id_item:
            return None
        active_text = estado_item.text() if estado_item else t("users_page.status_active", default="Activo")
        return (
            row,
            int(id_item.text()),
            nombre_item.text() if nombre_item else "",
            active_text == t("users_page.status_active", default="Activo"),
        )

    # ── Selección (sin uso con botones por fila) ──────────────────────────────

    def _on_user_selection_changed(self):
        pass

    def _on_admin_selection_changed(self):
        pass

    # ── Acciones directas USUARIOS ────────────────────────────────────────────

    def _confirmar_eliminar_usuario(self):
        data = self._get_selected_user()
        if not data: return
        _, user_id, nombre, _ = data
        self._eliminar_usuario_directo(user_id, nombre)

    def _eliminar_usuario_directo(self, user_id, nombre):
        msg = QMessageBox(self)
        msg.setWindowTitle(t("users_page.confirm_delete_user_title", default="Confirmar eliminación"))
        msg.setText(t("users_page.confirm_delete_user_text", default="¿Eliminar al usuario <b>{name}</b> (ID: {id})?").format(name=nombre, id=user_id))
        msg.setInformativeText(t("users_page.confirm_delete_user_info", default="Se eliminarán también sus registros faciales e historial de accesos.\nEsta acción no se puede deshacer."))
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText(t("users_page.dialog_button_delete", default="Eliminar"))
        msg.button(QMessageBox.Cancel).setText(t("users_page.dialog_button_cancel", default="Cancelar"))
        msg.setStyleSheet(_MSG_STYLE)
        if msg.exec_() == QMessageBox.Yes:
            if eliminar_usuario_por_id(user_id):
                self._notificar(
                    t("users_page.user_deleted_ok", default="✅  Usuario «{name}» eliminado correctamente.").format(name=nombre),
                    ok=True
                )
                self.refresh_data()
            else:
                self._notificar(
                    t("users_page.user_deleted_error", default="❌  No se pudo eliminar a «{name}»." ).format(name=nombre),
                    ok=False
                )

    def _toggle_baja_usuario(self):
        data = self._get_selected_user()
        if not data: return
        _, user_id, nombre, is_active = data
        self._toggle_baja_usuario_directo(user_id, nombre, is_active)

    def _toggle_baja_usuario_directo(self, user_id, nombre, is_active):
        accion = t("users_page.user_action_reactivate", default="reactivar") if not is_active else t("users_page.user_action_deactivate", default="dar de baja")
        msg = QMessageBox(self)
        msg.setWindowTitle(t("users_page.confirm_action_title", default="Confirmar acción"))
        msg.setText(t("users_page.confirm_toggle_user_text", default="¿Deseas <b>{action}</b> al usuario <b>{name}</b>?").format(action=accion, name=nombre))
        msg.setInformativeText(
            t("users_page.confirm_toggle_user_info_reactivate", default="El usuario podrá volver a iniciar sesión.") if not is_active else
            t("users_page.confirm_toggle_user_info_deactivate", default="El usuario no podrá iniciar sesión hasta que sea reactivado.")
        )
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText(t("users_page.dialog_button_confirm", default="Confirmar"))
        msg.button(QDialogButtonBox.Cancel).setText(t("users_page.dialog_button_cancel", default="Cancelar"))
        msg.setStyleSheet(_MSG_STYLE)
        if msg.exec_() == QMessageBox.Yes:
            ok = reactivar_usuario(user_id) if not is_active else dar_de_baja_usuario(user_id)
            if ok:
                self._notificar(
                    t(
                        "users_page.user_toggle_status_ok",
                        default="✅  Usuario «{name}» {action} correctamente."
                    ).format(
                        name=nombre,
                        action=t("users_page.user_action_reactivated", default="reactivado") if not is_active else t("users_page.user_action_deactivated", default="dado de baja")
                    ),
                    ok=True
                )
                self.refresh_data()
            else:
                self._notificar(
                    t("users_page.user_toggle_status_error", default="❌  No se pudo {action} a «{name}».").format(
                        action=accion,
                        name=nombre
                    ),
                    ok=False
                )

    def _modificar_usuario(self):
        data = self._get_selected_user()
        if not data: return
        _, user_id, nombre, _ = data
        self._modificar_usuario_directo(user_id, nombre)

    def _modificar_usuario_directo(self, user_id, nombre):
        from database.consultas import obtener_usuario_por_id
        info = obtener_usuario_por_id(user_id)
        cuenta_actual = info.get("account_number", "") if info else ""
        dlg = ModificarUsuarioDialog(nombre, cuenta_actual or "", self)
        if dlg.exec_() == QDialog.Accepted:
            nuevo_nombre, nueva_cuenta = dlg.get_datos()
            if not nuevo_nombre:
                self._notificar(t("users_page.user_update_empty_name_error", default="❌  El nombre no puede estar vacío."), ok=False)
                return
            ok = modificar_usuario(user_id, nuevo_nombre, nueva_cuenta or None)
            if ok:
                self._notificar(t("users_page.user_update_ok", default="✅  Usuario actualizado correctamente."), ok=True)
                self.refresh_data()
            else:
                self._notificar(t("users_page.user_update_error", default="❌  No se pudo actualizar el usuario."), ok=False)

    # ── Acciones directas ADMINS ──────────────────────────────────────────────

    def _confirmar_eliminar_admin(self):
        data = self._get_selected_admin()
        if not data: return
        _, admin_id, nombre, _ = data
        self._eliminar_admin_directo(admin_id, nombre)

    def _eliminar_admin_directo(self, admin_id, nombre):
        msg = QMessageBox(self)
        msg.setWindowTitle(t("users_page.confirm_delete_admin_title", default="Confirmar eliminación"))
        msg.setText(t("users_page.confirm_delete_admin_text", default="¿Eliminar al administrador <b>{name}</b> (ID: {id})?").format(name=nombre, id=admin_id))
        msg.setInformativeText(t("users_page.confirm_delete_admin_info", default="Esta acción no se puede deshacer."))
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText(t("users_page.dialog_button_delete", default="Eliminar"))
        msg.button(QMessageBox.Cancel).setText(t("users_page.dialog_button_cancel", default="Cancelar"))
        msg.setStyleSheet(_MSG_STYLE)
        if msg.exec_() == QMessageBox.Yes:
            if eliminar_admin_por_id(admin_id):
                self._notificar(
                    t("users_page.admin_deleted_ok", default="✅  Administrador «{name}» eliminado correctamente.").format(name=nombre),
                    ok=True
                )
                self.refresh_data()
            else:
                self._notificar(
                    t("users_page.admin_deleted_error", default="❌  No se pudo eliminar al administrador «{name}»." ).format(name=nombre),
                    ok=False
                )

    def _toggle_baja_admin(self):
        data = self._get_selected_admin()
        if not data: return
        _, admin_id, nombre, is_active = data
        self._toggle_baja_admin_directo(admin_id, nombre, is_active)

    def _toggle_baja_admin_directo(self, admin_id, nombre, is_active):
        accion = t("users_page.admin_action_reactivate", default="reactivar") if not is_active else t("users_page.admin_action_deactivate", default="dar de baja")
        msg = QMessageBox(self)
        msg.setWindowTitle(t("users_page.confirm_action_title", default="Confirmar acción"))
        msg.setText(t("users_page.confirm_toggle_admin_text", default="¿Deseas <b>{action}</b> al administrador <b>{name}</b>?").format(action=accion, name=nombre))
        msg.setInformativeText(
            t("users_page.confirm_toggle_admin_info_reactivate", default="El administrador podrá volver a iniciar sesión.") if not is_active else
            t("users_page.confirm_toggle_admin_info_deactivate", default="El administrador no podrá iniciar sesión hasta que sea reactivado.")
        )
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.button(QMessageBox.Yes).setText(t("users_page.dialog_button_confirm", default="Confirmar"))
        msg.button(QDialogButtonBox.Cancel).setText(t("users_page.dialog_button_cancel", default="Cancelar"))
        msg.setStyleSheet(_MSG_STYLE)
        if msg.exec_() == QMessageBox.Yes:
            ok = reactivar_admin(admin_id) if not is_active else dar_de_baja_admin(admin_id)
            if ok:
                self._notificar(
                    t(
                        "users_page.admin_toggle_status_ok",
                        default="✅  Administrador «{name}» {action} correctamente."
                    ).format(
                        name=nombre,
                        action=t("users_page.admin_action_reactivated", default="reactivado") if not is_active else t("users_page.admin_action_deactivated", default="dado de baja")
                    ),
                    ok=True
                )
                self.refresh_data()
            else:
                self._notificar(
                    t("users_page.admin_toggle_status_error", default="❌  No se pudo {action} al administrador «{name}»." ).format(
                        action=accion,
                        name=nombre
                    ),
                    ok=False
                )

    def _modificar_admin(self):
        data = self._get_selected_admin()
        if not data: return
        _, admin_id, nombre, _ = data
        self._modificar_admin_directo(admin_id, nombre)

    def _modificar_admin_directo(self, admin_id, nombre):
        dlg = ModificarAdminDialog(nombre, self)
        if dlg.exec_() == QDialog.Accepted:
            nuevo_nombre = dlg.get_nombre()
            if not nuevo_nombre:
                self._notificar(t("users_page.admin_update_empty_name_error", default="❌  El nombre no puede estar vacío."), ok=False)
                return
            ok = modificar_admin(admin_id, nuevo_nombre)
            if ok:
                self._notificar(t("users_page.admin_update_ok", default="✅  Administrador actualizado correctamente."), ok=True)
                self.refresh_data()
            else:
                self._notificar(t("users_page.admin_update_error", default="❌  No se pudo actualizar. El nombre puede estar duplicado."), ok=False)

    # ── Notificaciones ────────────────────────────────────────────────────────

    def _notificar(self, texto: str, ok: bool):
        msg = QMessageBox(self)
        msg.setWindowTitle(t("users_page.notification_title", default="Resultado"))
        msg.setText(texto)
        msg.setIcon(QMessageBox.Information if ok else QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet(_MSG_STYLE)
        msg.exec_()

    # ── Filtrado de búsqueda ────────────────────────────────────────────────

    def _filter_users(self, text: str):
        """Filtra la tabla de usuarios por ID, nombre o número de cuenta."""
        query = text.strip().lower()
        if not query:
            self._populate_user_table(self._all_users)
            return
        filtered = [
            u for u in self._all_users
            if query in str(u.get("id", "")).lower()
            or query in str(u.get("nombre", "")).lower()
            or query in str(u.get("account_number", "")).lower()
        ]
        self._populate_user_table(filtered)

    def _filter_admins(self, text: str):
        """Filtra la tabla de admins por nombre, ID o número de cuenta."""
        query = text.strip().lower()
        if not query:
            self._populate_admin_table(self._all_admins)
            return
        filtered = [
            a for a in self._all_admins
            if query in str(a.get("id_admin", "")).lower()
            or query in str(a.get("nombre", "")).lower()
            or query in str(a.get("account_number", "")).lower()
        ]
        self._populate_admin_table(filtered)

    # ── Carga de datos ────────────────────────────────────────────────────────

    def refresh_data(self):
        self._load_users()
        self._load_admins()

    def _load_users(self):
        self._all_users = obtener_lista_usuarios()
        # Reaplicar filtro activo si hay texto en el buscador
        query = self.user_search.text().strip()
        if query:
            self._filter_users(query)
        else:
            self._populate_user_table(self._all_users)

    def _populate_user_table(self, users):
        """Llena la tabla de usuarios con la lista proporcionada."""
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            is_active = bool(user.get("is_active", 1))
            estado = t("users_page.status_active", default="Activo") if is_active else t("users_page.status_inactive", default="Baja")
            color  = "#86efac" if is_active else "#f87171"
            user_id = user.get("id", 0)
            nombre  = str(user.get("nombre", ""))

            self.user_table.setItem(row, 0, QTableWidgetItem(str(user_id)))
            self.user_table.setItem(row, 1, QTableWidgetItem(nombre))
            self.user_table.setItem(row, 2, QTableWidgetItem(str(user.get("account_number", "N/A"))))
            self.user_table.setItem(row, 3, QTableWidgetItem(str(user.get("tipo_usuario", ""))))

            estado_item = QTableWidgetItem(estado)
            estado_item.setForeground(__import__("PyQt5.QtGui", fromlist=["QColor"]).QColor(color))
            self.user_table.setItem(row, 4, estado_item)
            self.user_table.setItem(row, 5, QTableWidgetItem(str(user.get("fecha_registro", ""))))

            self.user_table.setCellWidget(row, 6, self._make_user_action_widget(user_id, nombre, is_active))
            self.user_table.setRowHeight(row, 38)

        self.user_table.resizeRowsToContents()

    def _load_admins(self):
        self._all_admins = obtener_lista_admins()
        # Reaplicar filtro activo si hay texto en el buscador
        query = self.admin_search.text().strip()
        if query:
            self._filter_admins(query)
        else:
            self._populate_admin_table(self._all_admins)

    def _populate_admin_table(self, admins):
        """Llena la tabla de admins con la lista proporcionada."""
        self.admin_table.setRowCount(len(admins))
        for row, admin in enumerate(admins):
            is_active = bool(admin.get("is_active", 1))
            estado = t("users_page.status_active", default="Activo") if is_active else t("users_page.status_inactive", default="Baja")
            color  = "#86efac" if is_active else "#f87171"
            admin_id = admin.get("id_admin", 0)
            nombre   = str(admin.get("nombre", ""))

            self.admin_table.setItem(row, 0, QTableWidgetItem(str(admin_id)))
            self.admin_table.setItem(row, 1, QTableWidgetItem(nombre))
            self.admin_table.setItem(row, 2, QTableWidgetItem(str(admin.get("account_number", "N/A"))))
            self.admin_table.setItem(row, 3, QTableWidgetItem("••••••••••••"))

            estado_item = QTableWidgetItem(estado)
            estado_item.setForeground(__import__("PyQt5.QtGui", fromlist=["QColor"]).QColor(color))
            self.admin_table.setItem(row, 4, estado_item)
            self.admin_table.setItem(row, 5, QTableWidgetItem(str(admin.get("created_at", ""))))

            self.admin_table.setCellWidget(row, 6, self._make_admin_action_widget(admin_id, nombre, is_active))
            self.admin_table.setRowHeight(row, 38)

        self.admin_table.resizeRowsToContents()

    # ── Widgets de acción por fila ───────────────────────────────────────────

    def _make_user_action_widget(self, user_id, nombre, is_active):
        from PyQt5.QtWidgets import QWidget as _W, QHBoxLayout as _H
        w = _W()
        w.setStyleSheet("background: transparent;")
        lay = _H(w)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(3)

        _S = "QPushButton { border-radius:4px; font-size:13px; font-weight:700; } QPushButton:hover { opacity:0.85; }"

        btn_mod = QPushButton("✏")
        btn_mod.setFixedSize(26, 26)
        btn_mod.setCursor(Qt.PointingHandCursor)
        btn_mod.setToolTip(t("users_page.tooltip_modify", default="Modificar"))
        btn_mod.setStyleSheet("QPushButton { background:#1e3a5f; border:1px solid #38bdf8; border-radius:4px; color:#7dd3fc; font-size:13px; } QPushButton:hover { background:#1e4d7a; color:#fff; }")
        btn_mod.clicked.connect(lambda _, uid=user_id, n=nombre: self._modificar_usuario_directo(uid, n))

        btn_baja = QPushButton("⛔" if is_active else "✅")
        btn_baja.setFixedSize(26, 26)
        btn_baja.setCursor(Qt.PointingHandCursor)
        btn_baja.setToolTip(t("users_page.tooltip_toggle_status", default="Dar de baja" if is_active else "Reactivar"))
        btn_baja.setStyleSheet("QPushButton { background:#78350f; border:1px solid #f59e0b; border-radius:4px; color:#fde68a; font-size:13px; } QPushButton:hover { background:#92400e; color:#fff; }")
        btn_baja.clicked.connect(lambda _, uid=user_id, n=nombre, active=is_active: self._toggle_baja_usuario_directo(uid, n, active))

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(26, 26)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip(t("users_page.tooltip_delete", default="Eliminar"))
        btn_del.setStyleSheet("QPushButton { background:#7f1d1d; border:1px solid #ef4444; border-radius:4px; color:#fca5a5; font-size:13px; } QPushButton:hover { background:#991b1b; color:#fff; }")
        btn_del.clicked.connect(lambda _, uid=user_id, n=nombre: self._eliminar_usuario_directo(uid, n))

        lay.addWidget(btn_mod)
        lay.addWidget(btn_baja)
        lay.addWidget(btn_del)
        return w

    def _make_admin_action_widget(self, admin_id, nombre, is_active):
        from PyQt5.QtWidgets import QWidget as _W, QHBoxLayout as _H
        w = _W()
        w.setStyleSheet("background: transparent;")
        lay = _H(w)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(3)

        btn_mod = QPushButton("✏")
        btn_mod.setFixedSize(26, 26)
        btn_mod.setCursor(Qt.PointingHandCursor)
        btn_mod.setToolTip(t("users_page.tooltip_modify", default="Modificar"))
        btn_mod.setStyleSheet("QPushButton { background:#1e3a5f; border:1px solid #38bdf8; border-radius:4px; color:#7dd3fc; font-size:13px; } QPushButton:hover { background:#1e4d7a; color:#fff; }")
        btn_mod.clicked.connect(lambda _, aid=admin_id, n=nombre: self._modificar_admin_directo(aid, n))

        btn_baja = QPushButton("⛔" if is_active else "✅")
        btn_baja.setFixedSize(26, 26)
        btn_baja.setCursor(Qt.PointingHandCursor)
        btn_baja.setToolTip(t("users_page.tooltip_toggle_status", default="Dar de baja" if is_active else "Reactivar"))
        btn_baja.setStyleSheet("QPushButton { background:#78350f; border:1px solid #f59e0b; border-radius:4px; color:#fde68a; font-size:13px; } QPushButton:hover { background:#92400e; color:#fff; }")
        btn_baja.clicked.connect(lambda _, aid=admin_id, n=nombre, active=is_active: self._toggle_baja_admin_directo(aid, n, active))

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(26, 26)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip(t("users_page.tooltip_delete", default="Eliminar"))
        btn_del.setStyleSheet("QPushButton { background:#7f1d1d; border:1px solid #ef4444; border-radius:4px; color:#fca5a5; font-size:13px; } QPushButton:hover { background:#991b1b; color:#fff; }")
        btn_del.clicked.connect(lambda _, aid=admin_id, n=nombre: self._eliminar_admin_directo(aid, n))

        lay.addWidget(btn_mod)
        lay.addWidget(btn_baja)
        lay.addWidget(btn_del)
        return w
