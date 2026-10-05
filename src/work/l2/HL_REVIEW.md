# Independent review: ライフライン ver.2 (highlight set)

You are the **independent checker**. Another agent wrote `/home/claude/l2/out_hX.json` from the user's highlighted textbook pages. The user, a Thai civil engineer who has sat the real JAC 特定技能2号 ライフライン・設備 実技 exam, asked that **the content and the language of the questions be checked before anything is deployed**. Assume nothing is right until you have checked it yourself.

Read first: `/home/claude/xl/INSTRUCTIONS.md` (rules for the Thai notes), `/home/claude/l2/INSTRUCTIONS.md` (format) and `/home/claude/l2/HL_WRITE.md` (what the writer was asked to do).

## For EVERY item, check
1. **Facts against the textbook page.**
   - Open `/home/claude/l2/pages/textNl_pNNN.txt` for the item's `src` and compare numbers, colours, names, definitions and order.
   - If `src` points to the wrong page, fix it. `grep` the pages folder to find the right one.
   - Also check against real Japanese practice. If the textbook itself contains an obvious misprint, do not build a question on it; for example, P102 says PF管 「耐燃性がない」, but PF is actually self-extinguishing. Use WebSearch for anything uncertain, and prefer official Japanese sources.
2. **Exactly one correct option**, and `ans` points to it. Solve the item yourself before looking at `ans`. No distractor may be defensible.
3. **Japanese:**
   - The stem and options read as natural JAC-exam Japanese, are unambiguous and are grammatical.
   - The option lengths do not give the answer away.
   - There is no 「テキストでは」.
4. **Readings:** every `漢字{かな}` is correct for its context, in stem_f, opts_f and the Thai notes alike.
5. **Thai notes** (sth, ath, oth, th):
   - natural Thai, explaining in **real-site context** so a Thai worker understands, not a literal translation;
   - sth must translate the whole question;
   - ath explains why the answer is right;
   - each oth explains what that wrong option actually is or means, and why it is wrong here;
   - th is a short memory hook;
   - no option numbers.
6. **Photos:** for every item with `img`, crop the image with PIL using `crop` and view the result. Save it to `/tmp/claude-0/rv_<id>.jpg` and Read it.
   - The object must be clearly visible.
   - The printed name label must be hidden whenever the question asks for the name.
   - The photo must really show the answer.
7. **Highlight relevance:** the item tests something the user actually marked in photo `/home/claude/l2/hl/<hl>.jpg`. Open the photo when unsure.
8. **Duplicates inside this file:** if two items test the identical fact from the same angle, delete the weaker one.

## How to fix
- Edit `/home/claude/l2/out_hX.json` in place.
- Keep the format and keep 4 options.
- Run `python3 /home/claude/l2/validate.py hX` until it reports 0 problems.
- Log every change in `/home/claude/l2/review_hX.md` as `id — problem → fix`.
- Be decisive. Fix what is wrong or weak. Do not rewrite items that are already good.

## Reply with
- the validator line;
- the number of items checked / changed / deleted;
- the change list (one line each);
- nothing else.
