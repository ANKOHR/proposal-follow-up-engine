"""Pure validation and monitoring. Amounts are input face values, not revenue."""
from datetime import date

class SchemaError(ValueError):
    """An explicit input field violates the schema."""

def fail(field, reason):
    raise SchemaError(f"field {field}: {reason}")

def exact(obj, fields, field):
    if not isinstance(obj, dict):
        fail(field, "expected object")
    missing, extra = set(fields) - obj.keys(), obj.keys() - set(fields)
    if missing or extra:
        fail(field, f"missing {sorted(missing)}, unknown {sorted(extra)}")

def day(value, field):
    if not isinstance(value, str):
        fail(field, "expected ISO date YYYY-MM-DD")
    try:
        result = date.fromisoformat(value)
    except ValueError:
        fail(field, "expected ISO date YYYY-MM-DD")
    if result.isoformat() != value:
        fail(field, "expected ISO date YYYY-MM-DD")
    return result

def string(value, field, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        fail(field, f"expected nonempty text up to {limit} characters")
    if chr(0x2014) in value or any(ord(c) < 32 for c in value):
        fail(field, "control characters and em dash are unsupported")

def validate(data):
    exact(data, {"schema_version", "synthetic", "entered_by", "as_of", "currency", "proposals"}, "document")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        fail("schema_version", "expected 1")
    if type(data["synthetic"]) is not bool:
        fail("synthetic", "expected boolean")
    string(data["entered_by"], "entered_by", 200)
    today = day(data["as_of"], "as_of")
    if data["currency"] not in ("GBP", "USD", "EUR"):
        fail("currency", "supported currencies: GBP, USD, EUR")
    if not isinstance(data["proposals"], list):
        fail("proposals", "expected array")
    seen = set()
    for i, p in enumerate(data["proposals"]):
        prefix = f"proposals[{i}]"
        exact(p, {"id", "client", "amount_minor", "status", "sent_on", "follow_up_on"}, prefix)
        for key, limit in (("id", 200), ("client", 10000)):
            string(p[key], f"{prefix}.{key}", limit)
        if p["id"] in seen:
            fail(f"{prefix}.id", "duplicate id")
        seen.add(p["id"])
        if type(p["amount_minor"]) is not int or not 0 <= p["amount_minor"] <= 10**12:
            fail(f"{prefix}.amount_minor", "expected integer between 0 and 1000000000000")
        if p["status"] not in ("sent", "accepted", "declined", "withdrawn"):
            fail(f"{prefix}.status", "expected sent, accepted, declined, withdrawn")
        sent = day(p["sent_on"], f"{prefix}.sent_on")
        due = day(p["follow_up_on"], f"{prefix}.follow_up_on")
        if sent > today:
            fail(f"{prefix}.sent_on", "future sent date relative to as_of")
        if due < sent:
            fail(f"{prefix}.follow_up_on", "must be on or after sent_on")
    return data

def monitor(data, sources):
    """Compute outstanding and actionable sets from the supplied snapshot date."""
    validate(data)
    proposals = sorted(data["proposals"], key=lambda p: p["id"])
    outstanding = [p for p in proposals if p["status"] == "sent"]
    overdue = [p for p in outstanding if p["follow_up_on"] < data["as_of"]]
    due_today = [p for p in outstanding if p["follow_up_on"] == data["as_of"]]
    upcoming = [p for p in outstanding if p["follow_up_on"] > data["as_of"]]
    groups = {"outstanding": outstanding, "overdue": overdue, "due_today": due_today, "upcoming": upcoming}
    return {"schema_version": 1, "as_of": data["as_of"], "currency": data["currency"],
            "provenance": sorted(sources, key=lambda s: s["file"]),
            "metrics": {"total_count": len(proposals), "closed_count": len(proposals)-len(outstanding),
                        **{f"{k}_count": len(v) for k,v in groups.items()},
                        **{f"{k}_amount_minor": sum(p["amount_minor"] for p in v) for k,v in groups.items()}},
            "ids": {k: [p["id"] for p in v] for k,v in groups.items()},
            "proposals": proposals,
            "honesty": "Amounts are supplied proposal face values, not earned revenue. Time and money saved are unmeasured and are not reported. No predictions."}
