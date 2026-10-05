# Thai study notes for JAC 建設 特定技能2号 exam questions

The reader is a Thai construction worker or engineer in Japan who is studying for the JAC construction exam (建設分野 特定技能2号). They read Thai well and are still learning Japanese. The notes appear in the practice app under each question once it has been answered.

The user asked for this explicitly: **do not translate word for word.** Translate the way an experienced Thai site engineer would explain it to a Thai colleague on a Japanese jobsite. That means:
- Use the words Thai construction people really use, such as นั่งร้าน, แบบหล่อ, เหล็กเสริม, รถขุด, ผู้ควบคุมงาน or หัวหน้างาน.
- Say what the thing is, what it is for on site, and when it is used.
- Keep it short and easy.

## Input / output
- Input: `/home/claude/xl/in_NN.json`. Each item has id, cat, src, stem, opts, ans (1-based index of the correct option), old_tip and img.
  - `stem` and `opts` show readings as `漢字(かな)`.
  - `old_tip` is the app's current short Thai note. Keep its facts.
  - If `img` is set, look at the picture with the Read tool at `/home/claude/build/<img>` before you write.
- Output: `/home/claude/xl/out_NN.json`. It is a JSON array with one object per input question, in the same order:

```json
{"id":"g069",
 "sth":"full Thai translation of the question",
 "ath":"the correct answer: full Thai translation + why it is right, in site context",
 "oth":["...", "", "...", "..."],
 "th":"จำให้ได้: the key point / memory tip",
 "flag":"optional — only if you think the app's answer or old_tip may be factually wrong; say why"}
```

- `oth` has one entry per option, in the same order as `opts`. The entry for the correct option (index ans-1) must be `""`. Each other entry gives the option's meaning in Thai and a short reason why it is not the answer, or what it really is.
- For questions that ask for the one that is NOT correct (正しくない / 不適切 / 誤り / 含まない …):
  - The correct answer is the false statement, so `ath` explains what is false in it and what the truth is.
  - The other options are true statements, so their `oth` end with "→ ถูกต้อง" plus a short note if useful.

## Japanese inside the Thai text
- You may mention Japanese terms in the Thai notes. The key term being tested should appear in Japanese at least once.
- **Every kanji must carry its reading**, written as `漢字{かな}`, for example `主任技術者{しゅにんぎじゅつしゃ}` or `選{えら}ぶ`.
  - The braces hold hiragana only.
  - They go right after the kanji run, and okurigana stays outside: `行{おこな}う`.
- Katakana and hiragana words need no braces.
- Readings must be correct for this construction/legal context. Copy the readings used in stem/opts when the same word appears, for example `見積{みつもり}` or `工種{こうしゅ}`.
- Put the Thai meaning after each Japanese term, e.g. `監理技術者{かんりぎじゅつしゃ} (วิศวกรควบคุมงานระดับสูง ใช้กับงานใหญ่ที่จ้างช่วงเกินวงเงินที่กฎหมายกำหนด)`.

## Rules
1. **Never refer to options by number or position.** Write "ข้อ 2", "ตัวเลือกที่ 3", "ข้อบน" and the like nowhere. The app shuffles the options. Name the content instead. Circled numbers ①②③ are fine only for listing steps of a procedure.
2. **Facts must be right.** This is exam material.
   - Do not invent numbers, laws or distances.
   - If you are not sure of a detail, leave it out rather than guess.
   - If you believe the app's answer (`ans`) or `old_tip` is wrong, still write the notes for the app's answer, and explain your doubt in `flag`.
3. Formatting: plain text. `<b>` for emphasis (use sparingly: the key word, or ไม่ถูกต้อง/ผิด in negative questions) and `<br>` for line breaks are the only HTML allowed. No markdown.
4. Length guide:
   - sth: one sentence.
   - ath: 1–3 sentences.
   - Each oth entry: about 1–2 sentences.
   - th: 1–4 short lines. It is the part people memorise, so make it catchy and concrete, e.g. "กระบะอยู่กลางระหว่างล้อ = スクレーパ".
5. Tone: friendly and clear, like a senior colleague. No filler, no "ดังนั้นคำตอบคือ".

## Example (already in the app — match this depth and style)
```json
{"id":"g076",
 "sth":"จงเลือกวิธีที่เป็นมาตรฐานของ KYT (危険予知訓練{きけんよちくんれん} = การฝึกคาดการณ์อันตรายก่อนเริ่มงาน)",
 "ath":"KYT基礎{きそ}4ラウンド法{ほう} = วิธี KYT พื้นฐาน 4 ขั้น (4R法{ほう}) ใช้ในการประชุมเช้าก่อนเริ่มงาน ให้ทีมช่วยกันมองหาอันตรายในงานวันนี้แล้วตกลงวิธีป้องกันร่วมกัน",
 "oth":["", "ハインリッヒの法則{ほうそく} = กฎของไฮน์ริช: อุบัติเหตุร้ายแรง 1 ครั้ง เบื้องหลังมีอุบัติเหตุเล็ก 29 และเหตุเกือบเกิด 300 → เป็นสถิติ ไม่ใช่วิธีฝึก", "リスクの見積{みつもり} = การประเมินระดับความเสี่ยง (ความรุนแรง × โอกาสเกิด) → เป็นขั้นหนึ่งของ リスクアセスメント ไม่ใช่วิธีฝึก KY", "5S活動{かつどう} = กิจกรรม 5ส จัดระเบียบที่ทำงาน → ไม่ใช่วิธีฝึก KY"],
 "th":"4 ขั้นของ 4R法{ほう}:<br>① 現状把握{げんじょうはあく} มีอันตรายอะไรแฝงอยู่<br>② 本質追究{ほんしつついきゅう} นี่คือจุดอันตราย<br>③ 対策樹立{たいさくじゅりつ} ถ้าเป็นคุณจะทำอย่างไร<br>④ 目標設定{もくひょうせってい} พวกเราจะทำแบบนี้"}
```

## When done
Run `python3 /home/claude/xl/validate.py NN`. Fix every problem it lists and run it again until it reports 0 problems.

Then reply with:
- the validator's final line;
- the list of any `flag`s;
- nothing else.
