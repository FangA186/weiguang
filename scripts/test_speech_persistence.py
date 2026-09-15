"""Exercise real PostgreSQL voice persistence; ALL writes are rolled back."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4
import psycopg
from psycopg.rows import dict_row
from backend.config import Settings
from backend.speech_store import SpeechStore
from backend.chat_import_store import ChatImportStore
from backend.persona_store import PersonaStore


def main():
    url = Settings.from_env().database_url
    with psycopg.connect(url, row_factory=dict_row) as connection:
        owner = connection.execute('SELECT id FROM app_users LIMIT 1').fetchone()['id']
        @contextmanager
        def borrowed(*args, **kwargs):
            yield connection
        try:
            with patch('psycopg.connect', borrowed):
                speech = SpeechStore(url)
                key = 'rollback-' + uuid4().hex
                plan = [{'text':'测试', 'tts_text':'[empathetic]测试','rate':.95,'instruction':'温柔','tag':'empathetic','effect':''}]
                speech.begin(owner,key,None,None,'test','qwen-audio-3.0-tts-flash',48000)
                speech.finish(owner,key,plan,b'\x00\x00'*480,'complete')
                assert speech.get(owner,key)['plan']==plan
                assert len(speech.get(owner,key)['audio'])==960
                assert speech.get('not-owner',key) is None
                connection.execute("UPDATE speech_turns SET audio_expires_at=NOW()-INTERVAL '1 day' WHERE request_id=%s",(key,))
                assert speech.get(owner,key)['audio'] is None
                assert speech.get(owner,key)['plan']==plan
                imports = ChatImportStore.__new__(ChatImportStore)
                imports.database_url = url
                batch = imports.create_batch(user_id=owner,attachments=[])
                style = {'pace_mode':'manual','rate':.75,'traits':['清脆'],'effects':'off'}
                imports.update_messages(batch['id'],owner,[],voice_style=style)
                assert imports.get_batch(batch['id'],owner)['voice_style']==style
                personas = PersonaStore.__new__(PersonaStore)
                personas.database_url = url
                original = personas.create_persona(user_id=owner,name='事务测试',slug=key,
                    persona={'layer2_expression_dna':{'sentence_rhythm':'短句'},'layer1_identity':{'summary':'保留人设'}},
                    memories={'notes':['保留记忆']},voice_id='retained-voice')
                updated = personas.update_persona(original['id'],owner,voice_style=style)
                assert updated['persona']['layer2_expression_dna']['voice_style']==style
                assert updated['persona']['layer2_expression_dna']['sentence_rhythm']=='短句'
                assert updated['persona']['layer1_identity']==original['persona']['layer1_identity']
                assert updated['memories']==original['memories'] and updated['voice_id']=='retained-voice'
                assert personas.update_persona(original['id'],'not-owner',voice_style={}) is None
                avatar = personas.update_persona(original['id'],owner,avatar_object_key='test/owned-avatar.png')
                assert avatar['avatar_object_key']=='test/owned-avatar.png'
                assert avatar['persona']==updated['persona'] and avatar['voice_id']==updated['voice_id']
                assert personas.update_persona(original['id'],'not-owner',avatar_object_key='other.png') is None
        finally:
            connection.rollback()
    print('PASS PostgreSQL speech plan/audio/expiry/ownership and OCR form roundtrip; all writes rolled back')


if __name__ == '__main__': main()
