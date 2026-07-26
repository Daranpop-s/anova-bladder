# Bladder explanation — aligned to the data

Your Act 2 (Slides 10–12) rewritten so every claim matches the analysis, in your
mechanic voice. Changes are small but important: two numbers tighten, and one
pain-point line is understated — **you actually have parts you *can* claim.**

---

## Alignment check (what the data says about each line you already have)

| Your line | Data verdict | Action |
|-----------|-------------|--------|
| "429 of them" | ✅ 429 records (417 with a usable life reading) | keep — say "429 records, 417 we could read a life on" if a judge asks |
| "roughly half manufacturer, half us" | ✅ 46% manufacturer / 54% us | keep exactly |
| "Deformation? About eighty percent our own operation" | ✅ **80.0%** | keep — it's exact, lean on it |
| "Leaks? About seventy percent the incoming **lot**" | ⚠️ ~72% manufacturer, but that's mostly **design**, not the delivered lot (batch is ~13%) | **reword to "the manufacturer's part"** |
| "we can't even make a claim" | ⚠️ True for *most* parts — but **two parts DO have a claimable bad-lot signal** | **upgrade to a win** |
| "cluster by when we removed them, not when delivered" | ✅ removal clusters (mid-2024, 50% premature); install doesn't | keep — name the quarter |
| "live two, three times the median" | ⚠️ understated — some live **6× their target, and one part 24×** | optional: sharpen |

The one that matters most: **"incoming lot" vs "the manufacturer's design."** Leaks
are ~72% the manufacturer, but the driver is *which part it is* (design + incoming
quality), not a bad shipment. Only **two specific parts** show a true bad-delivery
signal. Saying "lot" for all of them is the one claim a sharp manufacturer rep
could puncture — so split it: design for the many, lot for the two.

---

## SLIDE 10 — The Pain  *(aligned)*

Why Bladder? This time, I didn't inspect alone. I brought in the Pioneers of NKE —
mechanics who worked these engines before this shop was built. And they told me two
things that keep them up at night.

First: *"Seven — the bladders that arrive aren't the same. Some break on the FIRST
tire. Some break halfway. And some live SIX times their rated life. Same part, same
price, different fate — and for most of them we can't even make a claim."*

Second: *"Some bladders deform. Some leak. We think it's how we use them… but
honestly? We don't know how, and we don't know why."*

Thirty years of experience — and two mysteries. So I did what any mechanic with a
laptop would do.

> **Why the edits:** "six times" is real and lands harder than "two, three times"
> (the widest part runs from 0.1× to 6.7× its target; fleet max is 24×). "For
> *most* of them" sets up the reveal on Slide 12 that a *few* ARE claimable.

---

## SLIDE 11 — The Dataset Speaks  *(aligned)*

I pulled the record of every bladder that died in this shop. Four hundred and
twenty-nine of them. And I let the dataset talk.

*(click)* This is what 429 dead bladders look like on paper. Nothing. Just noise.

*(click)* But plot each one against **its own promise — the life we paid for** — and
the noise splits. Above the line, it did its job. Below the line, it broke its
promise. **Forty-seven percent broke their promise.**

*(click)* Label the clusters — and the early deaths aren't random. They have
*names*. One part almost always **leaks**. Another almost always **deforms**. Same
badness — but a tight, repeatable cluster is an *engineering* problem; a wide,
all-over-the-place scatter is a *process* problem.

*(click)* And they have *birthdays* — but here's the twist. The early deaths do
**not** line up by when the parts were *delivered*. They line up by when we *pulled
them* — and one quarter, **mid-2024, half of everything we removed was premature.**
A bad shipment clusters by arrival. This clustered by *plant time*. Different clock,
different suspect.

Two findings. **One:** it's not one killer — roughly **half the story is the
manufacturer, half is us.** Deformation? About **eighty percent our own operation.**
Leaks? About **seventy percent the manufacturer's part — the design and the incoming
quality.** **Two:** premature failures cluster by *removal* time, not *delivery*
time — which points the finger at our own floor, not a bad lot.

