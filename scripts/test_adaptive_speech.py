"""Mocked adaptive integration: no credentials, DB, or external network."""
import asyncio
import base64
import json
from dataclasses import replace
from types import SimpleNamespace

import test_quota_endpoints as fixture
from backend.speech_plan import PlanDecoder, VoiceProfile, normalize_profile, resolve_segment, guarded_events

service = fixture.service


class MemorySpeech:
    def __init__(self): self.rows = {}
    def begin(self, owner, request_id, conversation, persona, voice, model, sample_rate):
        if request_id in self.rows: raise ValueError('duplicate')
        self.rows[request_id] = dict(user_id=owner, request_id=request_id, conversation_id=conversation, persona_id=persona, voice=voice, model=model, sample_rate=sample_rate, status='pending')
    def get(self, owner, request_id):
        row = self.rows.get(request_id)
        return row if row and row['user_id']==owner else None
    def finish(self, owner, request_id, plan, pcm, status):
        self.rows[request_id].update(plan=plan, audio=pcm, status=status)


class Personas:
    style = {'pace_mode':'auto', 'emotion_mode':'auto'}
    def get_persona(self, persona_id, owner):
        if owner != 'user-a' or persona_id != 'persona-a': return None
        return dict(id=persona_id, voice_id='', compiled_prompt='温和的AI陪伴', persona={'layer2_expression_dna':{'voice_style':self.style}})


class ScopedData(fixture.FakeAppDataStore):
    def history(self, owner, limit, conversation_id):
        if owner != 'user-a' or conversation_id != 'conversation-a': raise ValueError('not owned')
        return {'messages':[
            {'role':'user','content':'刚才的画面','attachments':[{'kind':'image','object_key':'owned/image.png'}]},
            {'role':'ai','content':'我看到了。'},
            {'role':'user','content':'帮我看看这段内容'}
        ]}


class SignedOSS:
    def __init__(self, settings): pass
    def presign_object_download(self, key): return 'https://example.invalid/fresh/' + key


class PlannedLLM(fixture.FakeLLMProvider):
    seen = []
    mode = 'normal'
    closed = False
    async def stream_events(self, messages, **kwargs):
        type(self).calls += 1
        self.seen.append(messages)
        try:
            content = '{"scene":"chat","text":"我会认真听你说。"}\n'
            if self.mode == 'bad': content = '没有句号的普通回复'
            for i in range(0,len(content),3):
                yield {'type':'delta','text':content[i:i+3]}
            if self.mode == 'wait': await asyncio.Event().wait()
            yield {'type':'usage', 'usage':{'prompt_tokens':20,'completion_tokens':10,'total_tokens':30}}
        finally: type(self).closed = True


class TTS(fixture.FakeTTSProvider):
    seen = []
    async def stream_synthesize(self, text, **options):
        self.seen.append((text,options))
        async for item in super().stream_synthesize(text, **options): yield item


def parser_checks():
    pretty = PlanDecoder()
    decoded = []
    for char in '{\n "scene": "chat",\n "text": "你好"\n}\n{"text":"再见"}':
        decoded.extend(pretty.feed(char))
    decoded.extend(pretty.feed('', final=True))
    assert [r['text'] for r in decoded] == ['你好','再见']
    parser = PlanDecoder()
    records=[]
    raw='{"text":"[angry]你好\\n世界","tag":[],"effect":{}}\n'
    for char in raw: records.extend(parser.feed(char))
    segment=resolve_segment(records[0], VoiceProfile())
    assert segment['text']=='你好\n世界' and '[' not in segment['tts_text']
    p=normalize_profile({'pace':'slow','emotion':'calm','rate':.6, 'effects':'off'})
    s=resolve_segment({'text':'你好','rate':1.15,'tag':'angry','effect':'giggles'},p)
    assert s['rate']==.6 and s['tag']=='' and s['effect']==''
    assert '平静' in s['instruction']
    assert resolve_segment({'text':'你好','rate':float('nan'),'tag':'unlisted'},VoiceProfile())['rate']==1
    comfort = resolve_segment({'text':'今天确实不好受。','scene':'comfort'}, VoiceProfile(instruction='新闻播报', scenario='广告配音'))
    assert comfort['rate']==.96 and '温暖认真' in comfort['instruction']
    assert '新闻播报' not in comfort['instruction'] and '广告配音' not in comfort['instruction']
    continuation = resolve_segment({'text':'接着聊。','scene':'celebrate'}, VoiceProfile(), turn_style=comfort)
    assert continuation['scene']=='comfort' and continuation['rate']==comfort['rate']
    celebration = resolve_segment({'text':'过了，太好了！','scene':'celebrate'}, VoiceProfile())
    assert celebration['rate']==1.04 and '喜悦' in celebration['instruction']
    assert resolve_segment({'text':'你好','scene':[]},VoiceProfile())['scene']=='chat'
    fixed = resolve_segment({'text':'你好','scene':'celebrate'},VoiceProfile(pace_mode='manual',rate=.8))
    assert fixed['rate']==.8
    cosy = resolve_segment({'text':'你好'},VoiceProfile(emotion_mode='manual',control_tag='curious',effects='manual',effect_tag='giggles'),model='cosyvoice-v3.5-plus')
    assert cosy['tts_text']=='你好' and cosy['instruction'] and not cosy['effect']
    configured = resolve_segment({'text':'你好'},VoiceProfile(rate=.8,volume=0),model='cosyvoice-v3.5-plus')
    assert configured['rate']==.8 and configured['volume']==0
    raw = resolve_segment({'text':'你好'},VoiceProfile(use_defaults=True,rate=.7,pitch=1.5,instruction='甜美'),model='cosyvoice-v3.5-plus')
    assert raw['use_defaults'] and not raw['instruction'] and raw['rate']==1
    try: list(PlanDecoder().feed('x'*8193))
    except ValueError: pass
    else: raise AssertionError('unbounded parser')


