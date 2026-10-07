# Relation extraction over a gut microbiome corpus

Model-predicted relations between six entity types (Species, Disease, Chemical, Gene, CellLine,
Mutation), extracted from the full text of 52 open-access gut microbiome articles.

8,436 relations over 2,786 sentences and 3,060 distinct entity mentions.

> **Status: unvalidated system output.** These are predictions from a relation extraction model, not
> manually curated annotations. No gold standard exists for this corpus and no precision or recall
> figures are available. Every row should be treated as a hypothesis and checked against its source
> sentence, which is included in the data for that purpose. See
> [Limitations](docs/DATA_DICTIONARY.md#7-limitations) before use.

## Quick start

```bash
pip install -r requirements.txt

# optional: fill in PMID, DOI, title, journal, year for the 52 articles
python scripts/resolve_article_ids.py
```

```python
import pandas as pd

rel = pd.read_csv("data/derived/01_all_relations_enriched.csv")

# specific entities, directional relations only
clean = rel[~rel.entity_1_generic & ~rel.entity_2_generic
            & ~rel.abbrev_or_hypernym_pair & rel.relation_is_directional]

# species to metabolite, the most reliable layer
sc = clean[(clean.entity_1_type == "Species") & (clean.entity_2_type == "Chemical")]
```

## Repository layout

```
data/raw/predictions_output.xlsx   raw model output, unmodified
data/derived/                      9 CSVs, all rebuildable from the raw file
docs/DATA_DICTIONARY.md            column reference, relation label set, limitations
docs/ANNOTATION_GUIDE.md           how to fill in the validation sample
scripts/build_release.py           regenerates data/derived/ from data/raw/
scripts/resolve_article_ids.py     adds PMID and DOI to 08_articles.csv
```

## The derived files

| File | Rows | What it is |
|---|---|---|
| `01_all_relations_enriched.csv` | 8,436 | Everything. Entities and types in their own columns, plus quality flags. |
| `02_sentences.csv` | 2,786 | Unique source sentences, joins on `annotation_id`. |
| `03_entity_inventory.csv` | 3,060 | Distinct entity surface forms per type, with counts. Start here for ontology mapping. |
| `04_filtered_specific_directional.csv` | 2,731 | Generic entities and abbreviation pairs removed, directional relations only. |
| `05_species_chemical_directional.csv` | 406 | Species to Chemical subset of 04. The soundest layer. |
| `06_microbe_microbe_candidates_UNVERIFIED.csv` | 58 | Species to Species subset of 04. **Not an interaction network**, see below. |
| `07_type_relation_counts.csv` | 268 | Counts per entity-type pair and relation. Useful for scoping. |
| `08_articles.csv` | 52 | Source articles. Identifier columns filled by the resolver script. |
| `09_validation_sample_TO_ANNOTATE.csv` | 176 | Stratified random sample with blank annotation columns. |

Filtering is expressed as boolean columns on file 01 rather than applied destructively, so files 04
to 06 are reproducible views and you can redefine them rather than trusting ours.

## Two things to read before analysing

**Species to Chemical is the layer that holds up.** Microbe to metabolite direction is genuinely
asserted in this literature and the claims are species-specific rather than genus-level. Examples:
*Collinsella aerofaciens* and fructoselysine-6-phosphate (PMC6801109), *Clostridium scindens* and
3-oxo-DCA (PMC7319900), *Eggerthella lenta* and digoxin (PMC5534341).

**The microbe-microbe file is not an interaction network.** Source sentences were read for six of
the 58 candidates and none asserted an interaction between the two taxa. In each case the organisms
appeared side by side for an unrelated reason: separate monocolonisation arms of one experiment, two
taxa independently associated with obesity, taxa reported in different ageing cohorts, or a table
dump. The dominant failure mode of this data is sentence co-occurrence being labelled as a relation.
If you want microbe-microbe relationships, deriving them from shared metabolites in file 05 is
likely to be sounder.

There is no condition or context column anywhere. Disease, model system and intervention can only be
recovered from `original_text`, and a disease mentioned in a sentence does not necessarily scope the
relation extracted from it.

## Suggested first step

`09_validation_sample_TO_ANNOTATE.csv` is 176 rows stratified over all 28 entity-type pairs, with
the source sentence and six blank judgement columns. Two annotators on this sample would yield a
per-type precision estimate in a few hours, which determines how much weight the remaining 8,260
rows can carry. See [docs/ANNOTATION_GUIDE.md](docs/ANNOTATION_GUIDE.md).

## Reproducing the derived files

```bash
python scripts/build_release.py
```

Deterministic. All nine files, including the `relation_id` hashes and the stratified sample, rebuild
byte-identically from the raw Excel file.

## Reuse and citation

The 52 source articles are open access from PubMed Central and remain under their own licences,
which have not been individually verified in this release. These derived annotations are shared for
research collaboration. Please get in touch before using them in a publication, so that the
validation status above is represented accurately and so that authorship or acknowledgement can be
agreed. See [CITATION.cff](CITATION.cff).
