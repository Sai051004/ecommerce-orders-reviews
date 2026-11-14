# Sentiment Error Analysis (Part B1)

This note explains the results of comparing LLM-generated sentiment labels with reference
labels for the four reviews in [`data/reviews.json`](../data/reviews.json). The numbers come
from running `python -m src.sentiment_evaluation`.

## Results

| ID | Review | Reference | LLM | Correct |
|---|---|---|---|---|
| R1 | "Works fine but the battery died in a week." | mixed | positive | No |
| R2 | "Exactly what I needed, five stars!" | positive | positive | Yes |
| R3 | "Arrived broken, waste of money." | negative | negative | Yes |
| R4 | "It's okay, nothing special." | neutral | positive | No |

**Accuracy: 2 / 4 = 50%.**

Both errors share a pattern: the reviews are not clearly positive or negative, and in both
cases the LLM predicted **positive**. The LLM never predicted `mixed` or `neutral`.

## Misclassified reviews

### R1: mixed, predicted positive

> "Works fine but the battery died in a week."

- **"Works fine"** describes a positive experience: the product does its job.
- **"Battery died in a week"** describes a negative experience: a significant failure
  soon after purchase.
- The review therefore contains **conflicting sentiment** in a single sentence.
- The LLM appears to have **overemphasized the positive phrase** and ignored the complaint
  that follows "but".
- The reference label **`mixed`** captures both aspects, which is the most faithful
  description of the text.
- **This is a borderline case.** Under other annotation guidelines, the review could be
  labelled **negative**: a battery failing within a week is a serious defect, and many
  customers would weigh it more heavily than "works fine". Either way, `positive` is the
  least defensible label.

### R4: neutral, predicted positive

> "It's okay, nothing special."

- **"It's okay"** signals acceptance, not strong satisfaction.
- **"Nothing special"** suggests an average or slightly underwhelming experience.
- The reference label **`neutral`** is reasonable: the reviewer is neither pleased nor
  unhappy.
- The LLM may have read **"okay"** as a positive word in isolation.
- **This is a borderline case.** The line between *neutral* and *mildly positive* is
  subjective, and some annotators could reasonably call this review mildly positive.
  "Nothing special", however, pulls it back towards neutral.

## Correct predictions

- **R2**, "Exactly what I needed, five stars!", is **clearly positive**. It expresses
  satisfaction and gives the maximum rating. Reference and prediction agree.
- **R3**, "Arrived broken, waste of money.", is **clearly negative**. It reports a damaged
  product and regret about the purchase. Reference and prediction agree.

The LLM handled the unambiguous reviews correctly. Its errors are limited to the reviews
that require a judgement call.

## Limitations of this evaluation

1. **Only four reviews are available.** Each review changes accuracy by 25 percentage points.
2. **50% accuracy is not a reliable estimate of real-world performance.** The sample is far
   too small to draw conclusions about how the model would perform on new reviews.
3. **Sentiment labels are subjective.** Different people can read the same review
   differently, so the reference labels are not automatically correct. R1 and R4 show this.
4. **`mixed` and `neutral` are especially hard.** They sit between the clear positive and
   negative classes, and both errors occurred there.
5. **Annotation guidelines matter.** Clear definitions are needed for each label. For
   example: when does a complaint turn a review from `mixed` into `negative`, and does
   "okay" count as `neutral` or `positive`? Without these rules, both annotators and the
   LLM will be inconsistent.
6. **A larger, representative labelled dataset is needed.** Reliable evaluation would
   require many more reviews, covering all four labels, ideally labelled by more than one
   annotator so that disagreements can be measured.
