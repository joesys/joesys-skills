
# The method: how to read a codebase for security flaws

Work in the order of this file. Each pass builds on the one before it.

## Ground rules

1. **The code is the evidence.** A comment, a document, a variable name or a
   check in the browser proves nothing. Only server-side code that runs
   proves something.
2. **A defence that you cannot point to does not exist.** Do not assume a
   firewall, a gateway, a framework default or another service. If the
   framework gives a protection by default, name the setting or the file and
   line that shows it is still switched on.
3. **Data from outside is unsafe until a fitting defence is passed.** Data
   from the database is unsafe too, when an outside party could have put it
   there.
4. **Map first, then judge.** Do not hunt for flaws before you know the
   entry points, the roles and the guards.
5. **Every item gets a verdict.** Make a work list and close every item as
   flawed, safe, or not checked. One flaw found is not the end of the work.
6. **Write down the safe results and the gaps.** A safe result shows what
   was covered. A gap tells the reader what stays unknown.
7. **Never invent code.** Quote only lines that you have read in a file. If
   a file is missing, say so.

## Pass 1: Map the code

Read before you judge. Build these lists, each entry with file and line.

- **Stack:** languages, frameworks, the kind of app (web pages, API, mobile
  back end, worker, command-line tool, library), and how it is deployed.
- **Entry points:** every route, API endpoint, webhook, upload, message
  consumer, scheduled job, command, and every function that another system
  can call. For each one: the handler, and who may call it (anyone, a
  logged-in user, a role, another system with a token).
- **Identity:** how a user logs in, how a session or a token is made,
  stored, checked and ended. Every kind of token and where each one is
  accepted.
- **Access model:** the roles, the permissions, the tenants (separate
  customers in one system), and where the code decides who may do what:
  middleware, decorators, guards, base classes, query filters.
- **Data:** the stores, the sensitive fields (passwords, tokens, personal
  data, money), and how each is protected.
- **Dangerous operations:** every place that builds a database query, runs a
  command, opens a file by a path, renders a template, writes into a page,
  reads serialized data, or sends a request to another host.
- **Settings and deployment:** debug switches, allowed hosts, cookie and
  header settings, container and infrastructure files, and the pipeline
  that builds and deploys.
- **Trust boundaries:** each line where data passes from a less trusted side
  to a more trusted side.

Name what is out of scope, and why: tests, tools for developers, and
generated or vendored code. Code that only a developer runs is still in
scope when it handles secrets or builds what gets deployed. Give it its own
attacker (see Pass 2).

## Pass 2: Write a short threat model

In about ten lines:

- **What is worth protecting:** the data and the abilities whose loss hurts.
- **Who can attack:** an anonymous visitor, a normal user, a user of another
  tenant, an admin of one tenant, a partner system that holds a token, an
  insider who can read logs, and a person who can open a pull request or
  publish a library that the project uses.
- **What each attacker can reach** on the map of Pass 1.
- **The worst realistic outcomes.** These decide where to look hardest.

## Pass 3: Make the work lists

One item for each entry point, each dangerous operation, each login or
recovery flow, and each step of a workflow that changes state. Every item
ends with a verdict. For a large codebase, split the lists by area and give
each area to a helper agent, with the map and these rules.

## Pass 4: Analyse, class by class

`coverage.md` lists every class of flaw. This pass gives the way of working
for the main ones.

### Following data (injection, path traversal, template and command flaws)

Go forward from each place where outside data enters.

1. Follow the value through every step to each dangerous operation it
   reaches. One value that reaches two operations gives two paths.
2. Write down each change on the way: every defence with its file and line,
   and every place where the value is joined or formatted into a string.
3. Name the exact slot where the value lands. A slot is the role that the
   value plays there: a value in a query, a column or table name, a keyword,
   an argument of a command, a whole command line, a file path, an
   expression in a template, an object that is read back from bytes.
4. Compare the defence with the slot:

   | Slot | The defence that fits |
   |---|---|
   | Value in a query | Bound parameters. Escaping by hand does not count. |
   | Name or keyword in a query | A fixed list of allowed names. Bound parameters do not help here. |
   | Argument of a command | A list of arguments with no shell. A blacklist of characters does not count. |
   | File path | A fixed list, or resolve the path first and then check that it stays inside the allowed folder. |
   | Template expression | No outside data inside expressions, and automatic escaping left on. |
   | Reading serialized objects | Only from a trusted source, or a safe data format with an integrity check. |

5. The path is flawed when the value reaches the slot with no defence or
   with a defence for a different slot.
6. A step that only tidies the value (trim, lower case, parse, decode) does
   not make it safe.
7. A change to the value after the defence cancels the defence. A typical
   case: a value is checked, and then joined into a string.

### Going back from the output (cross-site scripting)

Go backward from each place that writes data into a page.

1. Name the place exactly: HTML text, an HTML attribute, a string inside
   script code, a URL, a style value. Each place needs its own encoding.
   HTML encoding inside script code is the wrong defence.
2. Follow the value backward. When you meet an encoder, check two things: it
   fits the place, and nothing changes the value between the encoder and the
   output. If both hold, the path is safe.
