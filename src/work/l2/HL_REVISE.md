# Revise ver.2 items so they look like the REAL exam

The user is a Thai civil engineer who has sat the real JAC 特定技能2号 ライフライン・設備 実技 exam.
- `/home/claude/l2/real_doboku.json` holds 81 REAL exam questions (土木区分), stems and options exactly as they appeared. The 土木 and lifeline tests share the textbook chapters on tools, management and safety, so these show the real style.
- `/home/claude/l2/realism.json` scores each of our items:
  - `topic`: A = the same item appears in a real 土木 question; B = strongly highlighted; C = peripheral.
  - `format`: 1 = looks real, 2 = differs, 3 = unlike the real exam.
  - `suggest`: the proposed change.

First read `/home/claude/xl/INSTRUCTIONS.md` (rules for the Thai notes) and `/home/claude/l2/INSTRUCTIONS.md` (item format). Then **read every question in real_doboku.json**, so you know the style by heart.

## The real style
- **About 64% name questions**:
  - the stem is the textbook definition (often nearly verbatim) and ends 「〜はなんですか。」「〜を何と言いますか。」「〜はどれですか。」;
  - or the stem is 「写真の〜の名前を選びなさい。」 or 「写真の正しい用語を選びなさい。」;
  - the options are 4 short names of sibling items.
- **About 36% definition questions**: 「〜の説明で正しいものを選べ。」「〜の用途で正しいものを選びなさい。」「写真の道具は、何のために使用しますか、正しいものを選びなさい。」 The options are near-verbatim textbook definitions of sibling items.
- **Blanks（　　　）are rare.** They are only for a key word inside a textbook sentence, e.g. 「コンクリートは（　　　）力には、弱いです。」
- **Negatives (about 12–16%)**: the user confirms that 「誤っているものを選びなさい」 DOES appear on the real lifeline exam, as do 「正しくないものを選べ」「含まれないものはどれですか」. All are fine.
- **No combination/matching items, no ordering items, and no "pick the right pair of numbers" items.**
- **Photos in about a third** of items.
- 選べ and 選びなさい are both used; mix them. Write なんですか in kana.

## What to do, for your file `/home/claude/l2/out_hX.json`
1. Apply each item's `suggest` from realism.json where it makes sense. Every format-2 or format-3 item must end up format 1, or be deleted if it cannot be made real-looking and is topic C trivia.
2. **Blank items** 「〜は（　　）です／といいます」 where the blank is the item name: convert them to 「〜はなんですか。」 or 「〜を何と言いますか。」. Keep a blank only where the real exam would use one, i.e. a key word inside a sentence; aim for at most about 10% of items.
3. **Mutated-statement items** (a true textbook sentence altered to make a false option): rewrite them as 「Xの説明で正しいものを選べ」. The options are the textbook definitions of X and 3 siblings from the same page.
4. **Combination, ordering and number-pair items**: rewrite each as a single-fact question in real style. For example, 「Y の気密試験で、管路内の圧力は（　　　）にします」 has one blank with 4 single values. If the single fact is trivial, delete the item.
5. **Keep 「誤っているもの」 wording.** The user has seen it on the real exam. Change a negative item only if it has another problem.
6. **Photos**: raise the photo share.
   - Where the textbook page has a clear figure of the answer item, use it for name questions (「写真の〜の名前を選びなさい」 / 「写真の正しい用語を選びなさい」) or for 用途 questions.
   - Figures are in `/home/claude/l2/fig/` and `/home/claude/l2/index.json` maps pages to figures.
   - Use `crop` to hide the printed label, and VERIFY by cropping with PIL to `/tmp/claude-0/rv_*.jpg` and viewing the result.
7. **Mirror pairs for topic-A items**: for items whose topic is A, if the set has only one direction (name→definition or definition→name), ADD the other direction as a new item with id `hX-NN` continuing after the highest existing number. Mark it `"dup_of"` the same as its partner, if that partner has one.
8. Keep distractors plausible. They should be siblings from the same page. Do not make them silly.
9. Facts must still match the textbook page `/home/claude/l2/pages/textNl_pNNN.txt` exactly. Keep `src`, `hl`, `from` and `dup_of`.
10. **Rewrite the Thai notes for every changed item**, in full and in site context: sth, ath, oth and th. Keep `漢字{かな}` readings everywhere. **Never change an existing item's `id`.** Deleting is allowed.
11. Run `python3 /home/claude/l2/validate.py hX` until it reports 0 problems.

## Reply with
- the validator line;
- the counts: changed / added / deleted / photos before→after / blanks before→after;
- one line per change;
- nothing else.
