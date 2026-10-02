# Building and freezing the design in Claude Design

Claude Design is the Artifact tool's "Design" type: a canvas of live artboards. The type's URL is per account, so never hardcode one. Discover it at run time.

## 1. Create the design artifact

1. Call the Artifact tool with `action: "quickstart"` and `intent: "design"`. The result lists the Design type and its `type_url`. If it lists no Design type, use the HTML fallback instead.
2. Publish to start the artifact: Artifact with `type_url` set to the one returned, a short `title` (the project name plus " design"), no files, and `auto_open: "after_first_write"`.
3. The create result carries the type's own instructions and how to fill it. Follow them. Do not assume them from memory; they are the authority on how artboards are laid out.
4. Draw one artboard per approved screen and one for `tokens`. Label each artboard with its id exactly (`screen-cart`, `tokens`). Updating the artifact later means publishing again to the same `url`.

Tell the user the artifact link after the first write so they can open it and review.

## 2. Snapshot at freeze time

Workers cannot rely on a live link, so on approval save a snapshot:

1. Read the artifact with the Artifact tool: `action: "read"`, the artifact `url`, and `page: true` so the rendered page is returned. The result names the local file where the page was saved.
2. Copy that file to `docs/waves/design/snapshot.html`.
3. Check the snapshot: it must be a self-contained HTML file, and it must contain every screen id and `tokens` (search the file for each id). Report to the user which ids were found.
4. If the read returns something unusable (no screen ids, or only a shell page), do not pretend it worked. Tell the user plainly. Offer two ways forward: they export the design themselves and put it at `docs/waves/design/snapshot.html`, or you rebuild the approved design as the HTML fallback with the same screen ids. Do not continue to decomposition until a usable snapshot exists.

## 3. Record the freeze

`docs/waves/design/DESIGN.md` is the human-readable freeze record:

```markdown
# Design (FROZEN)

- Source: <Claude Design URL, or "HTML fallback">
- Approved: <YYYY-MM-DD>
- Snapshot: docs/waves/design/snapshot.html

| Screen id | Feature |
|---|---|
| screen-cart | F3 |

## Tokens
<colours, spacing scale, type scale in a few lines>

FROZEN: changes after approval require replanning.
```
