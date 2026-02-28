"""Mock ERP API client for simulated posting."""

import random
import uuid
from datetime import datetime

from app.config import ERP_SUCCESS_RATE


def post_to_erp(
    transaction_id: int,
    gl_code: str,
    amount: float,
    description: str = "",
) -> dict:
    """
    Simulate posting a transaction to an ERP system.

    Returns a mock response mimicking real ERP APIs like SAP or Oracle.
    """
    # Simulate network latency + processing
    erp_ref = f"ERP-{uuid.uuid4().hex[:8].upper()}"

    if random.random() < ERP_SUCCESS_RATE:
        return {
            "success": True,
            "erp_response_code": "200",
            "erp_response_message": f"Posted successfully. ERP Reference: {erp_ref}",
            "erp_reference": erp_ref,
            "posted_at": datetime.utcnow().isoformat(),
            "journal_entry": {
                "debit_account": gl_code,
                "credit_account": "1100",  # Cash & Bank (default offset)
                "amount": amount,
                "memo": description[:100] if description else "",
            },
        }
    else:
        return {
            "success": False,
            "erp_response_code": "500",
            "erp_response_message": "ERP posting failed: Temporary service unavailability. Retry recommended.",
            "erp_reference": None,
            "posted_at": None,
        }
