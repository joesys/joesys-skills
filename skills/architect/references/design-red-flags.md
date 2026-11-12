# Design Red Flags

Check every candidate against this list before you merge. A red flag is a
reason to change a shape or to reject it.

Assume that the next person to change this code is an agent. It sees only
the files that it opened. It copies the nearest example, and it takes the
shortest path that compiles. Prefer the design where a change that looks
right from one file is right for the whole project.

## Shallow module

The module has a large public interface and hides little. Judge depth by how
much behavior sits behind the interface, compared with the size of the
interface. A deep module is not a long chain of calls: a long chain spreads
the knowledge over many layers.

Signs:

- A caller must call several methods in order to finish one operation.
- The options expose the inner steps.
- Learning the interface does not save the caller from learning the inside.

## Information leakage

Several modules depend on one inner decision. A data layout, a policy, or a
detail of a protocol appears in more than one place, so a change needs edits
in all of them. Passing the types of the network or of storage through the
public interface is leakage too. Parse outside data into the project's own
types behind the interface.

## Split by time

The modules follow the order in which things run, and not the knowledge that
each one owns. Separate load, check, transform, and save stages often repeat
one data layout and its rules in four places. Group code by what it knows.
Steps that run at different times can belong to one module when they guard
the same decision.

## Pass-through method

A method passes the same arguments on to another method with the same shape.
It adds a layer and hides nothing. Remove it, or move the work into it. Keep
it only when it adds a policy, an adaptation, or a different level of
abstraction.

## Split ownership

More than one module writes the same state, or keeps its own copy. An agent
that edits one writer does not see the others, so their rules drift apart.
Give each piece of state one owner. The other modules read it, or ask the
owner to change it.

## Two ways to do one task

The design supports more than one way to do the same thing. An agent copies
the way that it finds first, so every way keeps getting new callers. Keep
one way. Move the callers off the others and delete them in the same change.

## Importable internals

A caller can import the inside of a module. An agent takes the shortest path
that compiles, so the inside becomes part of the interface. Make the inside
impossible to reach from outside, so that such an import fails the build.

## Hand-synced list

Two or more places list the same items, and a new item needs an edit in each
place. An agent that sees one list updates only that one. Keep one list and
derive the others. If a list cannot be derived, make the build fail when the
lists disagree.
