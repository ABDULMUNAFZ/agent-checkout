import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
import core

class ExactApprovalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=patch.object(core,'ROOT',Path(self.temp.name));self.root.start()
        self.external=AsyncMock(return_value={'id':'rfnd_TEST','status':'processed'})
        self.refund=patch.object(core,'refund_payment',self.external);self.refund.start()
    async def asyncTearDown(self):
        self.refund.stop();self.root.stop();self.temp.cleanup()
    def approve(self,expires=None):
        with core.db() as c:c.execute('INSERT INTO approvals(id,digest,expires) VALUES(?,?,?)',('approval-test',core.digest('pay_A',100000),expires or time.time()+300))
    async def test_changed_payment_or_amount_does_not_execute(self):
        self.approve()
        for payment,amount in [('pay_B',100000),('pay_A',99900)]:
            self.assertEqual((await core.approved_refund_payment(payment,amount))['status'],'review_required')
        self.external.assert_not_awaited()
    async def test_concurrent_reuse_executes_once(self):
        self.approve()
        results=await asyncio.gather(core.approved_refund_payment('pay_A',100000),core.approved_refund_payment('pay_A',100000))
        self.assertEqual(self.external.await_count,1)
        self.assertEqual(sum(r.get('status')=='review_required' for r in results),1)
    async def test_expired_approval_does_not_execute(self):
        self.approve(time.time()-10)
        self.assertEqual((await core.approved_refund_payment('pay_A',100000))['status'],'review_required')
        self.external.assert_not_awaited()
    async def test_uncertain_external_failure_does_not_allow_reuse(self):
        self.approve();self.external.side_effect=TimeoutError('uncertain outcome')
        with self.assertRaises(TimeoutError):await core.approved_refund_payment('pay_A',100000)
        self.assertEqual((await core.approved_refund_payment('pay_A',100000))['status'],'review_required')
        self.assertEqual(self.external.await_count,1)
if __name__=='__main__':unittest.main()
