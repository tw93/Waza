# IME / Unicode Debugging Reference

Recurring patterns in webview-hosted and native macOS apps. Check these before forming a hypothesis.

## IME State Desync

**Symptom**: Latin characters appear correctly but CJK input is dropped, doubled, or committed at the wrong time.

**Cause candidates**:
- Input method switch mid-composition: the IME commits the preedit with a stale target, then the new mode processes the same keystrokes again.
- `keydown` handler consuming events during active composition: suppress the confirmation event's bound submit/navigation action while preserving normal IME text commitment. Do not queue that action for `compositionend`; check the event-ordering section for cases where `isComposing` is already false.
- Webview + native frame split focus: in Tauri, the webview and the native window title bar can hold focus simultaneously. A click on a native control during IME composition triggers a focus-out, committing incomplete preedit text.

**Instruments**:
- Log `compositionstart`, `compositionupdate`, `compositionend` sequence; confirm they fire in order without gaps.
- Log the `data` field of each `compositionupdate`; a sudden empty string signals a forced commit.

## Cursor Position Drift After IME Commit

**Symptom**: After confirming a CJK word, the cursor jumps to the wrong position or the selection collapses.

**Cause candidates**:
- DOM mutation during composition: React/Svelte/Vue re-rendering while `isComposing` is true will reset the selection. Batch state updates and flush only on `compositionend`.
- Mixing offset units: JavaScript string lengths and text-node DOM offsets use UTF-16 code units; string iteration counts code points, and visible-character operations may need grapheme clusters. Identify the receiving API's unit before converting positions; replacing `str.length` with `[...str].length` can itself cause drift.

## Emoji ZWJ Sequence Splitting

**Symptom**: Multi-person or profession emoji (e.g. `👩‍🚒`) renders as two or three separate emoji, or the ZWJ (`U+200D`) appears as a visible character.

**Cause candidates**:
- String sliced at a UTF-16 code-unit offset: `str.slice(0, n)` splits a ZWJ sequence if `n` falls inside the sequence. Use `Intl.Segmenter` with `granularity: 'grapheme'` for visible-character truncation.
- Font does not support the sequence: the font renders each code point individually. Verify with `canvas.measureText` or by checking which font is actually used via `document.fonts`.
- Serialization strips ZWJ: some JSON encoders normalize or escape `U+200D`. Verify the raw bytes of the stored string.

**Test**: `[...'👩‍🚒'].length` is 3 code points; `[...new Intl.Segmenter(undefined, {granularity: 'grapheme'}).segment('👩‍🚒')].length` is 1 grapheme cluster. Test offsets separately against the consuming API.

## `compositionend` / `keydown` Event Ordering

**Symptom**: The action bound to Enter or Tab fires during IME confirmation, submitting incomplete input.

**Cause candidate**: `compositionend` can precede the confirmation `keydown`, leaving `isComposing` false, or follow it. Capture the actual order for the affected IME and host rather than inferring it from the OS.

**Verification target**: IME confirmation commits text without submitting; a subsequent deliberate Enter submits once. A flag cleared on `compositionend` has the same ordering gap as `isComposing`. Log the key events and composition boundaries, derive the confirmation-key guard from the observed host behavior, and replay both orderings plus a normal Enter in regression tests. Do not substitute an arbitrary timeout for that evidence.

## macOS Text System vs Webview Conflict

**Symptom**: Undo (`Cmd+Z`) reverts individual IME preedit characters instead of committed words, or system text shortcuts (Cmd+Shift+Left for word selection) behave differently inside vs outside the webview.

**Cause**: WKWebView has its own text system that partially overlaps with NSTextView conventions. The webview host's key-handling config can suppress system shortcuts (Tauri's `preventDefaultFor` in `tauri.conf.json` or `app.json`, or the equivalent in other hosts); check it for `preventDefault` rules that are too broad.
