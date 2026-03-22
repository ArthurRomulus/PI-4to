import sys
from PyQt5.QtWidgets import QApplication
from ui.admin.admin_panel import AdminPanelWindow

app = QApplication(sys.argv)
window = AdminPanelWindow()
window.show()
sys.exit(app.exec_())