# Documentation quality contract

Use this contract for guides, API docs, examples, public docstrings, and public
code comments.

Do not use the reading-level rule for LLM prompts, agent instructions, or skill
control files. Those files may state this contract, but they are not reader
content.

## Reading level

- Keep each prose part at U.S. grade 12 or below. Aim for grade 9 or 10 in user
  guides.
- Check each useful prose part. Easy text must not hide one hard part.
- Do not score code, URLs, command output, schemas, legal text, or text made by
  a tool. Do not score tables made mostly of public names.
- Log each case where text must stay exact. Name its owner, cause, scope, and
  review date. Do not waive a whole file with no notice.

## Public-surface coverage

List each public surface in scope. This includes APIs, library calls, MCP tools,
config keys, commands, events, and shared schemas. For each item, add:

- its goal, users, inputs, limits, defaults, and access needs;
- at least one tested use case;
- the return value, output, status, or side effect; and
- each user error, what it means, and how to fix it.

Use `Not applicable` with a cause when an item has no result or error. A blank
part does not count.

## Verification and gate behavior

- Link each list item to its source, docs, example, result, errors, owner, and
  test proof.
- Test examples with the smallest useful test.
- Run the project's docs check. Block on a missing check or list item. Also
  block on hard prose, a stale example, a missing result, or unclear errors.
- Tell a docs flaw from a broken check. A broken check is not a pass.
- Check new and changed docs now. Log old debt with an owner and a cleanup plan.
  Do not add new debt.
