# Independent review: ライフライン ver.2 questions

You are a strict second reviewer. You did NOT write these questions. Read `/home/claude/xl/INSTRUCTIONS.md` and `/home/claude/l2/INSTRUCTIONS.md` first (rules for Thai notes, readings, style, photos, `src` page refs).

Your file: `/home/claude/l2/out_rN.json` (N given in your task). Edit it in place.

For EVERY question:
1. **Open the cited textbook page** (`src` like "L5 P118" = text5l printed page 118; `/home/claude/l2/index.json` gives the PDF page number; read it with the Read tool on `/home/claude/l2/text5l.pdf` etc. and/or `/home/claude/l2/pages/text5l_p118.txt`). Confirm:
   - the fact really is on that page (fix `src` if it's on another page),
   - the keyed `ans` is correct per the text and Japanese practice, and **no other option is also defensible**,
   - the stem is natural, unambiguous JAC-style exam Japanese (not 「テキストでは」),
   - for negative questions (誤っている/含まれない/適切でない) the Thai `sth` makes the direction obvious.
2. **Readings**: every `{}` reading in stem_f / opts_f / notes is correct in context.
3. **Thai notes**: accurate, site-context, natural Thai a Thai worker understands; `oth` aligned to options with "" at ans-1; no option numbers.
4. **Photos** (`img` + `crop`): view `/home/claude/l2/crops/<id>.jpg` (already cropped). The photo must show the item, and **must not show a printed label that gives away the answer**. If it does, tighten `crop` (fractions of the original image `/home/claude/l2/<img>`) or remove the photo and make it a text question.
5. Too-easy or trivial questions (answer obvious from wording alone) → make distractors more plausible.

Fix problems directly. Keep JSON valid. Run `python3 /home/claude/l2/validate.py rN` until 0 problems. Log changes in `/home/claude/l2/review_rN.md` (`id — problem → fix`), or "no changes".

Reply with: validator line, number of questions changed, and any question you think should be deleted (id + reason). Nothing else.
