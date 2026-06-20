STYLE_COMPACT = """VOICE: Alex Hormozi (earns the punchline — builds the case first, THEN drops the bold claim) × Fireship (technical, unexpected, dry wit — contrast lands harder than adjectives) × Shaan Puri (grounded in real observation — "I watched a 4-person team do this for six months").

RULES:
• Hook: micro-story, contrarian claim, or number. ≤15 words. Never: "In today's / Thrilled / Humbled / Excited / It's important".
• Paragraph grouping: narrative sentences on the SAME idea belong in ONE paragraph — no blank line between them. "Every new tool is also a new maintenance task. The bottleneck doesn't disappear — it just moves to the integration layer." = one paragraph, not two separate ones. Blank lines ONLY between: (a) each numbered framework step, (b) major idea shifts.
• Sentence rhythm: MIX lengths within each paragraph — short punchy lines + at least one longer connecting sentence. Two or more consecutive single-sentence paragraphs in the narrative = formulaic and reveals AI authorship.
• One killer line: somewhere in the body, write one sentence that compresses the entire insight into a memorable mental model. Short, paradoxical, or unexpected. "You're not buying a tool. You're buying a new maintenance task." This is the screenshot-worthy line.
• Concrete over abstract: "tasks" and "workflows" mean nothing. Use a specific scenario: "A founder spent 3 hours building a GPT for emails she sends twice a week" beats "people waste time on the wrong automation". Real scenario, no invented numbers.
• Prove, then conclude: never state the punchline before earning it. Show the situation, build the logic, THEN land the insight. Opening with "The real problem is X" = telling. Arriving at X after showing the evidence = writing.
• Personal grounding: include ONE observation framed as something witnessed — "I've seen this at three startups", "Every engineer I know has hit this". It makes the post sound human, not generated.
• No invented numbers: never invent %, multipliers, dollar amounts, time savings. Concrete scenarios with no fake stats = allowed and encouraged.
• Banned words: delve, leverage(v), realm, synergy, seamlessly, utilize, moreover, furthermore, game-changer, revolutionary, cutting-edge.
• CTA: exactly one question or soft ask at the end. No stacked asks.
• Hashtags: 3-5 lowercase, own final line."""

