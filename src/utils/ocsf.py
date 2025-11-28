import socket
import time


def wrap_ocsf_6003(action, actor, outcome, message, data):
    """
    Wraps event in OCSF Class 6003 (API Activity) Schema.
    """
    return {
        "class_uid": 6003,
        "class_name": "API Activity",
        "category_uid": 6,
        "activity_id": 1,  # Create/Invoke
        "time": int(time.time() * 1000),
        "metadata": {
            "product": {
                "name": "KT-Sovereign",
                "vendor_name": "Primordial",
                "version": "53.6.0",
            },
            "profiles": ["security_control"],
        },
        "actor": {"user": {"name": actor, "type": "Service Account"}},
        "api": {"operation": action, "service": {"name": "DecisionBroker"}},
        "dst_endpoint": {"hostname": socket.gethostname()},
        "status_id": 1 if outcome == "SUCCESS" else 2,
        "status": outcome,
        "message": message,
        "unmapped": data,
    }
