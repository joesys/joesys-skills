# Confidence Tiers

The record of a project is old, partial, and sometimes wrong. An answer that
sounds sure on weak evidence misleads the reader. So every claim in a `why`
answer sits in exactly one of five tiers. The tier decides where the claim
goes in the answer and which words it may use.

## Stated

An author wrote the reason down, and you can cite the text. Examples: a
commit message that says "clamp to 100 because the upstream service rejects
larger values", a pull request that names the bug it fixes, a code comment
that gives the cause, a spec that says "we chose A over B because".

Wording: plain and cited. "This exists because X (commit `abc1234`)."

## Supported

No single source states the reason, but several separate items point to the
same one. Example: the commit subject says "improve performance", every test
added with it uses a very large input, and the next three commits touch the
same hot path.

Wording: sure, but shown as derived. "The evidence points to X:" followed by
each item and what it adds.

## Inferred

A reasonable reading that nothing in the record supports directly. It is
your reading, not a fact from the record. Example: the commit gives no
reason, but it was made the same day as a commit titled "revert", so it was
likely a quick repair.

Wording: hedged, with the steps shown. "Given A and B, C seems likely."

## Guess

A possible explanation on thin evidence, where other explanations fit as
well. It is worth showing, because the reader may know which one is right.
Mark it as a guess.

Wording: "One possibility is X, but nothing in the record confirms it."
A guess goes under Other explanations, next to the alternatives.

## Unknown

You searched and did not find the reason. This is a valid result. Say
exactly what you searched: "The 6 commits that touch this function give no
reason. `git log -S 'MAX_RETRIES'` finds one commit, with the message
'tune'. No file under `docs/` names the constant."

## Words

**Words that claim a fact** need a citation right next to them: "because",
"the reason is", "was designed to", "fixes", "the team decided". Never use
them for an Inferred claim or a Guess.

**Words that hedge** mark your own reading: "appears to", "likely",
"suggests", "is consistent with", "may have been".

**Words to avoid:** "obviously", "clearly", "of course", and "just" as in
"it is just for speed". They hide doubt. Avoid "I think" too: say what the
evidence suggests.

## Traps

- **Do not tidy the history.** Code that makes sense today may have been
  written for a reason that no longer holds, or for a wrong reason. Do not
  assume that the author did the right thing and then work backward.
- **A pattern is not a decision.** The same shape in five files can be five
  copies of one paste.
- **Silence is not proof.** "No one mentioned security" does not show that
  security was not a concern.
- **Mechanics are not motive.** A diff that changes `limit = 50` to
  `limit = 100` shows the change. The reason is in the words around it, or
  it is missing.
