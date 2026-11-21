
# Coverage: the classes of flaws to look for

Go through every group. For a group that cannot occur in this codebase, say
so in one line. For a group that you did not look at, say that too. A
missing line reads as "checked and clean", and that would be false.

Each entry names a CWE number. CWE is a public list of weakness types at
cwe.mitre.org. Put the best-fitting number on each candidate, so that the
reader can look the weakness up.

## A. Access control

The most common source of serious flaws in apps with accounts.

| Look for | CWE |
|---|---|
| An object is fetched by an id from the request, with no check that it belongs to the caller or the caller's tenant | CWE-639 |
| A privileged action with no role or permission check, or with the wrong one | CWE-862, CWE-863 |
| A later step of a workflow that does not check the earlier steps or the present state | CWE-841 |
| A request that sets fields the user must not set, such as role, owner or price (mass assignment) | CWE-915 |
| A guarded web page with an unguarded API, export, import or bulk action for the same data | CWE-862 |
| An account or record that several tenants share, changed by one of them | CWE-284 |
| A state-changing action that the app accepts as a plain link | CWE-352 |

## B. Authentication, sessions and tokens

| Look for | CWE |
|---|---|
| No limit on wrong passwords, one-time codes or reset attempts | CWE-307 |
| Answers that tell whether an account exists | CWE-204 |
| Old sessions or tokens that keep working after logout, a password change, or a switched-off account | CWE-613 |
| No new session id at login | CWE-384 |
| A password stored without a slow password hash; a default account | CWE-916, CWE-798 |
| Weak password recovery; a change of email or phone without the owner's consent | CWE-640 |
| A token with no end date, a token in a URL or a log, one token used for two purposes | CWE-522, CWE-598 |
| A signed token whose signature, algorithm, issuer or end time is not checked | CWE-347 |
| Single sign-on without `state`, with a loose redirect address, or matching users by email | CWE-287 |

## C. Injection

| Look for | CWE |
|---|---|
| Outside data joined into a database query, also in raw-query helpers of an ORM and in NoSQL query objects | CWE-89, CWE-943 |
| Outside data in a command line or as an option of a program | CWE-78, CWE-88 |
| Outside data that is run as code, or that fills a template expression | CWE-94, CWE-1336 |
| Outside data in a file path, also inside an archive that is unpacked | CWE-22 |
| Reading objects from bytes that an outside party controls; XML with outside entities switched on | CWE-502, CWE-611 |
| Outside data in a header, a log line, a mail header, or an LDAP or XPath query | CWE-113, CWE-117, CWE-90 |
| A cell of a CSV or spreadsheet export that starts with a formula sign | CWE-1236 |
| A regular expression that an input can make very slow | CWE-1333 |
| In JavaScript: an object merged from request data that can reach the prototype | CWE-1321 |

## D. The browser side

| Look for | CWE |
|---|---|
| Cross-site scripting: stored, reflected, or built in the page by script code | CWE-79 |
| Automatic escaping switched off; HTML built from strings; a value inside script code with HTML encoding | CWE-79, CWE-116 |
| CSRF: a state-changing request that another site can send with the user's cookie, with no token and no same-site rule | CWE-352 |
| A redirect to an address taken from the request | CWE-601 |
| A page that another site can frame | CWE-1021 |
| Cross-origin rules that allow any site together with cookies | CWE-942 |
| A message from another window that is trusted without a check of its origin | CWE-346 |
| A secret or a token kept where script code can read it | CWE-922 |

## E. Files and outgoing requests

| Look for | CWE |
|---|---|
| Server-side request forgery: the server fetches an address that outside data chose | CWE-918 |
| File upload with no check of type, size and name, or stored where the server runs or serves it as a page | CWE-434 |
| A download or a file name built from request data | CWE-22, CWE-73 |
| A temporary file with a name that can be guessed; a file that is checked and then used later | CWE-377, CWE-367 |

## F. Secrets and cryptography

