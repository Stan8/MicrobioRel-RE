# Biomedical relation extraction output: gut microbiome corpus

Model-predicted relations between six entity types (Species, Disease, Chemical, Gene, CellLine,
Mutation), extracted from the full text of 52 open-access gut-microbiome articles.

**Status: unvalidated predictions, over automatically recognised entities.** These are outputs of
the MicrobioRel relation extraction model applied to entities found by an automatic NER step, not
manual annotations at either stage. The model itself is evaluated in the preprint (PubMedBERT, about 71%
F1 on the held-out MicrobioRel test split), but no row in *this* prediction set has been manually
checked, and these 52 articles are documents the model had not seen. Treat every row as a hypothesis
to be checked against the source passage, which is included for that purpose. Please read the
Limitations section before use.

Provenance:

- Preprint: *MicrobioRel: A Manually Annotated Dataset for Microbiome Relation Extraction*,
  bioRxiv 2025.08.03.666357, <https://www.biorxiv.org/content/10.1101/2025.08.03.666357v1.full>
- Annotated corpus, annotation guidelines, decision tree and training code:
  <https://github.com/Stan8/MicrobioRel>
- This repository: <https://github.com/Stan8/MicrobioRel-RE>

Contact: Oumaima (LS2N, Nantes Université).

---

## 1. Contents

| File | Rows | Description |
|---|---|---|
| `01_all_relations_enriched.csv` | 8,436 | Complete output, one row per predicted relation, with entities and types split into their own columns. |
| `02_sentences.csv` | 2,786 | Unique source sentences, joinable on `annotation_id`. |
| `03_entity_inventory.csv` | 3,060 | Every distinct entity surface form per type, with occurrence counts. Use this for ontology mapping. |
| `04_filtered_specific_directional.csv` | 2,731 | Subset of 01 with generic entities and abbreviation pairs removed, directional relations only. |
| `05_species_chemical_directional.csv` | 406 | Species to Chemical subset of 04. The most reliable layer, see Section 4. |
| `06_microbe_microbe_candidates_UNVERIFIED.csv` | 58 | Species to Species subset of 04. See the warning in Section 4. |
| `07_type_relation_counts.csv` | 268 | Counts per (entity_1_type, entity_2_type, relation). Useful for scoping before you dig in. |
| `08_articles.csv` | 52 | Source articles. PMID, DOI, title, journal and year are empty, see Section 5. |
| `09_validation_sample_TO_ANNOTATE.csv` | 176 | Stratified random sample with blank annotation columns, see Section 6. |
| `10_training_support_by_type_pair.csv` | 31 | Predicted volume against gold training support per entity-type pair. See Section 4. |
| `data/reference/gold_support_by_type_pair.csv` | 28 | Gold annotation counts, derived from the MicrobioRel corpus. Input to the build. |
| `data/reference/suspect_entity_spans.csv` | 44 | Hand-checked spans mistyped by the automatic NER step, with a reason each. Input to the build. |
| `resolve_article_ids.py` | | Fills in the empty columns of `08_articles.csv` from Europe PMC. |

All files except `02` and `08` keep `PMC` and `original_text`, so each row can be read in context
without a join.

## 2. Column dictionary (files 01, 04, 05, 06)

