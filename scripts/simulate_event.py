#!/usr/bin/env python3
"""Fire a simulated GitHub issue webhook at a running Sentinel server.

    python scripts/simulate_event.py            # hits http://localhost:8000
    SENTINEL_URL=http://host:8000 python scripts/simulate_event.py

This mirrors exactly what GitHub would POST when an issue is labelled, so the
"webhook" path is exercised end-to-end even without a public tunnel.
"""
from __future__ import annotations

import os
import sys

import httpx

URL = os.environ.get("SENTINEL_URL", "http://localhost:8000")
TRIGGER_LABEL = os.environ.get("TRIGGER_LABEL", "devin-fix")

payload = {
    "action": "labeled",
    "issue": {
        "number": int(os.environ.get("ISSUE_NUMBER", "424")),
        "title": "Upgrade vulnerable `cryptography` dependency",
        "body": "Dependency scanner flagged a critical advisory in the pinned "
                "`cryptography` version. Upgrade to the patched release and "
                "verify the Fernet/x509 code paths.",
        "labels": [
            {"name": TRIGGER_LABEL},
            {"name": "severity:critical"},
            {"name": "category:vulnerability"},
        ],
    },
}

resp = httpx.post(
    f"{URL}/webhooks/github",
    json=payload,
    headers={"X-GitHub-Event": "issues"},
    timeout=30,
)
print(resp.status_code, resp.text)
sys.exit(0 if resp.is_success else 1)
