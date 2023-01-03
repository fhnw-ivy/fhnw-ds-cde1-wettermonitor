class ServiceStatus:
    is_live = False
    last_fetch = None
    last_update = None

    @staticmethod
    def get_status():
        return [ServiceStatus.is_live, ServiceStatus.last_fetch]

    @staticmethod
    def update_last_fetch(time):
        # Convert time to current timezone
        if time is not None:
            ServiceStatus.last_fetch = time.tz_localize('UTC').tz_convert('Europe/Berlin')