| Column | Meaning |
|---|---|
| `relation_id` | Stable identifier, SHA1 over PMC, sentence, both entities and the relation. Use it to reference rows back to us. |
| `PMC` | PubMed Central identifier of the source article. |
| `annotation_id` | Source sentence identifier, joins to `02_sentences.csv`. |
| `entity_1`, `entity_2` | Entity surface forms, exactly as they appear in the text. |
| `entity_1_type`, `entity_2_type` | One of Species, Disease, Chemical, Gene, CellLine, Mutation. |
| `relation` | Predicted relation label, 18 values, see Section 3. |
| `entity_1_norm`, `entity_2_norm` | Lowercased, punctuation-stripped, with `spp.`, `subsp.`, `strain`, `serovar` removed. String normalisation only, **not** ontology grounding. |
| `tuple`, `tuple_type` | Original columns from the model output, kept for traceability. |
| `candidate_labels` | All relation labels the model considered for this pair. |
| `n_candidate_labels` | Length of `candidate_labels`. |
| `label_ambiguous` | True when `n_candidate_labels` > 1. True for 3,289 of 8,436 rows. |
| `relation_is_directional` | True for labels that imply an asymmetric effect. 5,379 rows. |
| `relation_is_structural` | True for containment or carriage labels rather than interactions. 2,301 rows. |
| `entity_1_generic`, `entity_2_generic` | True when the entity is a non-specific term such as `mice`, `patients`, `gut microbiome`, `inflammation`. True on at least one side for 4,060 rows. |
| `entity_1_type_suspect`, `entity_2_type_suspect` | True when the span is on the hand-checked list of clear NER type errors (`gut` as Gene, `muL` as Gene, figure labels, version strings). |
| `any_entity_type_suspect` | True when either side is suspect. 986 rows, 12% of the file, and 36% of Gene-involving rows. |
| `entity_1_type_ambiguous`, `entity_2_type_ambiguous` | True for real gene symbols used mostly in another sense here (`kit`, `clock`, `insulin`, `HPRT`). 198 rows. Your call, not flagged as errors. |
| `abbrev_or_hypernym_pair` | True when the two entities are the same concept at different granularity, for example `B. longum` and `Bifidobacterium`, or `AD` and `Alzheimer's disease`. 585 rows. |
| `mutation_looks_valid` | For rows involving a Mutation entity only. True for rsIDs and protein variant notation, False otherwise. 48 of 106 Mutation rows are True. |
| `pairs_from_same_sentence` | How many relations were extracted from this sentence. High values indicate dense co-mention. |
| `n_supporting_sentences` | How many distinct sentences yield this same normalised triple. 1,687 rows have more than one. |
| `entity_type_pair` | `entity_1_type` and `entity_2_type` joined, the key for the support table. |
| `gold_annotated_for_type_pair` | Number of annotations for this ordered type pair in the MicrobioRel gold corpus (2,494 relations total). |
| `support_tier` | `supported` (80 or more gold), `weak (<80 gold)`, `very weak (<20 gold)`, `NO training support`. 5,602 / 21 / 2,724 / 89 rows respectively. |
| `original_text` | The source sentence or passage. |

## 3. Relation label set

Directional: `increase`, `decrease`, `start`, `causes`, `prevents`, `treats`, `improve`, `worsen`,
`affects`, `Interacts_with`, `Negative_correlation`.

Structural or non-interaction: `part_of`, `Location_of`, `experiences`, `possible`,
`Physically_related_to`.

Other: `Associated_with`, `Marker/Mechanism`.

The MicrobioRel schema defines 22 relation types. These 18 are the ones the model predicted here.
The four absent (`complicates`, `presence`, `reveals`, `stop`) are the four rarest in training, with
7, 6, 5 and 4 examples, so their absence is expected. Label definitions and the disambiguation
decision tree are in the sibling repository under `docs/`.

Some labels overlap in practice, and `affects` is the catch-all, accounting for 1,868 rows. We
suggest collapsing labels to three classes for most analyses: positive effect, negative effect,
unspecified association.

## 4. Which subsets are usable

**`05_species_chemical_directional.csv` is the layer we would start from.** Microbe to metabolite
direction is genuinely asserted in this literature, and the claims are species-specific rather than
genus-level. Examples: *Collinsella aerofaciens* and fructoselysine-6-phosphate (PMC6801109),
*Clostridium scindens* and 3-oxo-DCA (PMC7319900), *Eggerthella lenta* and digoxin (PMC5534341),
*Bacteroides thetaiotaomicron* and leucovorin (PMC7954989).

**`06_microbe_microbe_candidates_UNVERIFIED.csv` should not be used as an interaction network.** We
read the source sentences for six of these candidates and none of the six asserted an interaction
between the two taxa. In each case the two organisms were listed side by side for another reason:
separate monocolonisation arms of one experiment, two taxa independently associated with obesity,
two taxa reported in different ageing cohorts, or a table dump. The file is included for
completeness and because a minority may be genuine, but every row needs the sentence read before it
is believed. If you want microbe-microbe relationships, deriving them from shared metabolites in
file 05 is likely to be sounder than taking this file at face value.

There is no condition or context column anywhere in the data. Disease, model system and intervention
can only be recovered from `original_text`, and a disease mentioned in a sentence does not
necessarily scope the relation extracted from it.

## 5. Article identifiers

