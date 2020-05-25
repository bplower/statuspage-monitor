# StatusPage Monitor

This is a lightweight MacOS menubar app for watching the status of services that use StatusPage. When a monitored service logs an incident, the icon will change to indicate the severity. Clicking the entry for the service will take you to the configured StatusPage for more information about the status.

<p align="center">
  <img width="50%" src="https://i.imgur.com/OI5xYse.png">
</p>

## Usage

### Preferences

Example preferences file:
```
{
    "profiles": [
        {
            "name": "Github",
            "hostname": "www.githubstatus.com"
        }
    ]
}
```

The value for the hostname field must be the domain name serving the [StatusPage](https://www.statuspage.io/) site. If you're unsure if you have the correct hostname, you can test it by browsing directly to the status api page: `https://foo.bar.baz/api/v2/status.json`. If you get a valid json response, then you likely have the correct hostname.

## Development

Set up the environment and dependencies

```
virtualenv -p python3 venv
source ./venv/bin/activate
pip install -r requirements.txt
```

Now you can build the development version of the app and run it:

```
make build-dev
make run
```

Once you're ready, you can build the full release version by running:

```
make build
```
