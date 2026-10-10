"""Test-only payment tools and trusted, exact-action approval store."""
import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
import re
from contextvars import ContextVar
RUN_ID = ContextVar("run_id", default=None)
from pathlib import Path
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent

def config():
    load_dotenv(ROOT / '.env', override=True)
    return {k: os.getenv(k, '') for k in ['OPENAI_API_KEY', 'OPENAI_MODEL', 'RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'AGNTID_MCP_URL']}

def db():
    conn = sqlite3.connect(os.getenv('DATABASE_PATH') or ROOT / 'demo.sqlite3', timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=15000')
    conn.executescript('''CREATE TABLE IF NOT EXISTS payments (slot TEXT PRIMARY KEY, order_id TEXT, payment_id TEXT);
    CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, digest TEXT, expires REAL, used INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, created REAL, kind TEXT, details TEXT);''')
    conn.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created REAL, action TEXT, mode TEXT, status TEXT, response TEXT)')
    if 'payload_digest' not in {r['name'] for r in conn.execute('PRAGMA table_info(runs)')}:
        conn.execute('ALTER TABLE runs ADD COLUMN payload_digest TEXT')
    conn.execute('CREATE TABLE IF NOT EXISTS resolutions (id TEXT PRIMARY KEY, payment_id TEXT, amount INTEGER, rationale TEXT, message TEXT, status TEXT, created REAL, result TEXT)')
    return conn

def record(kind, details):
    with db() as c:
        c.execute('INSERT INTO events(created,kind,details) VALUES(?,?,?)', (time.time(),kind,json.dumps({**details, **({'run_id':RUN_ID.get()} if RUN_ID.get() else {})})))

def digest(payment_id, amount_paise):
    return hashlib.sha256(json.dumps({'tool':'approved_refund_payment','payment_id':payment_id,'amount_paise':amount_paise},sort_keys=True,separators=(',',':')).encode()).hexdigest()

async def razorpay(method, path, body=None):
    cfg=config()
    if not cfg['RAZORPAY_KEY_ID'].startswith('rzp_test_'):
        raise ValueError('Only Razorpay TEST keys are accepted.')
    if not cfg['RAZORPAY_KEY_SECRET']:
        raise ValueError('Razorpay secret is missing in .env.')
    async with httpx.AsyncClient(timeout=25, auth=(cfg['RAZORPAY_KEY_ID'],cfg['RAZORPAY_KEY_SECRET'])) as client:
        r=await client.request(method,'https://api.razorpay.com/v1/'+path,json=body)
    if r.is_error:
        # Never log request headers or authentication values.
        code=r.json().get('error',{}).get('code','API_ERROR')
        raise ValueError(f'Razorpay rejected this request ({code}, HTTP {r.status_code}). Check the test dashboard.')
    return r.json()

def validate_payment(payment_id):
    if not isinstance(payment_id,str) or not re.fullmatch(r'pay_[A-Za-z0-9_]{1,80}',payment_id):
        raise ValueError('Invalid payment ID.')

async def get_payment(payment_id: str) -> dict:
    """Read the status and remaining refundable balance of a Razorpay test payment."""
    validate_payment(payment_id)
    p=await razorpay('GET',f'payments/{payment_id}')
    return {k:p.get(k) for k in ['id','amount','amount_refunded','currency','status','order_id']}

async def refund_payment(payment_id: str, amount_paise: int) -> dict:
    """Issue a normal Razorpay TEST refund. Amount is in paise; authorization belongs to AgntID."""
    validate_payment(payment_id)
    if not isinstance(amount_paise,int) or isinstance(amount_paise,bool) or amount_paise < 100:
        raise ValueError('Refund must be an integer amount of at least 100 paise.')
    record('razorpay_request',{'payment_id':payment_id,'amount_paise':amount_paise,'tool':'refund_payment'})
    result=await razorpay('POST',f'payments/{payment_id}/refund',{'amount':amount_paise,'speed':'normal'})
    receipt={k:result.get(k) for k in ['id','payment_id','amount','currency','status']}
    record('refund',receipt)
    return receipt

async def approved_refund_payment(payment_id: str, amount_paise: int) -> dict:
    """Refund only when a human approved this exact payment and amount within the last 5 minutes. The model cannot create approval evidence."""
    validate_payment(payment_id)
    if not isinstance(amount_paise,int) or isinstance(amount_paise,bool) or not 100 <= amount_paise <= 100000:
        raise ValueError('Approved refunds support integer amounts from 100 to 100000 paise.')
    expected=digest(payment_id,amount_paise)
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT * FROM approvals WHERE digest=? AND used=0 AND expires>? ORDER BY expires DESC LIMIT 1',(expected,time.time())).fetchone()
        if not row:
            return {'status':'review_required','reason':'No unused human approval matches this exact payment and amount.','payment_id':payment_id,'amount_paise':amount_paise,'authority':'application approval gate'}
        # Consume before the external call. An uncertain network result is never automatically retried.
        c.execute('UPDATE approvals SET used=1 WHERE id=? AND used=0',(row['id'],))
    record('approval_consumed',{'approval_id':row['id'],'arguments_digest':expected})
    return await refund_payment(payment_id,amount_paise)

TOOLS={'get_payment':get_payment,'refund_payment':refund_payment,'approved_refund_payment':approved_refund_payment}
