import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock,MagicMock,patch
from types import SimpleNamespace
from openai.types.chat import ChatCompletionMessage
from starlette.testclient import TestClient
import core
import app as web

class WorkspaceSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=patch.object(core,'ROOT',Path(self.temp.name));self.root.start()
        self.client=TestClient(web.app)
        self.headers={'X-Demo-Token':web.LOCAL_TOKEN,'Origin':'http://localhost:8090'}
        with core.db() as c:
            c.execute('INSERT INTO payments VALUES(?,?,?)',('ticket','order_A','pay_A'))
            c.execute('INSERT INTO payments VALUES(?,?,?)',('baseline','order_B','pay_B'))
    def tearDown(self):self.root.stop();self.temp.cleanup()
    def post(self,action,data):return self.client.post('/api/'+action,json=data,headers=self.headers)
    def test_hosted_mode_disables_demo_refund_paths(self):
        with patch.object(web,'HOSTED',True):
            for action in ('approve','agent','replay'):
                data={'request_id':'hosted-request-1234-'+action}
                self.assertEqual(self.post(action,data).status_code,403)
    def proposal(self):
        with core.db() as c:c.execute('INSERT INTO resolutions VALUES(?,?,?,?,?,?,?,NULL)',('resolution_A','pay_A',40000,'Damaged item','Refund request','proposed',1))
    def test_saved_proposal_ignores_changed_client_amount_and_executes_once(self):
        self.proposal()
        fake=AsyncMock(return_value={'result':{'id':'rfnd_TEST','status':'pending'}})
        with patch.object(web,'get_payment',AsyncMock(return_value={'amount':500000,'amount_refunded':0})),patch.object(web,'invoke',fake):
            a=self.post('resolve',{'request_id':'resolve-request-1234','resolution_id':'resolution_A','amount_paise':100000,'payment_id':'pay_B'})
            b=self.post('resolve',{'request_id':'resolve-request-5678','resolution_id':'resolution_A'})
        self.assertEqual(a.status_code,200);self.assertEqual(b.status_code,400)
        self.assertEqual(fake.await_count,1)
        self.assertEqual(fake.call_args.args[1],{'payment_id':'pay_A','amount_paise':40000})
    def test_uncertain_resolution_blocks_second_attempt(self):
        self.proposal()
        with patch.object(web,'get_payment',AsyncMock(return_value={'amount':500000,'amount_refunded':0})),patch.object(web,'invoke',AsyncMock(side_effect=TimeoutError())):
            self.post('resolve',{'request_id':'resolve-request-1234','resolution_id':'resolution_A'})
        with core.db() as c:self.assertEqual(c.execute('SELECT status FROM resolutions').fetchone()[0],'needs_reconciliation')
        self.assertEqual(self.post('resolve',{'request_id':'resolve-request-5678','resolution_id':'resolution_A'}).status_code,400)
    def test_changed_ticket_cannot_execute_old_proposal(self):
        self.proposal()
        with core.db() as c:c.execute("UPDATE payments SET payment_id='pay_NEW' WHERE slot='ticket'")
        self.assertEqual(self.post('resolve',{'request_id':'resolve-request-1234','resolution_id':'resolution_A'}).status_code,400)
    def test_rejected_proposal_cannot_execute(self):
        self.proposal()
        self.assertEqual(self.post('reject',{'resolution_id':'resolution_A'}).status_code,200)
        self.assertEqual(self.post('resolve',{'request_id':'resolve-request-1234','resolution_id':'resolution_A'}).status_code,400)
    def test_request_id_replay_executes_once(self):
        fake=AsyncMock(return_value={'tool':'refund_payment','arguments':{},'result':{'id':'rfnd_TEST'}})
        payload={'request_id':'request-1234567890','mode':'protected','tool':'refund_payment','arguments':{'payment_id':'pay_A','amount_paise':40000}}
        with patch.object(web,'invoke',fake):
            a=self.post('replay',payload);b=self.post('replay',payload)
        self.assertEqual(a.status_code,200);self.assertEqual(a.json(),b.json());self.assertEqual(fake.await_count,1)
    def test_request_id_cannot_be_reused_with_changed_amount(self):
        fake=AsyncMock(return_value={'tool':'refund_payment','arguments':{},'result':{'id':'rfnd_TEST'}})
        payload={'request_id':'request-1234567890','mode':'protected','tool':'refund_payment','arguments':{'payment_id':'pay_A','amount_paise':40000}}
        with patch.object(web,'invoke',fake):
            self.post('replay',payload)
            payload['arguments']['amount_paise']=50000
            self.assertEqual(self.post('replay',payload).status_code,409)
        self.assertEqual(fake.await_count,1)
    def test_uncertain_refund_is_not_retried_by_agent(self):
        msg=ChatCompletionMessage(role='assistant',content=None,tool_calls=[{'id':'call_A','type':'function','function':{'name':'refund_payment','arguments':'{"payment_id":"pay_A","amount_paise":40000}'}}])
        finish=ChatCompletionMessage(role='assistant',content='Please reconcile the provider outcome.')
        client=MagicMock()
        client.chat.completions.create=AsyncMock(side_effect=[SimpleNamespace(choices=[SimpleNamespace(message=msg)]),SimpleNamespace(choices=[SimpleNamespace(message=msg)]),SimpleNamespace(choices=[SimpleNamespace(message=finish)])])
        client.__aenter__=AsyncMock(return_value=client);client.__aexit__=AsyncMock(return_value=False)
        invoke=AsyncMock(return_value={'tool':'refund_payment','arguments':{'payment_id':'pay_A','amount_paise':40000},'result':{'status':'upstream_error','reason':'Outcome unknown'}})
        with patch.object(web,'AsyncOpenAI',return_value=client),patch.object(web,'invoke',invoke),patch.object(web,'config',return_value={'OPENAI_API_KEY':'test','OPENAI_MODEL':'test'}):
            response=self.post('agent',{'request_id':'request-1234567890','mode':'protected','message':'Refund 400 rupees.'})
        self.assertEqual(response.status_code,200);self.assertEqual(invoke.await_count,1)
        with core.db() as c:self.assertEqual(c.execute('SELECT status FROM runs').fetchone()['status'],'needs_review')
    def test_cross_origin_mutation_denied(self):
        res=self.client.post('/api/approve',json={'payment_id':'pay_A','amount_paise':10000},headers={'X-Demo-Token':web.LOCAL_TOKEN,'Origin':'https://malicious.example'})
        self.assertEqual(res.status_code,403)
    def test_new_approval_replaces_previous(self):
        a=self.post('approve',{'payment_id':'pay_A','amount_paise':100000});b=self.post('approve',{'payment_id':'pay_A','amount_paise':99900})
        self.assertEqual(b.status_code,200)
        with core.db() as c:
            self.assertEqual(c.execute('SELECT used FROM approvals WHERE id=?',(a.json()['approval_id'],)).fetchone()['used'],1)
            self.assertEqual(c.execute('SELECT count(*) FROM approvals WHERE used=0').fetchone()[0],1)
    def test_boolean_approval_amount_rejected(self):
        self.assertEqual(self.post('approve',{'payment_id':'pay_A','amount_paise':True}).status_code,400)
    def test_baseline_cannot_target_ticket(self):
        res=self.post('replay',{'request_id':'request-1234567890','mode':'unprotected','tool':'refund_payment','arguments':{'payment_id':'pay_A','amount_paise':100000}})
        self.assertEqual(res.status_code,400);self.assertIn('isolated baseline',res.json()['error'])
    def test_invalid_payment_path_rejected(self):
        with self.assertRaises(ValueError):core.validate_payment('pay_A/../orders')
    def test_missing_session_rejected(self):
        self.assertEqual(self.client.post('/api/approve',json={}).status_code,403)
    def test_state_contains_no_credentials(self):
        state=self.client.get('/api/state').json()
        self.assertNotIn('OPENAI_API_KEY',state);self.assertNotIn('RAZORPAY_KEY_SECRET',state)
        self.assertIn('approvals',state);self.assertIn('runs',state)
if __name__=='__main__':unittest.main()
