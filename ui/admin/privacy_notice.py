"""
privacy_notice.py
Ventana de aviso de privacidad para el sistema de reconocimiento facial.

Este módulo muestra al usuario el aviso de privacidad antes de registrar
sus datos biométricos (reconocimiento facial).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.i18n import t


class PrivacyNoticeDialog(QDialog):
    """
    Diálogo que muestra el aviso de privacidad del sistema.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("privacy_notice.window_title", default="Aviso de Privacidad"))
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
            QLabel {
                color: #f1f5f9;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #1e293b;
                border: 2px solid #38bdf8;
                border-radius: 10px;
                padding: 12px 24px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #38bdf8;
                color: #0f172a;
            }
            QScrollArea {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #1e293b;
                border: none;
                color: #cbd5e1;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # ── Título ───────────────────────────────────────────────────────────
        title = QLabel(t("privacy_notice.title", default="📋 Aviso de Privacidad"))
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #38bdf8; border: none;")
        title.setAlignment(Qt.AlignCenter)
        
        # ── Subtítulo ─────────────────────────────────────────────────────────
        subtitle = QLabel(t("privacy_notice.subtitle", default="Sistema de Reconocimiento Facial Biometrico"))
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #94a3b8; border: none;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        # ── Contenido del aviso ───────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        
        aviso_texto = t("privacy_notice.content_html", default="""
<h2 style="color: #38bdf8;">1. Responsable del Tratamiento de Datos</h2>
<p>El responsable del tratamiento de sus datos personales es el administrador del sistema de reconocimiento facial biométrico. Los datos serán utilizados exclusivamente para el control de acceso mediante reconocimiento facial.</p>

<h2 style="color: #38bdf8;">2. Datos que se Recopilan</h2>
<p>Para el funcionamiento del sistema, se recopilarán los siguientes datos:</p>
<ul>
    <li><strong>Datos biométricos:</strong> Se capturará un embedding facial (representación matemática de los rasgos faciales) derivado de una fotografía de su rostro.</li>
    <li><strong>Nombre completo:</strong> Para identificarlo como usuario registrado en el sistema.</li>
    <li><strong>Fecha y hora de registro:</strong> Para auditoría y control del sistema.</li>
</ul>

<h2 style="color: #38bdf8;">3. Finalidad del Tratamiento</h2>
<p>Sus datos serán utilizados exclusivamente para:</p>
<ul>
    <li>Verificar su identidad mediante reconocimiento facial al momento de acceder al sistema.</li>
    <li>Controlar el acceso a áreas o funciones restringidas.</li>
    <li>Mantener un registro de usuarios autorizados.</li>
</ul>

<h2 style="color: #38bdf8;">4. Protección de sus Datos</h2>
<p>Nos comprometemos a:</p>
<ul>
    <li>Almacenar sus datos biométricos de forma segura y encriptada.</li>
    <li>No compartir sus datos con terceros sin su consentimiento expreso.</li>
    <li>No utilizar sus datos para fines distintos a los aquí descritos.</li>
    <li>Implementar medidas de seguridad técnicas y administrativas apropiadas.</li>
</ul>

<h2 style="color: #38bdf8;">5. Derechos del Titular</h2>
<p>Usted tiene derecho a:</p>
<ul>
    <li><strong>Acceder:</strong> Conocer qué datos personales tenemos de usted.</li>
    <li><strong>Rectificar:</strong> Solicitar la corrección de datos inexactos.</li>
    <li><strong>Eliminar:</strong> Solicitar la eliminación de sus datos cuando así lo desee.</li>
    <li><strong>Oponerse:</strong> Oponerse al tratamiento de sus datos.</li>
</ul>
<p>Para ejercer estos derechos, contacte al administrador del sistema.</p>

<h2 style="color: #38bdf8;">6. Consentimiento</h2>
<p>Al hacer clic en "Aceptar" y proceder con el registro, usted:</p>
<ul>
    <li>Manifiesta que ha leído y comprende el presente aviso de privacidad.</li>
    <li>Otorga su consentimiento expreso para el tratamiento de sus datos biométricos con las finalidades descritas.</li>
    <li>Declara que los datos proporcionados son verídicos y que cuenta con la autorización necesaria para proporcionarlos.</li>
</ul>

<h2 style="color: #38bdf8;">7. Contacto</h2>
<p>Si tiene preguntas sobre este aviso de privacidad o desea ejercer sus derechos, contacte al administrador del sistema.</p>

<hr>
<p style="color: #64748b; font-size: 12px;">Fecha de última actualización: Abril 2026</p>
""")
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        content_layout.addWidget(self.text_edit)
        scroll.setWidget(content_widget)
        
        # ── Botones ───────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_accept = QPushButton(t("privacy_notice.button_accept", default="✅ Aceptar y Continuar"))
        self.btn_accept.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton(t("privacy_notice.button_cancel", default="❌ Cancelar"))
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_accept)
        
        # ── Checkbox de confirmación ─────────────────────────────────────────
        self.confirm_check = QLabel(t("privacy_notice.confirm_text", default="☑ He leído y acepto el aviso de privacidad"))
        self.confirm_check.setStyleSheet("color: #94a3b8; font-size: 12px; border: none;")
        self.confirm_check.setAlignment(Qt.AlignCenter)
        
        # Ensamblar layout
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(scroll)
        layout.addWidget(self.confirm_check)
        layout.addLayout(btn_layout)
    
    def accept(self):
        """Sobreescribimos accept para validar que el usuario haya leído el aviso."""
        super().accept()
    
    def reject(self):
        """Sobreescribimos reject para cancelar."""
        super().reject()