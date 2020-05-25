import os.path
import subprocess
import json
import rumps
import webbrowser
import requests
import functools

class StatusController(object):
    STATUS_NONE = 0
    STATUS_MINOR = 1
    STATUS_MAJOR = 2
    STATUS_CRITICAL = 3

    STATUSES = [
        STATUS_NONE,
        STATUS_MINOR,
        STATUS_MAJOR,
        STATUS_CRITICAL
    ]

    STATUSPAGE_NONE = 'none'
    STATUSPAGE_MINOR = 'minor'
    STATUSPAGE_MAJOR = 'major'
    STATUSPAGE_CRITICAL = 'critical'

    STATUSPAGE_STATUSES = [
        STATUSPAGE_NONE,
        STATUSPAGE_MINOR,
        STATUSPAGE_MAJOR,
        STATUSPAGE_CRITICAL
    ]

    STATUSPAGE_STATUS_MAP = {
        STATUSPAGE_NONE: STATUS_NONE,
        STATUSPAGE_MINOR: STATUS_MINOR,
        STATUSPAGE_MAJOR: STATUS_MAJOR,
        STATUSPAGE_CRITICAL: STATUS_CRITICAL
    }

    ICON_NONE = 'icons/check-mark-button.png'
    ICON_MINOR = 'icons/exclamation-mark.png'
    ICON_MAJOR = 'icons/warning.png'
    ICON_CRITICAL = 'icons/collision.png'

    STATUS_ICON_MAP = {
        STATUS_NONE: ICON_NONE,
        STATUS_MINOR: ICON_MINOR,
        STATUS_MAJOR: ICON_MAJOR,
        STATUS_CRITICAL: ICON_CRITICAL
    }

    @classmethod
    def icon_for_status(cls, status):
        if status not in cls.STATUSES:
            raise ValueError("Invalid status '{}'. Must be one of {}".format(status, cls.STATUSES))
        return cls.STATUS_ICON_MAP[status]

    @classmethod
    def status_from_statuspage(cls, statuspage_status):
        if statuspage_status not in cls.STATUSPAGE_STATUSES:
            raise ValueError("Invalid statuspage status '{}'. Must be one of {}".format(statuspage_status, cls.STATUSPAGE_STATUSES))
        return cls.STATUSPAGE_STATUS_MAP[statuspage_status]

class StatusPageProfile(object):
    def __init__(self, name, hostname):
        self.proto = None
        self.hostname = None
        self._clean_hostname(hostname) # Sets proto & hostname
        self.name = name
        self._status = None
        self.refresh_status()

    def _clean_hostname(self, value):
        if value.endswith('/'):
            value = value[:-1]
        if value.startswith('https://'):
            self.proto = 'https'
            value = value.replace('https://', '')
        elif value.startswith('http://'):
            self.proto = 'http'
            value = value.replace('http://', '')
        self.hostname = value

    @property
    def uri_base(self):
        return "{}://{}".format(self.proto, self.hostname)

    @property
    def uri_status(self):
        return "{}/api/v2/status.json".format(self.uri_base)

    def open_browser(self, _):
        webbrowser.open(self.uri_base)

    def as_menu_item(self):
        status_icon = StatusController.icon_for_status(self._status)
        return rumps.MenuItem(self.name, callback=self.open_browser, icon=status_icon)

    def get_status(self):
        result = requests.get(self.uri_status)
        if result.status_code != 200:
            print("Failed to request status endpoint for {}".format(self.name))

        indicator = result.json()["status"]["indicator"]
        return StatusController.status_from_statuspage(indicator)

    def refresh_status(self):
        self._status = self.get_status()
        return self._status

class StatusPageBarApp(rumps.App):
    SETTINGS_FILENAME = 'settings.json'

    def refresh_menu_item(self):
        return rumps.MenuItem('Refresh', callback=self.hook_refresh_statuses)

    def preferences_menu_item(self):
        return rumps.MenuItem('Preferences', callback=self.hook_open_preferences)

    def quit_menu_item(self):
        return rumps.MenuItem('Quit', callback=self.hook_quit)

    def hook_refresh_statuses(self, _):
        self.refresh_statuses()

    def hook_open_preferences(self, _):
        self.open_preferences()

    def hook_quit(self, _):
        rumps.quit_application()

    @rumps.timer(5)
    def periodic_update(self, _):
        self.refresh_statuses()

    def refresh_statuses(self):
        statuses = []
        menu_items = []
        for p in self.profile_list.values():
            statuses.append(p.refresh_status())
            menu_items.append(p.as_menu_item())

        # Reset the menubar icon
        worst_status = functools.reduce(lambda a, b: a if a > b else b, statuses)
        self.icon = StatusController.icon_for_status(worst_status)
        # Redeclare the menu items
        self.menu.clear()
        self.menu.update([
            *menu_items,
            None,
            self.refresh_menu_item(),
            self.preferences_menu_item(),
            self.quit_menu_item()
        ])

    def open_preferences(self):
        settings_filepath = os.path.join(rumps.application_support(self.name), self.SETTINGS_FILENAME)
        subprocess.run(['open', settings_filepath], check=True)

    def add_profiles(self, profile_list):
        for i in profile_list:
            self.add_profile(i)

    def add_profile(self, profile):
        if hasattr(self, 'profile_list') is False:
            setattr(self, 'profile_list', {})
        self.profile_list[profile.name] = profile

    def validate_settings(self):
        with self.open(self.SETTINGS_FILENAME, 'w+') as file_wr:
            try:
                json.loads(file_wr.read())
                return True
            except:
                # If the content is invalid, then we need to open the file so the user can fix it
                file_wr.close()
                self.open_preferences()
                return False

def main(debug_mode=True):
    profiles = [
        StatusPageProfile('Github', 'https://www.githubstatus.com/'),
        StatusPageProfile('My Flakey Service', 'http://localhost:8088/'),
        StatusPageProfile('Digital Ocean', 'https://status.digitalocean.com/'),
    ]
    app = StatusPageBarApp('Settings Page Notifier', title=None, icon=StatusController.ICON_NONE, quit_button=None)
    app.add_profiles(profiles)
    app.refresh_statuses()
    app.run(debug=debug_mode)

if __name__ == "__main__":
    main()
