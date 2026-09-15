"""Conversation edit permissions and validation, without database writes."""
import test_quota_endpoints as fixture

service = fixture.service

class Store(fixture.FakeAppDataStore):
    def update_conversation(self, owner, conversation, title, avatar):
        if owner != 'user-a' or conversation != 'owned':
            return None
        return {'id':conversation, 'title':title or '原标题', 'avatar_object_key':avatar}

service.app_data_store = Store()
service._enrich_conversation_avatars = lambda rows: None
client = fixture.TestClient(service.app)
client.cookies.set(service.SESSION_COOKIE, 'session-a')
endpoint = '/api/chat-history/conversations/owned'
assert client.patch(endpoint,json={'title':'新标题'}).json()['title']=='新标题'
assert client.patch(endpoint,json={'avatar_object_key':'account-avatars/user-a/photo.png'}).status_code==200
assert client.patch(endpoint,json={'avatar_object_key':'account-avatars/user-b/photo.png'}).status_code==403
assert client.patch(endpoint,json={'avatar_object_key':'account-avatars/user-a/../photo.png'}).status_code==403
assert client.patch(endpoint,json={'title':'   '}).status_code==422
assert client.patch(endpoint,json={'title':'字'*65}).status_code==422
assert client.patch('/api/chat-history/conversations/other',json={'title':'新标题'}).status_code==404
client.cookies.set(service.SESSION_COOKIE,'session-b')
assert client.patch(endpoint,json={'title':'新标题'}).status_code==404
print('PASS conversation edits, ownership and validation')
