"""Simple append-only ledger scaffold."""
import hashlib
import json
from typing import List, Dict, Any


class ObjectLedger:
    def __init__(self):
        self.txns: List[Dict[str, Any]] = []

    def append(self, action: Dict[str, Any]) -> str:
        payload = json.dumps(action, sort_keys=True).encode("utf-8")
        h = hashlib.sha256(payload).hexdigest()
        tx = {"hash": h, "action": action}
        self.txns.append(tx)
        return h

    def history(self) -> List[Dict[str, Any]]:
        return self.txns