> **Why the edits:** "against its own promise" is the normalization your whole story
> rests on — it lets a mechanic and a CEO read the same chart. "Seventy percent the
> manufacturer's part (design + incoming quality)" replaces "incoming lot" because
> the batch/lot component is only ~13% — calling it all "lot" is the one number a
> manufacturer rep could attack. Naming the mid-2024 quarter (50% premature) makes
> the "two clocks" point concrete.

---

## SLIDE 12 — The Council + Cards #1 & #2  *(aligned)*

So I brought these two graphs to one table — design team, setters, BEU. And one by
one, the experts raised their hands.

*"That leak pattern? That's real — that's the manufacturer's part. And for two of
them, it IS a bad lot — we finally have the evidence to claim it."*

*"That slow death? There's a 2007 reference — the bladder must fully deflate between
cycles. And some operators… don't wait."*

My data didn't replace their thirty years of experience. It gave their experience
*evidence* — and it handed us two parts we can take straight back to France with a
number attached.

Now — cards up! Which two actions fix this? …*(five seconds — then reveal)*

**Card one — standardize the human.** Work instruction, operator training — then we
locked it into the machine itself. Recipe changed, PLC parameters locked. The right
way became the *only* way. *(This is the fix for the 80%-us deformation.)*

**Card two — redesign the part.** We opened a direct line to the manufacturer in
France — into the annual VSM, with central running a monthly design loop. *(This is
the fix for the 70%-manufacturer leaks — including the two claimable parts.)*

Two problems. Two graphs. Two actions. Remember that rhythm.

> **Why the edits:** your finding gives you a *concrete* win the original script
> throws away — **two parts (the 10″ turnup and the 15″ turnup) show a genuine
> bad-lot signal you can claim.** One honesty guard: the 15″ turnup's signal is
> partly one of *our* machines (it dies fast on one press), so lead the France claim
> with the **10″ turnup** — the clean one — and check the 15″ against the machine
> first. Keeping that nuance in your back pocket protects you in Q&A.

---

## SLIDE 16 — the gain, with a formula you can defend

Your lock list flags 5M/yr vs your 2–3M estimate. Here's a formula that survives a
hostile question, built straight from the lifetime data:

> **Gain = (cycles below target on fixable parts) ÷ (avg target) × (unit cost).**
> Every under-target bladder died some fraction of its promise early. Sum that
> wasted fraction across the fixable parts, value it at the bladder's price.

From the data: the three under-target parts (turnup 8″, 15″, 21″) carry **~35
bladder-equivalents of wasted life per the record**, and the fleet ~74. At an
**assumed ฿30,000/bladder** that is **≈฿1.05M focused / ≈฿2.2M fleet** of
*headroom* — the gap to target if the fix lands, **not money already saved.**

So your honest line: *"This is headroom, not a receipt. At our real bladder cost,
closing the gap on the three worst parts is worth roughly [lock ฿]. I'd rather hand
you a number I can defend than one I can't."* — Swap ฿30k for the true unit cost and
the number locks itself.

> If your real unit cost is ~฿60–70k, this formula lands right on your conservative
> **2–3M/yr** — so the two estimates reconcile once the price is locked.

---

## Bladder number-lock (add to your master sheet)
| Number | Locked value from the data |
|--------|----------------------------|
| Bladders analyzed | 429 records, **417** with a usable life |
| Broke their promise | **47%** (198 of 417) |
| Manufacturer vs us (overall) | **46% / 54%** |
| Deformation = us | **80%** |
| Leaks = manufacturer | **~72%** (design-led; ~13% is true lot) |
| Claimable bad-lot parts | **2** — turnup 10″ (clean), turnup 15″ (check machine first) |
| Worst removal quarter | **mid-2024, 50% premature** |
| Bladder headroom | **฿1.05M (3 parts) / ฿2.2M fleet** @ assumed ฿30k/unit |
