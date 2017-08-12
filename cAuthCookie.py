import codecs
import datetime
import json
import os.path

import cLogger

try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, settings_file):
    cache_settings = api.settings
    with open(settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        cLogger.log('[I] New settings file was made: {0!s}'.format(settings_file), "GREEN")


def login(username, password):
    from cMain import scriptVersion
    cLogger.log('PYINSTALIVE DOWNLOADER (Script v{0!s})'.format(scriptVersion), "GREEN")
    cLogger.seperator("GREEN")

    device_id = None
    try:
        
        settings_file = "credentials.json"
        if not os.path.isfile(settings_file):
            # settings file does not exist
            cLogger.log('[W] Unable to find settings file: {0!s}'.format(settings_file), "YELLOW")

            # login new
            api = Client(
                username, password,
                on_login=lambda x: onlogin_callback(x, settings_file))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            # cLogger.log('[I] Using settings file: {0!s}'.format(settings_file), "GREEN")

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                username, password,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        cLogger.log('[E] ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e), "RED")

        # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(
            username, password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, settings))

    except ClientLoginError as e:
        cLogger.log('[E] ClientLoginError: {0!s}'.format(e), "RED")
        sys.exit(9)
    except ClientError as e:
        cLogger.log('[E] ClientError: {0!s}'.format(e), "RED")
        sys.exit(9)
    except Exception as e:
        cLogger.log('[E] Unexpected Exception: {0!s}'.format(e), "RED")
        sys.exit(99)

    # Show when login expires
    # cookie_expiry = api.cookie_jar.expires_earliest
    # print('[I] Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%S')), "WHITE")
    cLogger.log('[I] Login to "' + username + '" OK!', "GREEN")
    return api