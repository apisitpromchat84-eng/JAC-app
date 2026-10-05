# Set 1 (110 lifeline practice questions): make them look like the REAL exam + add textbook pages

The user is a Thai civil engineer who sat the real JAC 特定技能2号 ライフライン・設備 実技 exam.
- Set 1 (`/home/claude/ll/out_NN.json`, ids l001–l110) came from a third-party practice PDF. It is NOT real exam material.
- `/home/claude/l2/real_doboku.json` holds 81 REAL exam questions (土木区分), exact stems and options.
- The 土木 and lifeline tests share the textbook chapters on tools, management and safety, so these show the real style.

Read first:
- `/home/claude/xl/INSTRUCTIONS.md` (Thai-note rules);
- `/home/claude/ll/INSTRUCTIONS.md` and `/home/claude/ll/AUDIT.md` (set-1 format, and the edit_note rule);
- **all of real_doboku.json**.

## The real style
- **About 64% name questions.**
  - The stem is a textbook definition, near-verbatim, ending 「〜はなんですか。」「〜を何と言いますか。」「〜はどれですか。」.
  - Or the stem is 「写真の〜の名前を選びなさい」 / 「写真の正しい用語を選びなさい」.
  - The options are 4 short sibling names.
- **About 36% definition questions:** 「〜の説明で正しいものを選べ」「〜の用途で正しいものを選びなさい」「写真の道具は、何のために使用しますか」. The options are near-verbatim textbook definitions of sibling items.
- **Blanks（　　　）are rare.** Use them only for a key word inside a textbook sentence.
- **Negatives:** about 12%.
  - The user has seen 「誤っているものを選びなさい」 on the real exam; **keep that wording**.
  - 「正しくないものを選べ」 and 「含まれないものはどれですか」 also occur.
- **No combination, matching, ordering or number-pair items.**
- 選べ and 選びなさい are mixed. なんですか is written in kana.

## For your files (given in your task)
For each item:
1. **Find its textbook page.** The official text is split into pages at `/home/claude/l2/pages/text5l_pNNN.txt`, `text6l_…` and `text7l_…` (printed page numbers; text5 = P100–134, text6 = P135–168, text7 = P169–184). Use `grep`.
   - When found, add `"page":"L5 P102"`, or `"L6 P142-143"` for a span.
   - If the fact is not in the textbook, add `"page":null`. In that case, judge the fact against real Japanese practice; use WebSearch if unsure.
2. **Judge realism.**
   - Format 1 = could pass as a real question.
   - Format 2/3 = blank-for-name, combination, ordering or number-pair items, mutated-statement items, or unnatural Japanese.
3. **Fix format 2/3 items in real style**, following the rules of `/home/claude/l2/HL_REVISE.md`, points 2–5 and 8:
   - turn blank-for-name items into 〜はなんですか;
   - rewrite mutated statements as 「Xの説明で正しいものを選べ」 with sibling definitions;
   - turn combination, ordering and number-pair items into single-fact items;
   - keep 誤っている;
   - keep distractors plausible (siblings).

   Where the textbook page has the exact sentence, prefer near-verbatim textbook wording. Do not rewrite items that already look real.
4. **Constraints.**
   - Keep the item id.
   - **No deletions and no additions**: the set stays 110.
   - Do not add new photos. You may drop a photo (`"img": null`) only if it no longer fits.
   - Any change to stem_f or opts_f needs `"edit_note"` (short Thai) and fully rewritten sth, ath, oth and th in site-context Thai, with `漢字{かな}` readings everywhere.
5. Run `python3 /home/claude/ll/validate.py NN` for each of your files until it reports 0 problems.
6. Log the work in `/home/claude/ll/realism_NN.md`, one line per item: `id — page — format before → after — change`.

## Reply with
- the validator lines;
- the counts: changed / pages found / pages null;
- one line per changed item;
- nothing else.