async def cancellation_check(store):
    PlannedLLM.mode='wait'; TTS.wait_after_pcm=True
    request=service.ChatRequest(**fixture.payload('adaptive-cancel'), adaptive_voice=True, persona_id='persona-a')
    response=await service.chat_and_tts_stream(request,user_id='user-a')
    async def read():
        async for item in response.body_iterator:
            if 'audio.delta' in item: raise asyncio.CancelledError()
    try: await read()
    except asyncio.CancelledError: pass
    finally: await response.body_iterator.aclose()
    assert store.rows['adaptive-cancel']['status']=='interrupted'
    assert PlannedLLM.closed and TTS.stream_closed
    PlannedLLM.mode='normal'; TTS.wait_after_pcm=False


async def deadline_check():
    closed = False
    async def stalled():
        nonlocal closed
        try:
            yield {'type':'delta','text':'{"text":"已完成正文",'}
            await asyncio.Event().wait()
        finally: closed = True
    decoder = PlanDecoder()
    try:
        async for item in guarded_events(stalled(),lambda:False,first_timeout=.02):
            list(decoder.feed(item['text']))
    except TimeoutError:
        assert list(decoder.feed('',final=True))==[{'text':'已完成正文'}]
    else: raise AssertionError('deadline not enforced')
    assert closed


