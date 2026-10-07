# MicrobioRel-RE

Relations predicted by the MicrobioRel model on 52 gut microbiome articles from PubMed Central.

- 8,436 predicted relations over 2,786 passages
- 6 entity types: Species, Disease, Chemical, Gene, CellLine, Mutation
- 18 relation labels
- Entities come from an automatic NER step. Relations come from the MicrobioRel model.
- No row has been manually checked.

Preprint: [MicrobioRel: A Manually Annotated Dataset for Microbiome Relation Extraction](https://www.biorxiv.org/content/10.1101/2025.08.03.666357v1.full) (bioRxiv 2025.08.03.666357)
Annotated corpus, guidelines, training code: [Stan8/MicrobioRel](https://github.com/Stan8/MicrobioRel)

## Files

| Path | Rows | Content |
|---|---|---|
| `data/raw/predictions_output.xlsx` | 8,436 | Model output, unmodified |
| `data/derived/01_all_relations_enriched.csv` | 8,436 | All relations, one row each, with entities, types and flag columns |
| `data/derived/02_sentences.csv` | 2,786 | Source passages, joined on `annotation_id` |
| `data/derived/03_entity_inventory.csv` | 3,060 | Distinct entity forms per type, with counts |
| `data/derived/04_filtered_specific_directional.csv` | 2,599 | Subset of 01: no generic entities, no abbreviation pairs, no flagged spans, directional labels only |
| `data/derived/05_species_chemical_directional.csv` | 406 | Species to Chemical rows of 04 |
| `data/derived/06_microbe_microbe_candidates_UNVERIFIED.csv` | 58 | Species to Species rows of 04 |
| `data/derived/07_type_relation_counts.csv` | 268 | Row counts per entity type pair and relation |
| `data/derived/08_articles.csv` | 52 | Source articles; PMID, DOI, title, journal and year are empty until the resolver script is run |
| `data/derived/09_validation_sample_TO_ANNOTATE.csv` | 176 | Random sample across all 28 type pairs, with blank annotation columns |
| `data/derived/10_training_support_by_type_pair.csv` | 31 | Predicted rows against gold annotations per type pair |
| `data/reference/gold_support_by_type_pair.csv` | 28 | Gold annotation counts per type pair, from the MicrobioRel corpus |
| `data/reference/suspect_entity_spans.csv` | 44 | Hand-checked spans with the wrong entity type, with a reason each |
| `docs/DATA_DICTIONARY.md` | | Column definitions and known limitations |
| `docs/VALIDATION_PROTOCOL.md` | | Instructions for filling in file 09 |
| `scripts/build_release.py` | | Rebuilds `data/derived/` from `data/raw/` and `data/reference/` |
| `scripts/resolve_article_ids.py` | | Fills the identifier columns of file 08 from Europe PMC |
| `CITATION.cff` | | Citation metadata |

Files 01, 04, 05 and 06 share the same 32 columns. Column definitions are in `docs/DATA_DICTIONARY.md`.

## Usage

```bash
pip install -r requirements.txt
python scripts/build_release.py          # rebuild data/derived/
python scripts/resolve_article_ids.py    # fill PMID and DOI in 08_articles.csv
```

```python
import pandas as pd
rel = pd.read_csv("data/derived/01_all_relations_enriched.csv")
```

## Licence

The source articles are open access on PubMed Central. Their individual licences have not been checked.
