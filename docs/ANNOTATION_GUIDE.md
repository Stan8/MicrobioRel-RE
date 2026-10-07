# Annotation guide for the validation sample

File: `data/derived/09_validation_sample_TO_ANNOTATE.csv`, 176 rows.

The purpose is a precision estimate per entity-type pair, not a complete gold standard. Judge only
what is in front of you: the two entity spans, the predicted relation, and the sentence in
`original_text`.

Work from the sentence alone. Do not consult the full article, and do not use background knowledge
about whether the claim is biologically true. The question is what this sentence asserts.

## Columns to fill

Use `1` for yes, `0` for no, and `?` when the sentence does not let you decide. Leave nothing blank.

**`annot_entity_1_correct` / `annot_entity_2_correct`**
Is the span a real entity of the type given in `entity_1_type`? Mark `0` if the span is not an
entity at all (`C for 30`, `for 5`, `to 7`), if it is a different type than stated (`gut` typed as
Gene, `inflammation` typed as Disease), or if the span is truncated or runs into neighbouring words.

**`annot_relation_asserted`**
Does the sentence assert some relationship between these two entities? Mark `0` when both are merely
mentioned, which is the most common error. Typical cases to mark `0`:

- both appear in a list of items sharing some property, with no claim linking them to each other
- each is linked to a third thing but not to the other
- they belong to different experimental arms or different cited studies
- the text is a table or figure dump with no grammatical relation

If this is `0`, set the remaining three columns to `0` and move on.

**`annot_relation_label_correct`**
Given that a relation is asserted, is the predicted label right? Judge at the level of the coarse
distinction: positive effect, negative effect, or unspecified association. Do not penalise
`affects` for being vague when the sentence is itself vague, but mark `0` if the sentence states a
direction of effect and the label contradicts it.

**`annot_direction_correct`**
Does `entity_1` play the role the relation implies, with `entity_2` as the target? For
`Faecalibacterium prausnitzii start butyrate`, correct means the sentence says the organism produces
the metabolite, not the reverse. Mark `0` if the roles are swapped. For symmetric labels
(`Interacts_with`, `Negative_correlation`, `Associated_with`) mark `?`.

**`annot_notes`**
Short free text. Worth recording: the correct label when you marked one wrong, and any recurring
error pattern you notice.

## Procedure

Two annotators independently, with no discussion during the pass. Then compute agreement, ideally
Cohen's kappa per column, and adjudicate only the disagreements. Report precision per entity-type
pair with the per-stratum counts alongside, since several strata have only 2 rows and their
estimates will be unusable on their own.

Expect roughly two to four hours per annotator.

## Reporting

What the collaboration needs out of this:

- precision per entity-type pair for `annot_relation_asserted`, which is the headline number
- precision per relation label
- inter-annotator agreement per column
- a short list of recurring error patterns

A precision figure below roughly 0.5 for a given entity-type pair means that stratum should not be
used without manual review of every row.