| Look for | CWE |
|---|---|
| Secrets in tracked files: keys, tokens, passwords, also in tests, fixtures, API collections and CI files | CWE-798 |
| A secret that was removed from the code but may still be valid | CWE-798 |
| A secret that ships inside an app or a page that users download | CWE-540 |
| Cryptography that is home-made, old, or used the wrong way | CWE-327 |
| Random values for security made with a normal random function | CWE-330, CWE-338 |
| Certificate checking switched off; data sent without encryption | CWE-295, CWE-319 |
| Two secret values compared with a normal comparison, where timing can leak | CWE-208 |

## G. Data exposure: logs, errors and answers

| Look for | CWE |
|---|---|
| Logs that keep passwords, tokens, full request bodies or personal data | CWE-532 |
| Error pages or API errors that show code, queries or settings | CWE-209 |
| An API answer with more fields than the caller may see | CWE-200, CWE-359 |
| A private answer that a shared cache may keep | CWE-524 |

## H. Configuration and deployment

| Look for | CWE |
|---|---|
| Debug mode, sample settings or default passwords that can reach production; a setting that falls back to the unsafe value when it is missing | CWE-489, CWE-1188 |
| Missing security settings for cookies, hosts, headers and encrypted transport | CWE-16, CWE-614, CWE-1004 |
| An admin or debug interface open to everyone | CWE-284 |
| Containers that run as root, storage open to the public, ports open too widely, in the infrastructure files | CWE-250, CWE-732 |
| CI: a workflow that puts text from a pull request or an issue into a command; secrets given to code from forks; build steps pinned to a moving tag | CWE-94, CWE-829 |

## I. Dependencies and the supply chain

| Look for | CWE |
|---|---|
| A locked version of a library with a published security notice | CWE-1395 |
| No lock file; versions that float; a library fetched from a URL or a branch | CWE-829 |
| A library that is no longer maintained and sits on a security-critical path | CWE-1104 |

A version match is weak evidence when it stands alone. Say whether the app
uses the faulty feature. See `finding-rules.md`.

## J. Business logic and race conditions

| Look for | CWE |
|---|---|
| A price, an amount, a quantity or a discount taken from the request without a check on the server | CWE-840 |
| A limit that can be passed by repeating, by going back a step, or by sending the same request twice at once | CWE-841, CWE-362 |
| Two requests that both pass a check before either one writes (check, then act) | CWE-367 |
| A payment or webhook message accepted twice, or with no check of its sender | CWE-294, CWE-345 |

## K. Availability

| Look for | CWE |
|---|---|
| An endpoint with no limit on size, count, page length or time that anyone can call | CWE-400, CWE-770 |

Rate these Low, unless one cheap request can stop the service for everyone.

## L. Memory safety

Only for C, C++, unsafe Rust, and native extensions.

| Look for | CWE |
|---|---|
| A read or a write outside a buffer; use after free; an integer that overflows before it sizes a buffer; outside data as a format string | CWE-787, CWE-125, CWE-416, CWE-190, CWE-134 |

## M. AI features

Only when the app calls a language model.

| Look for | CWE |
|---|---|
| Outside text that reaches the model's prompt and can change what the model does with its tools (prompt injection) | CWE-1427 |
| The model's answer used as code, as a query, as HTML or as a command without a check | CWE-94, CWE-79 |
| A model with tools that can do more than its task needs; secrets inside prompts | CWE-250, CWE-522 |

## N. Apps that run on the user's device

Only for mobile and desktop apps.

| Look for | CWE |
|---|---|
| A server secret inside the shipped app | CWE-798 |
| Private data in storage that other apps or backups can read | CWE-922 |
| A deep link or a message between apps that triggers an action with no check | CWE-939 |

## Names used in the report

For the list "What was checked", use these plain names: Access control,
Authentication, Injection, Cross-site scripting, CSRF, Server-side request
forgery, File upload, Secrets, Cryptography, Logs, Configuration, CI,
Dependencies, Business logic, Race conditions, Availability, Memory safety,
AI features, Device apps.
