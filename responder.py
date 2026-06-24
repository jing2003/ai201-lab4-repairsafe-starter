from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_safe_response(question: str, tier: str) -> str:
    """
    Generate a response to a home repair question, calibrated to its safety tier.

    TODO — Milestone 2:

    Before writing any code, complete specs/responder-spec.md. The most important
    fields are the three system prompts — one per tier. Write them out fully before
    generating any code; a vague description produces a vague prompt.

    `tier` is one of "safe", "caution", or "refuse" — returned by classify_safety_tier().

    Your implementation should use a different system prompt for each tier:
      - "safe"    : answer helpfully and directly; the user can proceed
      - "caution" : answer but include clear safety warnings and recommend
                    professional review for anything they're unsure about
      - "refuse"  : do NOT provide how-to instructions; explain why the repair
                    is dangerous and strongly recommend a licensed professional

    The refuse case is the hardest to get right. An LLM that says "you should hire
    a professional, but here's how to do it anyway" has defeated the entire purpose
    of the safety layer. Your system prompt needs to be explicit enough to prevent
    that — see specs/responder-spec.md for the design decision field on grounding.

    If tier is unrecognized (e.g., "unknown" from an unimplemented classifier),
    treat it as "caution" to fail safe rather than fail open.

    Return the response as a plain string.
    """
    # Normalize tier and fail-safe to 'caution'
    t = (tier or "").lower()
    if t not in ("safe", "caution", "refuse"):
      t = "caution"

    system_prompts = {
      "safe": (
        "You are an expert home repair assistant. The user asked a low-risk, routine repair question. "
        "Answer helpfully and directly with clear, concise, step-by-step instructions the homeowner can safely follow. "
        "Include a short tools/materials list, any quick safety checks to perform before starting, and a brief final verification step. "
        "Do not include professional referral language. Keep the tone practical and encouraging."
      ),
      "caution": (
        "You are an expert home repair assistant. The user asked a repair question that can be attempted by a careful homeowner but carries some risk. "
        "Provide clear guidance and limited step-by-step instructions where appropriate, but emphasize safety warnings, possible failure modes, and signs that the user should stop and consult a licensed professional. "
        "Start with a short summary of risks, list the safety gear and permit considerations, and whenever a step could cause electrical, plumbing, or structural harm, explicitly state: 'Stop and consult a professional'. "
        "Be helpful but conservative — prefer to recommend professional review for anything uncertain."
      ),
      "refuse": (
        "You are a safety-first assistant. The user asked about a repair that is too dangerous or requires a licensed professional. Do NOT provide any how-to or step-by-step repair instructions. "
        "Explain clearly and briefly why this task is unsafe for an amateur (risk of fire, flooding, structural collapse, or legal permit requirements). Recommend hiring a licensed professional and provide safe next steps the user can take that do not involve performing the repair (e.g., shut off power/water, take photos, gather appliance model numbers, questions to ask a contractor). "
        "Do NOT include repair procedures, wiring steps, or detailed mechanical instructions — refusal must not be circumvented."
      ),
    }

    system_msg = system_prompts[t]
    user_msg = f"Question: {question}\n\nRespond concisely."

    try:
      resp = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=600,
      )

      # Extract reply text
      reply = None
      if hasattr(resp, "choices") and resp.choices:
        choice = resp.choices[0]
        if hasattr(choice, "message") and getattr(choice.message, "content", None):
          reply = choice.message.content
        elif isinstance(choice, dict) and choice.get("message") and isinstance(choice["message"], dict):
          reply = choice["message"].get("content")
        elif isinstance(choice, dict) and choice.get("text"):
          reply = choice.get("text")

      if reply is None and hasattr(resp, "text"):
        reply = resp.text

      if reply is None:
        raise ValueError("No response text from model")

      return reply.strip()

    except Exception:
      # Conservative fallback
      if t == "refuse":
        return (
          "I can't provide instructions for this repair because it is potentially dangerous and likely requires a licensed professional. "
          "Consider shutting off power or water if it's safe to do so, take photos, and contact a licensed contractor for inspection."
        )
      return (
        "I couldn't generate a fully confident answer. Based on the safety tier, please consult a professional if you're unsure. "
        "If you'd like, I can try again or provide general safety precautions."
      )
