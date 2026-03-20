from ui.admin.auditlogs import userlist;

from PyQt5 import QApplication, sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = userlist(admin_id=1)
    window.show()
    sys.exit(app.exec_())