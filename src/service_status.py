class ServiceStatus:
    is_live = False
    last_fetch = None

    @staticmethod
    def get_status():
        return ServiceStatus.is_live, ServiceStatus.last_fetch