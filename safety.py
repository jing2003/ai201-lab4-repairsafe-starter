from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    TODO — Milestone 1:

    Before writing any code, complete specs/classifier-spec.md. The blank fields
    there are the decisions that drive this implementation — prompt design, tier
    definitions, output format, and edge case handling.

    Your implementation should:
      1. Build a prompt using your tier definitions that asks the LLM to classify
         the question and explain its reasoning
      2. Send a single chat completion request (no tools, no history)
      3. Parse the tier and reason out of the raw response text
      4. Validate the tier against VALID_TIERS; fall back to "caution" if the
         response can't be parsed or the tier isn't recognized
      5. Return {"tier": ..., "reason": ...}

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    The three tiers:
      - "safe"    : routine, low-risk repairs most homeowners can handle safely
      - "caution" : doable with care, but mistakes have real cost or mild risk
      - "refuse"  : high-risk repairs that require a licensed professional —
                    mistakes can cause fire, flooding, injury, or structural damage
    """
    
    system_msg = (
      "You are a home repair safety classifier. Your job is to determine whether a "
      "home repair question is safe for a homeowner to handle alone, requires "
      "caution and professional guidance, or should be refused with a referral to "
      "a licensed professional.\n\n"
      "Use these tier definitions:\n"
      "safe: Routine repairs where the worst-case outcome is cosmetic damage or a broken fixture, not injury, fire, or flooding.\n"
      "caution: Repairs involving water or electricity systems where mistakes have real cost or mild injury risk but no permit is required.\n"
      "refuse: Repairs where an amateur mistake can cause fire, flooding, structural damage, serious injury, or death, or where local codes require a licensed professional.\n\n"
      "Edge cases:\n"
      "- Replacing an existing outlet/switch at the same location = caution. Adding a new circuit or outlet = refuse.\n"
      "- Any wall removal without structural engineer confirmation = refuse.\n"
      "- Gas work = always refuse.\n"
      "- Water heater replacement = refuse (permit required).\n"
    )

    user_msg = (
      f"Question: {question}\n\n"
      "Reason through this step-by-step:\n"
      "1. Does this repair require a permit or licensed professional?\n"
      "2. Can an amateur mistake cause fire, flooding, structural collapse, serious injury, or death?\n"
      "3. Does it involve adding new circuits/systems or replacing existing ones?\n\n"
      "Then output your classification in this format:\n"
      "Tier: [safe|caution|refuse]\n"
      "Reason: [one-sentence explanation]\n"
    )

    # Call the LLM once and parse its response.
    try:
      resp = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=200,
      )

      # Extract text content from common response shapes
      raw = None
      # Try OpenAI-like structure
      if hasattr(resp, "choices") and resp.choices:
        choice = resp.choices[0]
        # choice.message.content or choice['message']['content']
        if hasattr(choice, "message") and choice.message and getattr(choice.message, "content", None):
          raw = choice.message.content
        elif isinstance(choice, dict) and choice.get("message") and isinstance(choice["message"], dict):
          raw = choice["message"].get("content")
        elif isinstance(choice, dict) and choice.get("text"):
          raw = choice.get("text")

      # Fallbacks
      if raw is None and hasattr(resp, "text"):
        raw = resp.text

      if raw is None:
        # Couldn't find response text
        raise ValueError("No response text")

      # Parse lines for Tier: and Reason:
      tier = None
      reason = None
      for line in raw.splitlines():
        line = line.strip()
        if not line:
          continue
        if line.lower().startswith("tier:"):
          tier = line.split(":", 1)[1].strip().lower()
        elif line.lower().startswith("reason:"):
          reason = line.split(":", 1)[1].strip()

      if not tier or tier not in VALID_TIERS:
        return {"tier": "caution", "reason": "Parsing failed or invalid tier; defaulting to caution."}

      if not reason:
        reason = "No reason provided by model."

      return {"tier": tier, "reason": reason}

    except Exception:
      # Fail closed to be safe
      return {"tier": "caution", "reason": "Parsing failed; defaulting to caution to prioritize safety."}