def main():
    parser_checks()
    asyncio.run(deadline_check())
    service.settings=replace(service.settings, database_url='test', billing_enforcement_mode='hard', cookie_secure=False)
    billing=fixture.FakeBillingStore(); service.billing_store=billing
    service.app_data_store=ScopedData()
    service.OSSProvider=SignedOSS
    service.persona_store=Personas(); service.speech_store=MemorySpeech()
    service.voice_store=None; service.BailianLLMProvider=PlannedLLM; service.BailianTTSProvider=TTS
    service.QuotaExceededError=fixture.QuotaExceededError
    client=fixture.TestClient(service.app); client.cookies.set(service.SESSION_COOKIE,'session-a')
    media=[{'type':'text','text':'帮我看看这段内容'}, {'type':'image_url','image_url':{'url':'https://example.invalid/image.png'}}, {'type':'video_url','video_url':{'url':'https://example.invalid/movie.mp4'}}]
    body=dict(request_id='adaptive-a', messages=[{'role':'system','content':'不要发送这个提示词'},{'role':'user','content':media}], adaptive_voice=True, persona_id='persona-a')
    response=client.post('/api/chat-and-tts/stream',json=body)
    assert response.status_code==200, response.text
    events=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert any(e['type']=='audio.asset' for e in events),response.text
    display=''.join(e.get('text','') for e in events if e['type']=='text.delta')
    assert display=='我会认真听你说。\n' and 'scene' not in display
    assert PlannedLLM.seen[-1][-1]['content']==media
    assert TTS.seen[-1][0]=='我会认真听你说。'
    assert TTS.seen[-1][1]['rate']==1.0
    system_messages = [m for m in PlannedLLM.seen[-1] if m['role']=='system']
    assert len(system_messages)==1 and '简洁口语' in system_messages[0]['content']
    assert 'NDJSON' in system_messages[0]['content'] and '不要发送这个提示词' not in system_messages[0]['content']
    assert '温和共情' not in TTS.seen[-1][1]['instruction']
    manual=resolve_segment({'text':'你好','rate':1.15}, VoiceProfile(pace_mode='manual', rate=.9, emotion_mode='manual', control_tag='curious', effects='manual', effect_tag='giggles'))
    assert manual['rate']==.9 and manual['tts_text']=='[curious]你好[giggles]'
    assert service.speech_store.rows['adaptive-a']['status']=='complete'
    service.voice_store=fixture.FakeVoiceStore({'voice-own':{'user_id':'user-a','voice_id':'voice-own','active':True,'target_model':'qwen-audio-3.0-tts-flash'}})
    selected=client.post('/api/chat-and-tts/stream?voice=voice-own',json={**body,'request_id':'selected-voice'})
    assert selected.status_code==200 and TTS.seen[-1][1]['voice']=='voice-own'
    forced_default=client.post('/api/chat-and-tts/stream?voice=__default__',json={**body,'request_id':'forced-default'})
    assert forced_default.status_code==200 and TTS.seen[-1][1]['voice']==service.settings.tts_voice
    service.voice_store=None
    before=TTS.calls
    original_tts = TTS.seen[0]
    from unittest.mock import patch
    from backend.billing_store import tts_character_rate
    assert tts_character_rate('cosyvoice-v3.5-plus',1)==1.5
    assert tts_character_rate('qwen-audio-3.0-tts-flash',1)==1
    class ReadyClone:
        status='OK'
        def __init__(self, settings): pass
        async def voice_status(self, voice_id): return self.status
    cosy_id='cosyvoice-v3.5-plus-test-owned'
    service.voice_store=fixture.FakeVoiceStore({cosy_id:{'user_id':'user-a','voice_id':cosy_id,'active':True,'target_model':'cosyvoice-v3.5-plus'}})
    with patch.object(service,'BailianVoiceCloneProvider',ReadyClone):
        cosy_response=client.post('/api/chat-and-tts/stream?voice='+cosy_id,json={**body,'request_id':'cosy-ok'})
        assert cosy_response.status_code==200 and 'audio.asset' in cosy_response.text
        assert TTS.seen[-1][1]['model']=='cosyvoice-v3.5-plus'
        ReadyClone.status='DEPLOYING'
        assert client.post('/api/chat-and-tts/stream?voice='+cosy_id,json={**body,'request_id':'cosy-pending'}).status_code==409
        ReadyClone.status='UNDEPLOYED'
        assert client.post('/api/chat-and-tts/stream?voice='+cosy_id,json={**body,'request_id':'cosy-rejected'}).status_code==409
    service.voice_store=None
    before=TTS.calls
    audio=client.get('/api/speech-turns/adaptive-a/audio')
    assert audio.status_code==200 and audio.content[:4]==b'RIFF' and TTS.calls==before
    other=fixture.TestClient(service.app); other.cookies.set(service.SESSION_COOKIE,'session-b')
    assert other.get('/api/speech-turns/adaptive-a/audio').status_code==404
    assert other.post('/api/chat-and-tts/stream',json={**body,'request_id':'other'}).status_code==404
    calls=PlannedLLM.calls
    replay=client.post('/api/chat-and-tts/stream',json={**fixture.payload('replay-a'), 'replay_turn_id':'adaptive-a'})
    assert replay.status_code==200 and 'audio.asset' in replay.text
    assert PlannedLLM.calls==calls
    assert TTS.seen[-1]==original_tts
    scoped=client.post('/api/chat-and-tts/stream',json={**body,'request_id':'scoped','conversation_id':'conversation-a'})
    assert scoped.status_code==200 and 'audio.asset' in scoped.text
    assert PlannedLLM.seen[-1][1]['content'][1]['image_url']['url'].endswith('/fresh/owned/image.png')
    assert PlannedLLM.seen[-1][-1]['content']==media
    denied=client.post('/api/chat-and-tts/stream',json={**body,'request_id':'denied','conversation_id':'conversation-b'})
    assert denied.status_code==404
    invalid=client.put('/api/personas/persona-a',json={'persona':{'layer2_expression_dna':{'voice_style':{'rate':9}}}})
    assert invalid.status_code==422
    PlannedLLM.mode='bad'
    response=client.post('/api/chat-and-tts/stream',json={**body,'request_id':'bad-meta'})
    plain_events=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert ''.join(e.get('text','') for e in plain_events if e['type']=='text.delta') == '没有句号的普通回复\n'
    assert 'audio.asset' in response.text
    PlannedLLM.mode='normal'
    billing.fail_metric='ai_voice_seconds'
    response=client.post('/api/chat-and-tts/stream',json={**body,'request_id':'no-voice'})
    assert 'audio.quota_exhausted' in response.text and 'audio.asset' not in response.text
    billing.fail_metric=None
    asyncio.run(asyncio.wait_for(cancellation_check(service.speech_store),5))
    print('PASS adaptive media context, tag filtering, manual overrides, PCM asset/replay, ownership, malformed metadata, quota and cancellation')


if __name__=='__main__': main()
