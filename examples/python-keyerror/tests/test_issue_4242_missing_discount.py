"""Reproduction for Sentry issue 4242: KeyError: 'discount' in create_order.

Input comes from the sanitized Sentry event (see ../fixture.json): the client
sends an order without a "discount" field.
Expected behavior: order is created with no discount applied.
This test FAILS before the fix with the same KeyError as in Sentry.
"""
import json
from pathlib import Path

from app.orders import create_order

FIXTURE = json.loads((Path(__file__).parent.parent / "fixture.json").read_text())


def test_issue_4242_order_without_discount_field():
    payload = FIXTURE["request"]["data"]  # {"items": [...], "customer_email": "[REDACTED]"}
    assert "discount" not in payload

    result = create_order(payload)

    assert result["total"] == 100
