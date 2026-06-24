import json
import os
from datetime import datetime
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log.

    TODO — Milestone 3:

    Before writing any code, complete specs/auditor-spec.md. The key decisions
    are what fields to log, how much of the question and response to include,
    and how to handle the logs/ directory not existing yet.

    Each record should be a JSON object written as a single line to LOG_FILE
    (defined in config.py as "logs/audit.jsonl").

    Required fields:
      - "timestamp"        : ISO 8601 datetime string
      - "tier"             : the safety tier assigned to this question
      - "question"         : the user's question (truncate to 300 chars if longer)
      - "response_preview" : first 200 characters of the response

    If the logs/ directory doesn't exist, create it before writing.

    Also print a one-line summary to the terminal so you can see logged
    interactions in real time without opening the file:
      e.g. [LOGGED] tier=caution | "How do I replace a faucet?" → 47 chars

    Design your log entry in specs/auditor-spec.md before implementing here.
    """
    # Ensure logs directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
      try:
        os.makedirs(log_dir, exist_ok=True)
      except Exception:
        # Best-effort: if we can't create directory, skip logging to file but still print
        print(f"[LOG ERROR] could not create log directory: {log_dir}")

    # Prepare record fields
    timestamp = datetime.utcnow().isoformat() + "Z"
    truncated_question = (question[:300]) if question is not None else ""
    response_preview = (response[:200]) if response is not None else ""

    record = {
      "timestamp": timestamp,
      "tier": tier,
      "question": truncated_question,
      "response_preview": response_preview,
    }

    # Append JSON line to log file
    try:
      with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
      print(f"[LOG ERROR] could not write to log file: {LOG_FILE}")

    # Print one-line summary to terminal
    try:
      resp_len = len(response) if response is not None else 0
      display_q = truncated_question.replace('\n', ' ')[:80]
      print(f"[LOGGED] tier={tier} | \"{display_q}\" → {resp_len} chars")
    except Exception:
      # Silently ignore printing errors
      pass