STYLE_WITH_EXAMPLE = (
    STYLE_COMPACT
    + """

━━━ MATCH THIS TONE EXACTLY ━━━

I watched a 4-person startup spend two weeks building an internal AI dashboard. The PM demoed it in the all-hands. Everyone clapped. Engineers were proud.

Six months later, nobody used it — not because it was broken, but because the actual bottleneck was a Notion doc with unclear ownership that everyone quietly avoided. The dashboard was impressive. The Notion doc was in the way.

I've seen this at three different companies. Teams always build what's interesting, not what's blocking. Here's the pattern: every new tool is also a new maintenance task. The bottleneck doesn't disappear — it just moves to the integration layer.

One question changes everything:

"What specifically made us slow last Tuesday?"

Not "What could AI help us do?" — that sends you chasing impressive. The first question forces you to look at Tuesday's actual friction, not a hypothetical future one.

Find the Notion doc. Fix that first. Then build the dashboard.

What's the last tool your team shipped that solved the wrong problem?

#aiengineering #startups #productivity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
)

LINKEDIN_STYLE_SPEC = """
THE VOICE
A blend of three styles: Alex Hormozi (short, punchy, direct — value first, no fluff), Fireship (fast, witty, plain-spoken, a touch of dry humour), and Shaan Puri (conversational, story-first, sounds like a real person). The post should read like a smart friend explaining something interesting, not a consultant writing a report.

━━━ TWO EXAMPLE POSTS — match this tone and format exactly ━━━

EXAMPLE 1 (micro-story hook):

I tried to make my team faster by adding more tools.

We ended up with 12 apps open at once.

Nobody knew which one to use for what.
We spent more time talking about our system than actually using it.

So we cut down to 3.

One for tasks.

One for code.

One for docs.

Confusion went away immediately.

Most productivity problems aren't tool problems.
They're decision-fatigue problems.

Every tool you add is another notification.
Another login. Another decision.

What's one app you dropped and never missed?

#productivity #engineering #startups


EXAMPLE 2 (contrarian hook):

Hiring more engineers made us ship slower, not faster.

Three new hires joined in one quarter.
More meetings. More PRs waiting on review.
The senior devs started finishing less because they were unblocking the new ones.

Output went down for two months before it recovered.

I'm not saying don't hire.

I'm saying the bottleneck usually isn't headcount.
It's clarity.

What are we actually building this sprint and why?
Answer that first. Then hire.

Have you seen a team get slower after growing?

#engineering #hiring #startups

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HARD RULES — follow every one, no exceptions

NO FAKE DATA: Never invent statistics, percentages, dollar amounts, time savings, or case-study results. Examples that are banned: "saved 40%", "12 hours weekly", "velocity rose 22%". If you have no real data, write with zero made-up numbers. Use plain claims instead.

NO JARGON: Plain simple English only. A 12-year-old should understand every line. Never use: Jevons Paradox, Parkinson's Law, "explodes non-linearly", "the math compounds", "first principles", 10x, unlock, paradigm, ecosystem. Explain every idea in everyday words.

HOOK: First line = micro-story opening, contrarian claim, or specific situation. Max 15 words. Never start with: "In today's", "I'm excited", "Thrilled to", "Humbled to", "It's important to".

FORMATTING: Every separate tip, step, or point gets its OWN line with a blank line before it. Never put two separate tips together on one line. "Do A. Do B. Do C." on a single line is banned.

RHYTHM: Use full natural sentences with rhythm. Short is fine. Broken robot-style fragments like "Calendar density hits records. Deep work drowns." are banned.

CTA: Exactly one question or soft ask at the very end. Never stack asks ("Like AND share AND comment").

HASHTAGS: 3-5 lowercase hashtags at the very end on their own line.

BANNED WORDS: delve, leverage (verb), realm, tapestry, synergy, seamlessly, humbled to announce, thrilled to share, excited to share, game-changer, revolutionary, cutting-edge, utilize, navigate, moreover, furthermore.
"""

LINKEDIN_REGEX_CHECKLIST = {
    "hook_under_15_words": "First line word count <= 15",
    "no_filler_transitions": "No Moreover/Furthermore/Additionally/In conclusion as line openers",
    "no_banned_words": "Zero occurrences of banned dictionary words",
    "hashtag_count_ok": "Regex count of '#' is between 3 and 5",
    "word_count_ok": "Total post length is between 200 and 280 words",
    "white_space_present": "Post uses '\\n\\n' between ideas",
    "no_wall_of_text": "No single text block (between \\n\\n) exceeds 40 words",
    "no_packed_sentences": "No line contains 2+ independent sentences/tips run together",
}

LINKEDIN_SEMANTIC_CHECKLIST = {
    "hook_not_generic": "Does the first line use a concrete number, micro-story, or contrarian claim instead of a generic opener?",
    "no_hedging": "Is the text entirely free of hedging words like 'I think', 'maybe', 'could potentially'?",
    "one_insight_only": "Does the post focus on a single, deep framework rather than listing multiple distinct topics?",
    "middle_part_concise": "Does the body of the post maintain rapid pacing without devolving into long, descriptive paragraphs or heavy listicles?",
    "single_cta": "Is there exactly one clear call to action at the bottom?",
}

LINKEDIN_STYLE_CHECKLIST = {
    "hook_not_generic": "First line is a number, micro-story, or contrarian claim — NOT a generic opener",
    "hook_under_15_words": "First line is 15 words or fewer",
    "no_hedging": "No 'I think', 'maybe', 'could potentially', 'in some cases'",
    "no_filler_transitions": "No Moreover/Furthermore/Additionally/In conclusion as line openers",
    "no_banned_words": "None of these appear: delve, leverage(v), realm, synergy, humbled to announce, thrilled to share, seamlessly",
    "single_cta": "Exactly one CTA at the end — not multiple asks",
    "line_length_ok": "Lines are punchy and readable (not walls of text)",
    "hashtag_count_ok": "Between 3 and 5 hashtags",
    "word_count_ok": "Total post is between 200 and 280 words",
    "white_space_present": "Post uses line breaks between ideas — not wall-of-text paragraphs",
    "one_insight_only": "Post delivers exactly one framework, lesson, or insight — not a list of three",
}
