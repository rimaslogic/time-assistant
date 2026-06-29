# Weekly Planning — Socratic Prompt

Used when Rimas asks to "plan my week" or "plan next week" through the time-assistant skill.

This is NOT a calendar auto-generator. It's a guided reflection that produces a plan Rimas commits to, not one that Claude dictates.

## Flow (strict)

### Step 1 — Anchor the week

Ask ONE question:
> "Before we block anything, what are the 2–3 outcomes this week will be judged on? Not tasks — outcomes. 'Acme architecture reviewed and signed off' counts; 'work on Acme' doesn't."

Wait for the answer. If Rimas lists 5+ outcomes, push back: "That's a month of outcomes in a week. Pick 2–3 that are non-negotiable; the rest are stretch."

### Step 2 — Protect HVT blocks

Ask:
> "For each outcome, what's the minimum deep-work time it needs? Not 'how long will it take' — what's the minimum block size below which the work doesn't happen? 90 minutes? 3 hours?"

Then:
> "How many of those blocks can you realistically protect this week?"

### Step 3 — Box the LVT

Ask:
> "Email, support, admin — when do they live next week? Specific windows, not 'as needed'. E.g., 'email Mon/Wed/Fri 15:00–16:00'."

If Rimas resists ("I have to be responsive"):
> "Responsive to whom, for what? If it's a specific client in a specific window, block that client window and protect the rest."

### Step 4 — Meeting triage

Pull next week's calendar (via Google Calendar MCP). For each event:
- Tag projected HVT/LVT
- Flag candidates for decline/defer/shorten

Ask:
> "Here are the LVT meetings already on the calendar. Which ones can move to next week, be cut to 15 min, or be replaced with async?"

### Step 5 — Propose structure

Only now, propose blocks. Format:

```
Week of {dates}

HVT BLOCKS (target: {N}h)
  Mon 09:00–12:00 — {outcome 1, specific deliverable}
  Tue 09:00–11:30 — {outcome 2}
  Wed 09:00–12:00 — {outcome 1 continued}
  Thu 14:00–17:00 — {outcome 3}
  Fri 09:00–12:00 — {outcome buffer / content}

LVT WINDOWS (cap: {M}h, ~20% of tracked)
  Mon/Wed/Fri 15:00–16:00 — email
  Tue/Thu 14:00–15:00 — support batch
  Fri 16:00+  — weekly review + admin

PROTECTED  (do not book)
  Mon–Fri 09:00–12:00

PROJECTED HVT: {pct}%
```

### Step 6 — Commit

Ask:
> "Want me to push these blocks to your calendar, or are you adjusting first?"

If yes, use the Google Calendar MCP to create the events. Use title prefix `[HVT] ` or `[LVT] ` so routines can classify them instantly.

### Step 7 — One risk call-out

End with:
> "One thing to watch: {specific risk based on the plan — e.g., 'Your three-hour blocks all fall before lunch. If morning meetings creep in, the whole plan collapses. The single highest-leverage decline this week is {specific meeting}.'}"

---

## Things to never do in planning

- Don't propose structure before Step 5. Planning without outcomes first produces pretty calendars and no results.
- Don't average — "you usually do 2h of content" is a floor, not a target.
- Don't fill empty time. Empty time is a feature. If Friday afternoon is open, leave it open.
- Don't add buffer time between every block. Trust Rimas's calibration.
- Don't suggest breaks, lunch blocks, or "focus rituals". Not the job.
