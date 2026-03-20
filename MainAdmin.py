from ui.admin.userlist import userlist;

from PyQt5.QtWidgets import QApplication; import sys;

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = userlist(admin_id=1)
    window.show()
    sys.exit(app.exec_())