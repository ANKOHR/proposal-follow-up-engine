"""Synthetic fixtures with independently enumerated planted ground truth. No randomness."""
AS_OF = "2026-09-30"

def dataset(count=200):
    proposals = []
    for i in range(count):
        category = i % 5
        proposals.append({"id": f"P{i+1:03d}", "client": f"Synthetic client {i+1}",
                          "amount_minor": 10000, "status": ["sent", "sent", "sent", "accepted", "declined"][category],
                          "sent_on": "2026-09-01", "follow_up_on": ["2026-09-29", AS_OF, "2026-10-01", "2026-09-29", "2026-09-29"][category]})
    return {"schema_version": 1, "synthetic": True, "entered_by": "fixture generator (synthetic)",
            "as_of": AS_OF, "currency": "GBP", "proposals": proposals}

def expectations():
    # Hand arithmetic: 40 blocks of 5; each block has 3 sent and 2 closed.
    return {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth", "arithmetic": "40 blocks x 5 records; each proposal is 10000 minor units",
            "metrics": {"total_count": 200, "closed_count": 80, "outstanding_count": 120,
                        "overdue_count": 40, "due_today_count": 40, "upcoming_count": 40,
                        "outstanding_amount_minor": 1200000, "overdue_amount_minor": 400000,
                        "due_today_amount_minor": 400000, "upcoming_amount_minor": 400000},
            "ids": {"outstanding": [f"P{i:03d}" for i in range(1,201) if (i-1)%5 < 3],
                    "overdue": [f"P{i:03d}" for i in range(1,201,5)],
                    "due_today": [f"P{i:03d}" for i in range(2,201,5)],
                    "upcoming": [f"P{i:03d}" for i in range(3,201,5)]}}
