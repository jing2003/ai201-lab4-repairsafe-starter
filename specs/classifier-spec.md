# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter  | Type  | Description                     |
| ---------- | ----- | ------------------------------- |
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key        | Type  | Description                                        |
| ---------- | ----- | -------------------------------------------------- |
| `"tier"`   | `str` | One of: `"safe"`, `"caution"`, `"refuse"`          |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

_Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours._

---

### Tier definitions

_Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications._

**safe:**

```
Routine repairs where the worst-case outcome is cosmetic damage or a broken fixture, not injury, fire, or flooding.
```

**caution:**

```
Repairs involving water or electricity systems where mistakes have real cost or mild injury risk but no permit is required.
```

**refuse:**

```
Repairs where an amateur mistake can cause fire, flooding, structural damage, serious injury, or death, or where local codes require a licensed professional.
```

---

### Classification approach

_How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?_

_Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?_

```
Use few-shot learning with 2-3 examples per tier, plus edge case rules (e.g., "replacing vs. adding" for electrical, "new wall removal = always refuse"). Ask the LLM to reason step-by-step: does this require a permit? Can it cause fire/flooding/injury/death? Once it reasons through the key questions, output the tier. This handles boundary cases by anchoring decisions to concrete safety criteria rather than abstract tier names.
```

---

### Output format

_How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably._

_The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that._

```
Tier: [safe|caution|refuse]
Reason: [one-sentence explanation]

Parse by splitting on newline, then extracting the text after "Tier: " and "Reason: ". Use .strip() to handle leading/trailing whitespace.
```

---

### Prompt structure

_Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications._

**System message:**

```
You are a home repair safety classifier. Your job is to determine whether a home repair question is safe for a homeowner to handle alone, requires caution and professional guidance, or should be refused with a referral to a licensed professional.

Use these tier definitions:

safe: Routine repairs where the worst-case outcome is cosmetic damage or a broken fixture, not injury, fire, or flooding.
caution: Repairs involving water or electricity systems where mistakes have real cost or mild injury risk but no permit is required.
refuse: Repairs where an amateur mistake can cause fire, flooding, structural damage, serious injury, or death, or where local codes require a licensed professional.

Edge cases:
- Replacing an existing outlet/switch at the same location = caution. Adding a new circuit or outlet = refuse.
- Any wall removal without structural engineer confirmation = refuse.
- Gas work = always refuse.
- Water heater replacement = refuse (permit required).
```

**User message:**

```
Question: {question}

Reason through this step-by-step:
1. Does this repair require a permit or licensed professional?
2. Can an amateur mistake cause fire, flooding, structural collapse, serious injury, or death?
3. Does it involve adding new circuits/systems or replacing existing ones?

Then output your classification in this format:
Tier: [safe|caution|refuse]
Reason: [one-sentence explanation]
```

---

### Caution/refuse boundary

_The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why._

```
Rule: If an amateur mistake can cause fire, flooding, structural damage, serious injury/death, or if a permit/licensed professional is required, classify as refuse. Otherwise, if it involves water/electricity systems with real cost/mild injury risk, it's caution.

Example 1: "Can I replace the faucet in my bathroom?"
- Classification: caution
- Why: Replacing an existing fixture at the same location. Mistakes (cross-threading, water leak) have real costs but aren't life-threatening.

Example 2: "Can I add a new outlet in my garage?"
- Classification: refuse
- Why: Adding a new circuit requires opening the breaker panel and running wire—this is not permitted DIY work. An amateur error creating a fire hazard is the core danger.
```

---

### Fallback behavior

_What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?_

_Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?_

```
Fail closed: Return tier="caution" and reason="Parsing failed; defaulting to caution to prioritize safety."

Why: Returning "safe" when we can't parse the response risks giving dangerous advice. Returning "caution" forces human review and is the conservative choice. It's better to over-warn than under-warn in a safety-critical classifier.
```

---

## Implementation Notes

_Fill this in after implementing, before moving to Milestone 2._

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
none
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
none
```
