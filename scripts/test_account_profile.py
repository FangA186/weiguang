"""Account validation and avatar persistence; database writes are rolled back."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4
import psycopg
from psycopg.rows import dict_row
from backend.auth_validation import validate_email,validate_password,password_requirements
from backend.app_data_store import AppDataStore
from backend.config import Settings

for bad in ('x','a@b','a..b@example.com','a @example.com'):
    try: validate_email(bad)
    except ValueError: pass
    else: raise AssertionError(bad)
assert validate_email(' User+tag@Example.COM ')=='user+tag@example.com'
for bad in ('short','abcdefghij','1234567890','Letters1234'):
    try: validate_password(bad)
    except ValueError: pass
    else: raise AssertionError(bad)
assert not password_requirements('Safe-pass9')

url=Settings.from_env().database_url
with psycopg.connect(url,row_factory=dict_row) as connection:
    @contextmanager
    def borrowed(*args,**kwargs): yield connection
    try:
        store=AppDataStore.__new__(AppDataStore);store.database_url=url
        with patch('psycopg.connect',borrowed):
            email=f'avatar-{uuid4().hex}@example.invalid'
            profile,_=store.register(email,'Safe-pass9','头像测试')
            updated=store.patch_avatar(profile['id'],f"account-avatars/{profile['id']}/avatar.png")
            assert updated['avatar_object_key'].endswith('/avatar.png')
            try: store.patch_avatar(profile['id'],'account-avatars/other/avatar.png')
            except ValueError: pass
            else: raise AssertionError('cross-account avatar accepted')
            try: store.register(email,'Another-9x!','duplicate')
            except ValueError as exc: assert str(exc)=='该邮箱已注册'
            else: raise AssertionError('duplicate email accepted')
    finally: connection.rollback()
print('PASS email/password/duplicate/avatar ownership; all database writes rolled back')
