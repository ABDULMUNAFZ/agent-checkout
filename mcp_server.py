import os
from fastmcp import FastMCP
from core import get_payment, refund_payment, approved_refund_payment
mcp=FastMCP('Agent Checkout · Razorpay TEST')
for tool in (get_payment,refund_payment,approved_refund_payment):
    mcp.tool(tool)
if __name__=='__main__':
    mcp.run(transport='http',host=os.getenv('BIND_HOST','127.0.0.1'),port=8091)