`08_articles.csv` lists the 52 source articles with PMC identifiers, per-article relation and
sentence counts, and a PMC URL. The `pmid`, `doi`, `title`, `journal` and `year` columns are empty
because the machine used to prepare this release had no access to the NCBI and Europe PMC APIs.
Run `resolve_article_ids.py` from the same folder to fill them in. It needs `requests` and `pandas`
and takes under a minute.

## 6. Suggested first step: validation

`09_validation_sample_TO_ANNOTATE.csv` is a random sample of 176 rows, stratified over all 28
entity-type pairs, with the source sentence and six blank annotation columns:

- `annot_entity_1_correct`, `annot_entity_2_correct`: is the span a real entity of the stated type?
- `annot_relation_asserted`: does the sentence actually assert a relation between the two, as opposed
  to merely mentioning both?
- `annot_relation_label_correct`: is the predicted label right?
- `annot_direction_correct`: does the argument order match the direction in the sentence?
- `annot_notes`: free text.

Two annotators on this sample would give a per-type precision estimate in a few hours, which would
tell everyone how much weight the rest of the 8,436 rows can carry. We would rather you had that
number than not, and we are glad to do the annotation jointly.

## 7. Limitations

1. **Predictions, not annotations.** The model scores about 71% F1 in-domain on the MicrobioRel test
   split, but nothing in this file has been manually checked and these are unseen documents. There
   is no per-row confidence score.
2. **Entities were recognised automatically.** Spans and types for these 52 articles come from an
   automatic NER step, whereas the gold corpus the model was trained on was annotated by hand. The
   relation model therefore sees cleaner entities in training than at inference, and entity errors
   propagate into every relation built on them. This, rather than the relation model itself, is the
   origin of the typing problems documented in item 4.
3. **Co-mention versus assertion.** The relation model labels entity pairs that co-occur in a
   passage. A label does not guarantee the passage asserts that relation. This is the dominant
   relation-level failure mode and it is severe in the Species-Species subset.
4. **Direction is defined but not reproduced faithfully.** The gold schema is directional
   (`from_entity` to `to_entity`, with character offsets) and annotates both orders substantially:
   `Species-Disease` 339 versus `Disease-Species` 260. The predictions collapse toward one order,
   1,492 versus 65 for that same pair and 1,476 versus 5 for `Species-Chemical` versus
   `Chemical-Species`. Direction carries the schema's intended meaning but should not be relied on
   without checking the passage. This output also has no character offsets, unlike the gold data.
5. **Entity typing errors from the automatic NER step.** `gut` is typed as a Gene in 607 mentions,
   the most frequent Gene span in the data. `age`, `16S`, `ASV`, `SIC`, `Hyp`, `NAFLD`, `MTX`,
   `muL`, `muM`, figure labels and version strings are also typed as Gene. On a conservative list
   of 40 such spans, 986 rows (36% of Gene-involving relations) carry at least one. Most Mutation
   spans are isotope labels or incubation conditions rather than variants, and
   `mutation_looks_valid` marks the 49 of 114 mentions in plausible variant notation.
   `inflammation`, `dysbiosis`, `hypothalamus` and `fitness` are typed as Disease. Filter with
   `any_entity_type_suspect`, and with `support_tier` for the separate relation-level problem.
6. **No ontology grounding.** There are no NCBI Taxonomy, MeSH, ChEBI or Entrez identifiers.
   `03_entity_inventory.csv` is provided so that mapping can be done once, on 3,060 surface forms,
   rather than on 8,436 rows.
7. **Abbreviations unresolved.** `AD` and `Alzheimer's disease`, `TMAO` and `trimethylamine N-oxide`
   are distinct entities and their counts do not aggregate.
8. **Domain-restricted corpus, and under-prediction in places.** All 52 articles concern the gut
   microbiome, with a bias toward IBD, colorectal cancer, cardiometabolic disease and the
   microbiota-gut-brain axis. Separately, some well-supported type pairs are barely predicted at
   all: `CellLine-Species` has 79 gold annotations and 0 predictions, `Chemical-Species` has 181 and
   5. Absence of a relation here is not evidence of absence in the articles, let alone the
   literature.
9. **Mixed text zones.** A small number of rows (41) come from table or figure dumps in the full text
   rather than running prose.

## 8. Reuse

The underlying articles are open access from PubMed Central and remain under their own licences.
These derived annotations are shared for research collaboration. We would appreciate being consulted
before the data is used in a publication, so that the validation status above is represented
accurately, and so that authorship or acknowledgement can be agreed.
