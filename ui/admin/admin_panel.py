from dashboard_panel import DashboardPanel


class AdminPanelWindow(DashboardPanel):
    """Compatibilidad para imports legacy del panel administrativo."""

    def __init__(self, parent=None):
        super().__init__()
        if parent is not None:
            self.setParent(parent)
