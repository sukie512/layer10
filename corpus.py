"""
Synthetic corpus modeled after Enron-style email threads.
In a real run you would download the Enron dataset from:
  https://www.cs.cmu.edu/~./enron/  (CMU mirror)
  or Kaggle: https://www.kaggle.com/datasets/wcukierski/enron-email-dataset

We ship a curated synthetic sample so the project is fully self-contained
and reproducible without a large download.  The synthetic emails cover:
  - Identity aliases (same person, different From: addresses)
  - Thread quoting (duplicate content)
  - Decisions that get reversed
  - Ownership changes
  - Redacted / deleted messages (tombstones)
"""

EMAILS = [
    {
        "id": "msg-001",
        "message_id": "<001@enron.com>",
        "thread_id": "thread-alpha",
        "timestamp": "2001-09-05T09:12:00Z",
        "from": "kenneth.lay@enron.com",
        "to": ["jeffrey.skilling@enron.com", "andrew.fastow@enron.com"],
        "cc": [],
        "subject": "Q3 Revenue Targets",
        "body": (
            "Jeff, Andy,\n\n"
            "We need to hit $45B in revenue for Q3. I've spoken with the board and they "
            "are fully behind us. Andy, please make sure the SPE structures support this. "
            "Jeff will be taking over as CFO effective October 1st.\n\n"
            "Ken"
        ),
        "redacted": False,
    },
    {
        "id": "msg-002",
        "message_id": "<002@enron.com>",
        "thread_id": "thread-alpha",
        "timestamp": "2001-09-05T11:30:00Z",
        "from": "j.skilling@enron.com",   # alias – same person as jeffrey.skilling@enron.com
        "to": ["kenneth.lay@enron.com"],
        "cc": ["andrew.fastow@enron.com"],
        "subject": "RE: Q3 Revenue Targets",
        "body": (
            "Ken,\n\n"
            "Understood on the $45B target. However I want to flag that the broadband "
            "segment is tracking $2B below plan. We may need to restate.\n\n"
            "On the CFO role – I think Andy should remain CFO; I'd rather stay as CEO. "
            "Can we revisit?\n\n"
            "Jeff\n\n"
            "-----Original Message-----\n"
            "From: kenneth.lay@enron.com\n"
            "Sent: 2001-09-05 09:12\n"
            "To: jeffrey.skilling@enron.com; andrew.fastow@enron.com\n"
            "Subject: Q3 Revenue Targets\n\n"
            "Jeff, Andy,\n\n"
            "We need to hit $45B in revenue for Q3 ..."
        ),
        "redacted": False,
    },
    {
        "id": "msg-003",
        "message_id": "<003@enron.com>",
        "thread_id": "thread-alpha",
        "timestamp": "2001-09-06T08:00:00Z",
        "from": "kenneth.lay@enron.com",
        "to": ["j.skilling@enron.com", "andrew.fastow@enron.com"],
        "cc": [],
        "subject": "RE: RE: Q3 Revenue Targets",
        "body": (
            "Jeff – agreed. Andy stays as CFO. You remain CEO. My earlier note was wrong.\n\n"
            "Ken"
        ),
        "redacted": False,
    },
    {
        "id": "msg-004",
        "message_id": "<004@enron.com>",
        "thread_id": "thread-beta",
        "timestamp": "2001-10-12T14:22:00Z",
        "from": "andrew.fastow@enron.com",
        "to": ["sherron.watkins@enron.com"],
        "cc": [],
        "subject": "LJM Cayman – Accounting Treatment",
        "body": (
            "Sherron,\n\n"
            "The LJM Cayman partnership will be consolidated off-balance-sheet. "
            "Legal has signed off. The structure allows us to move $1.2B of debt "
            "off the books before year-end.\n\n"
            "Please keep this between us for now.\n\n"
            "Andy"
        ),
        "redacted": False,
    },
    {
        "id": "msg-005",
        "message_id": "<005@enron.com>",
        "thread_id": "thread-beta",
        "timestamp": "2001-10-15T09:05:00Z",
        "from": "sherron.watkins@enron.com",
        "to": ["kenneth.lay@enron.com"],
        "cc": [],
        "subject": "Concerns about accounting",
        "body": (
            "Ken,\n\n"
            "I am incredibly nervous that we will implode in a wave of accounting "
            "scandals. The LJM partnerships and Raptor vehicles look problematic. "
            "I strongly urge you to investigate the off-balance-sheet structures "
            "before it is too late.\n\n"
            "Sherron Watkins\n"
            "VP Accounting"
        ),
        "redacted": False,
    },
    {
        "id": "msg-006",
        "message_id": "<006@enron.com>",
        "thread_id": "thread-gamma",
        "timestamp": "2001-11-01T10:00:00Z",
        "from": "kenneth.lay@enron.com",
        "to": ["all.employees@enron.com"],
        "cc": [],
        "subject": "Company Update",
        "body": (
            "Team,\n\n"
            "Enron remains in strong financial shape. Our stock is undervalued and "
            "I am buying more shares personally. The Q3 revenue came in at $44.8B, "
            "just below our $45B target but within acceptable range.\n\n"
            "Ken Lay\nChairman & CEO"
        ),
        "redacted": False,
    },
    {
        "id": "msg-007",
        "message_id": "<007@enron.com>",
        "thread_id": "thread-gamma",
        "timestamp": "2001-11-08T16:45:00Z",
        "from": "andrew.fastow@enron.com",
        "to": ["kenneth.lay@enron.com"],
        "cc": [],
        "subject": "Restatement – URGENT",
        "body": (
            "Ken,\n\n"
            "We are being forced to restate earnings going back to 1997. "
            "The SEC has opened a formal investigation. LJM structures will not "
            "survive scrutiny. We need to disclose the $1.2B debt immediately.\n\n"
            "Andy"
        ),
        "redacted": False,
    },
    # Duplicate / near-duplicate of msg-004 (forwarded to a second recipient)
    {
        "id": "msg-008",
        "message_id": "<008@enron.com>",
        "thread_id": "thread-beta",
        "timestamp": "2001-10-12T14:55:00Z",
        "from": "andrew.fastow@enron.com",
        "to": ["richard.causey@enron.com"],
        "cc": [],
        "subject": "FWD: LJM Cayman – Accounting Treatment",
        "body": (
            "Richard – FYI, forwarding.\n\n"
            "---------- Forwarded message ----------\n"
            "From: andrew.fastow@enron.com\n"
            "To: sherron.watkins@enron.com\n"
            "Date: 2001-10-12\n"
            "Subject: LJM Cayman – Accounting Treatment\n\n"
            "Sherron,\n\n"
            "The LJM Cayman partnership will be consolidated off-balance-sheet. "
            "Legal has signed off. The structure allows us to move $1.2B of debt "
            "off the books before year-end.\n\n"
            "Please keep this between us for now.\n\n"
            "Andy"
        ),
        "redacted": False,
    },
    # Redacted message (tombstone)
    {
        "id": "msg-009",
        "message_id": "<009@enron.com>",
        "thread_id": "thread-delta",
        "timestamp": "2001-12-01T08:00:00Z",
        "from": "legal@enron.com",
        "to": ["andrew.fastow@enron.com"],
        "cc": [],
        "subject": "[REDACTED BY LEGAL HOLD]",
        "body": "[This message has been redacted under legal hold order LH-2001-044]",
        "redacted": True,
    },
    {
        "id": "msg-010",
        "message_id": "<010@enron.com>",
        "thread_id": "thread-epsilon",
        "timestamp": "2001-08-14T07:30:00Z",
        "from": "jeffrey.skilling@enron.com",
        "to": ["kenneth.lay@enron.com"],
        "cc": [],
        "subject": "My Resignation",
        "body": (
            "Ken,\n\n"
            "For personal reasons I am resigning as CEO effective immediately. "
            "I recommend you resume the CEO title. This has nothing to do with "
            "the company's financial condition.\n\n"
            "Jeff Skilling"
        ),
        "redacted": False,
    },
]