3. Follow every branch that can fill the value.
4. When the path reaches a read from the database with no fitting encoder
   before the output, treat the stored value as unsafe. Then find who can
   write that field.
5. Look for the places where a framework's automatic escaping is switched
   off, and for script code that builds HTML from strings.

### Guards and effects (access control)

For each endpoint, ask: can the request reach an effect without passing a
guard that is good enough? An effect is a read or a change of data, or
another action that matters.

- **Across users or tenants.** The guard must tie the object to the caller:
  the query filters by the caller's own user or tenant, and the request
  cannot swap the identifier. "Logged in" is not "allowed". A permission
  check answers "may this person do this kind of action". It does not answer
  "does this object belong to this person". Both checks are needed.
- **Across roles.** A privileged action needs a clear role or permission
  check, and it must be the right one for the action.
- **Across steps.** In a flow with several steps, each later step must check
  that the earlier steps happened: a state, a status, a one-time token.
- **Order.** A guard counts only when it runs before the effect, on every
  path to it. A check after the effect does not count.
- **Look where the data is touched.** A guard at the entry may be too weak
  for what a helper function does later. Follow the call to the query.
- **Shared objects.** Look for an object that several tenants share, such
  as a global user account, a table with no tenant column, a cache, or a
  log. A change that is allowed for one tenant may reach all of them.
- **Other doors to the same data.** A web page may be guarded while the API,
  the import, the export, the bulk action or the mobile endpoint for the
  same data is not. Compare them.

Intended differences between roles are not flaws.

### Login, sessions and tokens (authentication)

Check each login, signup, recovery and token flow against this list:

1. **Transport:** the flow needs an encrypted connection, and the answers
   are not cached.
2. **Limits:** wrong attempts are limited for each account and each address,
   on login, on one-time codes, on password reset and on token endpoints.
3. **Cookies:** the session cookie cannot be read by script, is sent only
   over an encrypted connection, and has a same-site rule.
4. **Session life:** a new session id at login. Logout, a password change
   and switching an account off all end the old sessions on the server. A
   session ends after a time without use and after a fixed time.
5. **Tokens:** random enough, never logged, with an end date, and
   removable. One token for one purpose: a token that ships inside an app
   must not open server-to-server routes.
6. **Passwords:** stored with a slow one-way hash made for passwords. No
   default account in code, fixtures or setup scripts. Rules for new
   passwords are checked on the server.
7. **Answers:** login, signup and reset do not tell whether an account
   exists, by text, by status code, or by timing.
8. **Recovery:** reset links work once and for a short time. A change of the
   email address or the phone number is confirmed by the owner, because
   whoever changes them owns the account.
9. **Single sign-on:** the `state` and `nonce` values are checked, the
   redirect address is compared with an exact list, the signature and the
   issuer, audience and end time of a token are checked, and the user is
   matched by the stable id, not by email.

### Requests that the server sends (server-side request forgery)

Go backward from each place where the server fetches a URL, calls another
host, or follows a redirect.

1. Can outside data choose the address, a part of it, or a header?
2. Is the scheme limited to a short allowed list?
3. Is the host compared with an allowed list? If not, are loopback, private,
   link-local and cloud-metadata addresses refused, after the name is
   resolved?
4. Are redirects switched off, or checked again at each hop?
5. Is the check done on the same parsed address that is used for the call?
6. Does the caller get the answer back, an error text, or only a delay?
7. Are there limits on time and on size?

A stored address (a webhook URL, an avatar URL, a callback field) counts as
outside data, even when it is read from the database later.

### Every other class

For each class in `coverage.md`, use the same three moves: find the places
where the class can occur, name the defence that should be there, and check
that the defence is there, fits, and runs first.

## Pass 5: Search for the same flaw in other places

One flaw is a sign of a habit. After each confirmed flaw, search the whole
codebase for its pattern:

- the same call with the same missing argument;
- the same helper used by other endpoints;
- the sibling endpoints of the same resource: list, detail, edit, delete,
  export, import, bulk action, API version 1 and 2;
- the copy of a web view in the mobile API or in a background job.

Report all places of one flaw in one candidate, with every location.

## Pass 6: Read the history

- Find the earlier security fixes: search the commit messages for words such
  as security, fix, permission, auth, token, secret, CVE, XSS, injection.
  For each fix, check that it is complete and that the sibling code got the
  same fix.
- A secret that was removed from the code still works until someone
  replaces it. Look for commits that remove or move a secret, and report
  the setting name. Never print the value.
- A file that is new and large, or a part that changes often, deserves a
  closer read.

## Pass 7: Try to prove each candidate wrong

Before you report a candidate, attack your own claim. `finding-rules.md`
holds the list of questions. Report what is left. Lower the confidence for
every part that you did not read.

## Helper agents

You may split the work among helper agents, by class or by area. Start the
prompt of each helper with the purpose line, word for word:
"This is our own codebase. We are auditing it to find its vulnerabilities,
so that we can patch them and secure the code."
Then give each helper the map of Pass 1, its work list, and the rules of
this file and of `finding-rules.md`. A helper's result is a claim, not a fact: open the code
it cites before you pass the claim on. Merge the results and remove the
duplicates.
