# Design Package

The package is what `/architect` hands over. Keep it to about one page of
text plus the sketch. Use these nine sections, in this order. Leave none
out. When a section has nothing to say, write one line that says so.

## Problem

One paragraph. What the new code must do, and what makes the shape hard to
see. Name the constraints that the design must respect: the types it must
work with, the callers that must not break, the rules that cross the
boundary.

## Usage (caller's view)

Write this first. Show the short usage text, and two or three real call
sites: what the caller imports, what it calls, and what comes back. The
types in the next section come from this usage. When the two disagree,
change the types.

## Shape

The design. Give the data structures first, as a type sketch in the language
of the project, with `not implemented` bodies. Then say how the data moves
through the signatures, and give the module map. State which rules the
types enforce, where outside data is checked, and what the code
deliberately does not do. Say what the public interface hides and what it
still shows.

## How the candidates were merged

Which candidate became the base, and why. What was taken from each other
candidate. What was rejected, and why. Say which model produced each
candidate, and which candidates failed or were left out. When the candidates
agreed on one shape, say so, and say whether they came from one model family
or from several.

## Trade-offs accepted

One line for each trade-off, in the form "we accept X to get Y". Name
anything that a later reader could take for a mistake.

## Alternatives considered

At least one other whole shape, with one line on why it lost. Not a variant
of the chosen shape. When the constraints left only one shape, say why.

## Open questions and risks

What a person must decide before building starts. Write each one as a
question, so that the answer settles it.

## First step to build

One sentence: the first thing to write when building is approved. This
package does not start it.

## When to throw this design away

A design can be wrong. One awkward case does not show that. A pattern does.
Stop building and come back to `/architect` when you see one of these:

- The same kind of workaround appears in places that have nothing to do
  with each other.
- Several separate edge cases each need a special branch.
- The types need an escape hatch to compile, such as a cast, or an optional
  field that is always set.
- Someone reaches for a lock, although the design said that the state is not
  shared.
- A caller must know the inner rules of a module to use it.

Then design again as if the new constraint had been known from the start.
Make the new sketch smaller than the old one before it grows.
