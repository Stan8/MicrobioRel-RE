# MicrobioRel-RE: model predictions over a gut microbiome corpus

Relations between six entity types (Species, Disease, Chemical, Gene, CellLine, Mutation) predicted
by the MicrobioRel relation extraction model over the full text of 52 open-access gut microbiome
articles.

8,436 predicted relations across 2,786 passages and 3,060 distinct entity mentions.

This is the **prediction** side of the MicrobioRel project. The annotated corpus, annotation
guidelines and training code live in a separate repository.

| | |
|---|---|
| Preprint | [MicrobioRel: A Manually Annotated Dataset for Microbiome Relation Extraction](https://www.biorxiv.org/content/10.1101/2025.08.03.666357v1.full), bioRxiv 2025.08.03.666357 |
| Annotated corpus, guidelines, training code | [Stan8/MicrobioRel](https://github.com/Stan8/MicrobioRel) |
| This repository | Model predictions on 52 unseen articles, enriched for downstream analysis |

## What is and is not validated

The underlying model is evaluated in the preprint: PubMedBERT reaches an F1 of about 71% on the
held-out MicrobioRel test split, ahead of BioBART at 64%, Random Forest at 44% and SVM at 24%.
Inter-annotator agreement on the gold corpus was about 51% F1 on exact triplets and about 78% when
scoring only the participating entities.

What that leaves open for **this** repository:

- The 71% F1 is in-domain, on the test split of the annotated corpus. These 52 articles are new
  documents, so that figure is an upper expectation rather than a measurement here.
- No row in this repository has been manually checked. There is no per-row confidence score.
- The 51% versus 78% agreement gap in the gold corpus says that even expert annotators concur on
  *which entities are related* far more than on *which relation label applies*. That gap is
  reproduced in the predictions, where 3,289 of 8,436 rows had more than one candidate label. Treat
  entity pairs as the more reliable signal and relation labels as the weaker one.

A stratified sample for validating this prediction set is provided, see
[Validation](#suggested-first-step-validation).

## Two independent error sources

Errors here come from two stages, and separating them matters because they call for different
filters.

**Stage 1, entity recognition, which was automatic.** Entity spans and types in these 52 articles
were produced by an automatic NER step, not by hand. The gold corpus behind the model was manually
annotated, so the relation model was trained on clean entities and is applied here to noisy ones.
That is ordinary error propagation in a pipeline, and it is the origin of the typing problems:
`gut` is tagged as a Gene 607 times, making it the single most frequent Gene span in the data, and
`age`, `16S`, `ASV`, `muL`, `muM`, `NAFLD`, `MTX` and a number of figure labels and version strings
are tagged as Genes too. On a conservative hand-checked list of 40 such spans, **986 rows, 36% of
all Gene-involving relations, contain at least one clearly mistyped entity.** Most Mutation spans
are isotope labels and incubation conditions (`U-13C`, `A to C`, `C for 30`) rather than variants.

This is flagged as data: `data/reference/suspect_entity_spans.csv` holds the list with a reason per
span, and `entity_1_type_suspect`, `entity_2_type_suspect` and `any_entity_type_suspect` mark the
affected rows in file 01. Four further spans (`kit`, `clock`, `insulin`, `HPRT`) are real gene
symbols that are mostly used in another sense here; those are marked `entity_*_type_ambiguous`
rather than suspect, 198 rows, and left for you to judge. The list is conservative and certainly
incomplete, so extend it rather than treat it as exhaustive.

**Stage 2, relation classification,** which labels pairs of whatever entities stage 1 supplied, with
very uneven training support across entity-type pairs. That is the next section.

A consequence worth keeping in mind: the predicted-to-gold ratios below are driven substantially by
how many candidate pairs stage 1 generated, not only by the relation model's behaviour. Gene spans
being over-tagged produces a large number of Gene-containing pairs that the relation model then has
to label, so a ratio of 121 for `Gene-Chemical` reflects entity supply at least as much as it
reflects extrapolation.

## Training support: which tiers to trust

The gold corpus contains 2,494 annotated relations, distributed very unevenly across entity-type
pairs. Comparing that distribution against what the model predicted here is the single most useful
guide to reliability, and it is shipped as data rather than advice:
`data/derived/10_training_support_by_type_pair.csv`, with `support_tier` and
`gold_annotated_for_type_pair` also attached to every row of file 01.

| Entity-type pair | Predicted here | Gold annotations | Ratio |
|---|---|---|---|
| Species-Disease | 1,492 | 339 | 4.4 |
| Species-Chemical | 1,476 | 167 | 8.8 |
| **Gene-Species** | **894** | **9** | **99** |
| **Gene-Chemical** | **725** | **6** | **121** |
| Chemical-Chemical | 670 | 204 | 3.3 |
| Chemical-Disease | 619 | 272 | 2.3 |
| Species-Species | 580 | 229 | 2.5 |
| **Gene-Disease** | **577** | **16** | **36** |
| Disease-Disease | 411 | 291 | 1.4 |
| **Gene-Gene** | **405** | **8** | **51** |
| Chemical-Mutation | 37 | 0 | no support |
| Species-Mutation | 30 | 0 | no support |
| Gene-Mutation | 22 | 0 | no support |

Summary: 5,602 rows sit in adequately supported type pairs, 2,724 rows in pairs with fewer than 20
gold annotations, and 89 rows in pairs with none at all.

**The Gene tier is the main caution, and it is hit from both sides.** Roughly 2,600 Gene-involving
relations were predicted from fewer than 50 gold examples, and 36% of those rows also contain a
clearly mistyped entity from the automatic NER step. **The Mutation tier has no relation-level
training support at all**, and its spans are mostly not mutations either; the
`mutation_looks_valid` column flags the 49 of 114 mentions in plausible variant notation
(rsIDs and protein substitutions).

The reverse also happens. CellLine pairs are substantially under-predicted relative to their gold
support: `CellLine-Species` has 79 gold annotations and zero predictions here,
`Chemical-Species` has 181 gold annotations and 5 predictions. Absence in this file is therefore not
evidence of absence in the articles.

## Direction

The gold schema is explicitly directional: annotations record `from_entity` to `to_entity` with
character offsets, and both orders of a type pair are annotated separately and substantially
(`Species-Disease` 339, `Disease-Species` 260).

The predictions do not preserve that balance. `Species-Disease` outnumbers `Disease-Species` here by
1,492 to 65, and `Species-Chemical` outnumbers `Chemical-Species` by 1,476 to 5, against gold ratios
near 1.3 and 0.9 respectively. The model appears to collapse direction toward one canonical order.
`entity_1` to `entity_2` therefore carries the schema's intended direction but should not be relied
on without checking the passage. Note also that this prediction output has no character offsets,
unlike the gold data.

## Quick start

```bash
pip install -r requirements.txt

# optional: fill in PMID, DOI, title, journal, year for the 52 articles
python scripts/resolve_article_ids.py
```

```python
import pandas as pd

rel = pd.read_csv("data/derived/01_all_relations_enriched.csv")

# specific entities, directional relations, adequately supported type pairs only
clean = rel[~rel.entity_1_generic & ~rel.entity_2_generic
            & ~rel.abbrev_or_hypernym_pair
            & ~rel.any_entity_type_suspect          # automatic NER type errors
            & rel.relation_is_directional
            & (rel.support_tier == "supported")]

# species to metabolite, the soundest layer
sc = clean[(clean.entity_1_type == "Species") & (clean.entity_2_type == "Chemical")]
```

## Repository layout

```
data/raw/predictions_output.xlsx   raw model output, unmodified
data/derived/                      10 CSVs, all rebuildable from the raw file
data/reference/                    gold training counts, and suspect entity spans
docs/DATA_DICTIONARY.md            column reference, relation label set, limitations
docs/VALIDATION_PROTOCOL.md        how to annotate the validation sample
scripts/build_release.py           regenerates data/derived/
scripts/resolve_article_ids.py     adds PMID and DOI to 08_articles.csv
```

## The derived files

| File | Rows | What it is |
|---|---|---|
| `01_all_relations_enriched.csv` | 8,436 | Everything. Entities and types in their own columns, plus quality and support flags. |
| `02_sentences.csv` | 2,786 | Unique source passages, joins on `annotation_id`. |
| `03_entity_inventory.csv` | 3,060 | Distinct entity surface forms per type, with counts. Start here for ontology mapping. |
| `04_filtered_specific_directional.csv` | 2,599 | Generic entities, abbreviation pairs and NER-suspect spans removed, directional relations only. |
| `05_species_chemical_directional.csv` | 406 | Species to Chemical subset of 04. The soundest layer. |
| `06_microbe_microbe_candidates_UNVERIFIED.csv` | 58 | Species to Species subset of 04. **Not an interaction network**, see below. |
| `07_type_relation_counts.csv` | 268 | Counts per entity-type pair and relation. |
| `08_articles.csv` | 52 | Source articles. Identifier columns filled by the resolver script. |
| `09_validation_sample_TO_ANNOTATE.csv` | 176 | Stratified random sample with blank annotation columns. |
| `10_training_support_by_type_pair.csv` | 31 | Predicted volume against gold training support. Read this before trusting any tier. |

Filtering is expressed as boolean columns on file 01 rather than applied destructively, so files 04
to 06 are reproducible views you can redefine rather than trust.

## Relation labels

The gold schema defines 22 relation types. This prediction set uses 18 of them. The four absent
(`complicates`, `presence`, `reveals`, `stop`) are precisely the four rarest in the training data,
with 7, 6, 5 and 4 examples respectively, so their absence is expected rather than meaningful.

`affects` is the catch-all and accounts for 1,868 rows. For most analyses we suggest collapsing to
three classes: positive effect, negative effect, unspecified association. Label definitions and the
disambiguation decision tree are in the sibling repository, under
[`docs/`](https://github.com/Stan8/MicrobioRel/tree/main/docs).

## Two things to read before analysing

**Species to Chemical is the layer that holds up.** Microbe to metabolite direction is genuinely
asserted in this literature, the claims are species-specific rather than genus-level, and the type
pair has adequate gold support. Examples: *Collinsella aerofaciens* and fructoselysine-6-phosphate
(PMC6801109), *Clostridium scindens* and 3-oxo-DCA (PMC7319900), *Eggerthella lenta* and digoxin
(PMC5534341).

**The microbe-microbe file is not an interaction network.** Source passages were read for six of the
58 candidates and none asserted an interaction between the two taxa. In each case the organisms
appeared side by side for an unrelated reason: separate monocolonisation arms of one experiment, two
taxa independently associated with obesity, taxa reported in different ageing cohorts, or a table
dump. Note that `Species-Species` is a well-supported type pair with 229 gold annotations, so this
is not a training-data gap; the gold `Species-Species` relations are heavily taxonomic (`part_of`),
and 306 of the 580 predicted here are indeed `part_of`, which is the part the model learned. The
directional labels on that pair are the extrapolation. If you want microbe-microbe relationships,
deriving them from shared metabolites in file 05 is likely to be sounder.

There is no condition or context column anywhere. Disease, model system and intervention can only be
recovered from `original_text`, and a disease mentioned in a passage does not necessarily scope the
relation extracted from it.

## Suggested first step: validation

`09_validation_sample_TO_ANNOTATE.csv` is 176 rows stratified over all 28 entity-type pairs, with
the source passage and six blank judgement columns. Two annotators would yield a per-tier precision
estimate in a few hours, which would turn the `support_tier` grouping above from a plausible proxy
into a measured one. See [docs/VALIDATION_PROTOCOL.md](docs/VALIDATION_PROTOCOL.md), which defers to
the project's own annotation guidelines for label definitions.

## Reproducing the derived files

```bash
python scripts/build_release.py
```

Deterministic. All ten files, including the `relation_id` hashes and the stratified sample, rebuild
byte-identically from the raw Excel file plus the two reference tables in `data/reference/`.

## Citation and reuse

Please cite the preprint. See [CITATION.cff](CITATION.cff).

The 52 source articles are open access from PubMed Central and remain under their own licences,
which have not been individually verified in this release. These derived predictions are shared for
research collaboration. Please get in touch before using them in a publication, so that the
validation status above is represented accurately and so that authorship or acknowledgement can be
agreed.
