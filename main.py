import os
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
        else:
            self.proto = 'https'
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
        return {
            'Preferences': [
                rumps.MenuItem('Edit', callback=self.hook_open_preferences),
                rumps.MenuItem('Reload', callback=self.hook_reload_preferences)
            ]
        }
        # return rumps.MenuItem('Preferences', callback=self.hook_open_preferences)

    def quit_menu_item(self):
        return rumps.MenuItem('Quit', callback=self.hook_quit)

    def hook_refresh_statuses(self, _):
        self.refresh_statuses()

    def hook_open_preferences(self, _):
        self.open_preferences()

    def hook_reload_preferences(self, _):
        self.reload_preferences()

    def hook_quit(self, _):
        rumps.quit_application()

    @rumps.timer(60)
    def periodic_update(self, _):
        self.refresh_statuses()

    def refresh_statuses(self):
        statuses = []
        menu_items = []
        for p in self.profiles_dict.values():
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
        subprocess.run(['open', self.settings.settings_path()], check=True)

    def reload_preferences(self):
        self.settings.load()
        self.set_profiles(self.settings.profiles())
        self.refresh_statuses()

    def set_profiles(self, profiles_list):
        if hasattr(self, 'profiles_dict') is False:
            setattr(self, 'profiles_dict', {})
        profiles_dict = {}
        for i in profiles_list:
            profiles_dict[i.name] = i
        self.profiles_dict = profiles_dict

    def set_settings(self, settings):
        if hasattr(self, 'settings') is False:
            setattr(self, 'settings', {})
        self.settings = settings

class Settings(object):
    SETTINGS_FILE_NAME = '.statuspage_monitor.json'

    def __init__(self, app_name, autoload=False, settings_path=None):
        self._json_content = None
        self._settings_path_override = settings_path
        self.app_name = app_name
        if autoload is True:
            self.load()

    def settings_path(self):
        if self._settings_path_override is None:
            return os.path.join(rumps.application_support(self.app_name), self.SETTINGS_FILE_NAME)
        else:
            return self._settings_path_override

    def load(self):
        try:
            # Open the file to be read in, but create it if it doesn't already exist. Had to
            # get tricky here becuase the normal `open(filepath, 'w+')` would truncate the
            # file which was extremely useless. Got this from here:
            # https://stackoverflow.com/questions/28918302/open-file-for-random-write-without-truncating
            with os.fdopen(os.open(self.settings_path(), os.O_RDWR | os.O_CREAT), 'w+') as sfile:
                self._json_content = json.load(sfile)
        except json.JSONDecodeError:
            subprocess.run(['open', self.settings_path()], check=True)
            raise Exception("Failed to load json settings")

    def profiles(self):
        if self._json_content is None:
            raise Exception("Cannot list profiles, settings file not yet loaded.")
        profile_list = []
        for jsono in self._json_content.get('profiles', []):
            if jsono.get('name', None) is None:
                raise Exception("Profile missing required field 'name'")
            if jsono.get('hostname', None) is None:
                raise Exception("Profile missing required field 'hostname'")
            profile_list.append(
                StatusPageProfile(jsono['name'], jsono['hostname'])
            )
        return profile_list

def main(debug_mode=True):
    APP_NAME = 'Settings Page Notifier'
    if debug_mode is False:
        settings_path = None
    else:
        settings_path = "./example-settings.json"
    settings = Settings(APP_NAME, autoload=True, settings_path=settings_path)
    app = StatusPageBarApp(APP_NAME, title=None, icon=StatusController.ICON_NONE, quit_button=None)
    app.set_settings(settings)
    app.set_profiles(settings.profiles())
    app.refresh_statuses()
    app.run(debug=debug_mode)

if __name__ == "__main__":
    main()
