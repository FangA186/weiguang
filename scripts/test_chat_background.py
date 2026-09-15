"""Mock-only background ownership, validation and persistence contract checks."""
from unittest.mock import MagicMock, patch
import test_quota_endpoints as fixture
from backend.app_data_store import AppDataStore

service = fixture.service
class Store(fixture.FakeAppDataStore):
    backgrounds = {}
    panels = {}
    def patch_chat_background(self, user, key, scope="global"):
        if scope == 'global':
            self.backgrounds[user] = key
            self.panels[user] = None
        else:
            self.panels[user] = key
        return {'id': user, 'chat_background_object_key': self.backgrounds.get(user), 'chat_panel_background_object_key': self.panels.get(user)}

store = Store()
service.app_data_store = store
client = fixture.TestClient(service.app)
endpoint = '/api/auth/chat-background'
assert client.put(endpoint, json={'object_key': None}).status_code == 401
client.cookies.set(service.SESSION_COOKIE, 'session-a')
key = 'account-avatars/user-a/background.png'
with patch.object(service, 'OSSProvider') as provider:
    oss = provider.return_value
    oss.download_object.return_value = b'\x89PNG\r\n\x1a\nimage'
    oss.presign_object_download.return_value = 'https://example.invalid/background.png'
    response = client.put(endpoint, json={'object_key': key})
    assert response.status_code == 200, response.text
    assert response.json()['chat_background_download_url'].endswith('background.png')
    assert store.backgrounds['user-a'] == key
    oss.download_object.assert_called_once_with(key, max_bytes=5*1024*1024)
    panel_key = 'account-avatars/user-a/panel.png'
    assert client.put(endpoint, json={'object_key': panel_key, 'scope': 'panel'}).status_code == 200
    assert store.panels['user-a'] == panel_key and store.backgrounds['user-a'] == key
    oss.download_object.side_effect = RuntimeError('upload failed')
    assert client.put(endpoint, json={'object_key': key, 'scope': 'global'}).status_code == 502
    assert store.panels['user-a'] == panel_key
    oss.download_object.side_effect = None
    assert client.put(endpoint, json={'object_key': key, 'scope': 'global'}).status_code == 200
    assert store.panels['user-a'] is None and store.backgrounds['user-a'] == key
    assert client.put(endpoint, json={'object_key': panel_key, 'scope': 'panel'}).status_code == 200
    assert client.put(endpoint, json={'object_key': None, 'scope': 'panel'}).status_code == 200
    assert store.backgrounds['user-a'] == key and store.panels['user-a'] is None
    assert client.put(endpoint, json={'object_key': key, 'scope': 'invalid'}).status_code == 422
    for bad in ['account-avatars/user-b/image.png', 'account-avatars/user-a/../x', 'https://example.invalid/image.png', '']:
        assert client.put(endpoint, json={'object_key': bad}).status_code == 422
    oss.download_object.return_value = b'<svg></svg>'
    assert client.put(endpoint, json={'object_key': key}).status_code == 422
    oss.download_object.side_effect = ValueError('OSS object exceeds the allowed size')
    assert client.put(endpoint, json={'object_key': key}).status_code == 422
    oss.download_object.side_effect = RuntimeError('storage failed')
    assert client.put(endpoint, json={'object_key': key}).status_code == 502
    assert store.backgrounds['user-a'] == key
    assert client.put(endpoint, json={}).status_code == 422
    assert client.put(endpoint, json={'object_key': None}).status_code == 200
    assert store.backgrounds['user-a'] is None

# Exercise the real store method: user-scoped SQL, null reset, early ownership rejection.
real = AppDataStore.__new__(AppDataStore)
connection = MagicMock()
real._connect = MagicMock()
real._connect.return_value.__enter__.return_value = connection
real.profile = MagicMock(return_value={'id': 'user-a'})
for value in [key, None]:
    real.patch_chat_background('user-a', value)
    sql, params = connection.execute.call_args.args
    assert 'WHERE id=%s' in sql and params == (value, 'user-a')
    assert 'chat_panel_background_object_key=NULL' in sql
real.patch_chat_background('user-a', key, 'panel')
sql, params = connection.execute.call_args.args
assert 'SET chat_panel_background_object_key=%s' in sql and 'chat_background_object_key=' not in sql
assert params == (key, 'user-a')
try:
    real.patch_chat_background('user-a', 'account-avatars/user-b/x.png')
except ValueError:
    pass
else:
    raise AssertionError('cross-account background accepted')
print('PASS background auth/ownership/image/size/storage failure/reset/user-scoped SQL; no DB or OSS writes')
