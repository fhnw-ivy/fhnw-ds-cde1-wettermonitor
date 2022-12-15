import datetime

import pytz


class ServiceStatus:
    is_live = False
    last_fetch = None
    last_update = None

    @staticmethod
    def get_status():
        return ServiceStatus.is_live, ServiceStatus.last_fetch

    @staticmethod
    def update_last_fetch():
        # Set last fetch to now in timezone Europe/Zurich
        # Also check if summer or winter time is active
        ServiceStatus.last_fetch = datetime.datetime.now(pytz.timezone("Europe/Zurich"))