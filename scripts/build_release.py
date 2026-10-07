"""
Rebuild every file in data/derived/ from data/raw/predictions_output.xlsx.

    pip install -r requirements.txt
    python scripts/build_release.py

Deterministic: same input gives byte-identical output, including relation_id
hashes and the stratified validation sample (fixed seed 42).
"""
import pandas as pd, ast, re, hashlib, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/raw/predictions_output.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/derived"
os.makedirs(OUT, exist_ok=True)
d = pd.read_excel(SRC)

# ---------- 1. split tuple and tuple_type into explicit columns ----------
d['tuple_parsed']      = d['tuple'].apply(ast.literal_eval)
d['tuple_type_parsed'] = d['tuple_type'].apply(ast.literal_eval)
d['entity_1']      = [t[0] for t in d.tuple_parsed]
d['entity_2']      = [t[1] for t in d.tuple_parsed]
d['entity_1_type'] = [t[0] for t in d.tuple_type_parsed]
d['entity_2_type'] = [t[1] for t in d.tuple_type_parsed]
d['relation']      = d['predictions']
d['n_candidate_labels'] = d['tuple_count']
d['candidate_labels']   = d['possible_relation']

# ---------- 2. stable identifier ----------
def rid(r):
    k = f"{r.PMC}|{r.annotation_id}|{r.entity_1}|{r.entity_2}|{r.relation}"
    return 'R' + hashlib.sha1(k.encode()).hexdigest()[:10]
d['relation_id'] = d.apply(rid, axis=1)

# ---------- 3. normalisation for joining (NOT ontology grounding) ----------
def norm(s):
    s = str(s).lower().strip()
    s = re.sub(r'\b(spp|sp|subsp|strain|str|serovar)\b\.?', ' ', s)
    s = re.sub(r'[^a-z0-9\.\-\s/]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()
d['entity_1_norm'] = d.entity_1.map(norm)
d['entity_2_norm'] = d.entity_2.map(norm)

# ---------- 4. quality flags ----------
GENERIC = set(x.strip() for x in '''mice|mouse|human|humans|patients|patient|people|children|child|infant|infants|rats|rat|murine|participants|participant|mammalian|mammals|adults|women|men|adult|subjects|individuals|donor|donors|volunteers|cohort|host|animals|animal|control|controls|gut microbiome|microbiota|microbiome|gut microbiota|human microbiome|human gut microbiota|human gut microbiome|human oral microbiome|gut-microbiome|metagenome|metagenomes|gut metagenome|bacteria|bacterial|microbes|microbial|commensal|commensals|species|strain|strains|cells|cell|gut bacteria|intestinal microbiota|gut|age|16s|disease|diseases|inflammation|dysbiosis|infection|infected|cancer|tumor|tumour|death|fitness|toxicity|water|pbs|glucose|oxygen|diet|protein|proteins|metabolites|metabolite|nutrients|expression|stocks|biota|yeast|fungi|fungal|prion|transgenic|transgenic mice|respiratory|healthy|ctrl'''.split('|'))
d['entity_1_generic'] = d.entity_1_norm.isin(GENERIC)
d['entity_2_generic'] = d.entity_2_norm.isin(GENERIC)

def abbrev_pair(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return False
    if a == b or a in b or b in a: return True
    ini = lambda s: ''.join(w[0] for w in re.split(r'[\s\-]+', s) if w)
    return a.replace('s','') == ini(b).replace('s','') or b.replace('s','') == ini(a).replace('s','')
d['abbrev_or_hypernym_pair'] = [abbrev_pair(a, b) for a, b in zip(d.entity_1, d.entity_2)]

# relation-level flags
DIRECTIONAL = {'increase','decrease','start','prevents','treats','improve','worsen','causes',
               'Negative_correlation','affects','Interacts_with'}
STRUCTURAL  = {'part_of','Location_of','experiences','possible','Physically_related_to'}
d['relation_is_directional'] = d.relation.isin(DIRECTIONAL)
d['relation_is_structural']  = d.relation.isin(STRUCTURAL)
d['label_ambiguous']         = d.n_candidate_labels > 1

# entities mis-typed as Mutation (isotope labels, temperatures, incubation times)
BAD_MUT = re.compile(r'^(u-?\d*[cn]|[a-z] (to|for|at|in) \d|\(e\) of \d|\d+[a-z]?|[a-z]?\d+[a-z]?)$', re.I)
RSID    = re.compile(r'^rs\d+$', re.I)
PROTVAR = re.compile(r'^[a-z]\d{1,4}[a-z]$', re.I)
def mut_ok(e, t):
    if t != 'Mutation': return pd.NA
    k = str(e).strip()
    if RSID.match(k) or PROTVAR.match(k): return True
    return False
d['mutation_looks_valid'] = [
    mut_ok(e, t) if t == 'Mutation' else (mut_ok(e2, t2) if t2 == 'Mutation' else pd.NA)
    for e, t, e2, t2 in zip(d.entity_1, d.entity_1_type, d.entity_2, d.entity_2_type)]

# sentence-level co-mention density
dens = d.groupby('annotation_id').size()
d['pairs_from_same_sentence'] = d.annotation_id.map(dens)

# how many distinct sentences support this (entity_1, relation, entity_2)
sup = d.groupby(['entity_1_norm','relation','entity_2_norm']).annotation_id.nunique()
d['n_supporting_sentences'] = [sup.get((a,r,b), 1) for a,r,b in zip(d.entity_1_norm, d.relation, d.entity_2_norm)]

COLS = ['relation_id','PMC','annotation_id',
        'entity_1','entity_1_type','relation','entity_2','entity_2_type',
        'entity_1_norm','entity_2_norm',
        'tuple','tuple_type','candidate_labels','n_candidate_labels','label_ambiguous',
        'relation_is_directional','relation_is_structural',
        'entity_1_generic','entity_2_generic','abbrev_or_hypernym_pair',
        'mutation_looks_valid','pairs_from_same_sentence','n_supporting_sentences',
        'original_text']
main = d[COLS]
main.to_csv(f'{OUT}/01_all_relations_enriched.csv', index=False)
print('01_all_relations_enriched.csv', main.shape)

# ---------- 5. sentences table ----------
sent = d[['annotation_id','PMC','original_text']].drop_duplicates('annotation_id')
sent.to_csv(f'{OUT}/02_sentences.csv', index=False)
print('02_sentences.csv', sent.shape)

# ---------- 6. entity inventory ----------
rec = []
for e, t, n in zip(d.entity_1, d.entity_1_type, d.entity_1_norm): rec.append((t, e, n))
for e, t, n in zip(d.entity_2, d.entity_2_type, d.entity_2_norm): rec.append((t, e, n))
inv = pd.DataFrame(rec, columns=['entity_type','entity_surface_form','entity_norm'])
inv = (inv.groupby(['entity_type','entity_surface_form','entity_norm'])
          .size().reset_index(name='n_occurrences')
          .sort_values(['entity_type','n_occurrences'], ascending=[True, False]))
inv['is_generic'] = inv.entity_norm.isin(GENERIC)
inv.to_csv(f'{OUT}/03_entity_inventory.csv', index=False)
print('03_entity_inventory.csv', inv.shape)

# ---------- 7. filtered: specific + directional ----------
f = main[(~main.entity_1_generic) & (~main.entity_2_generic)
         & (~main.abbrev_or_hypernym_pair) & (main.relation_is_directional)]
f.to_csv(f'{OUT}/04_filtered_specific_directional.csv', index=False)
print('04_filtered_specific_directional.csv', f.shape)

# ---------- 8. species -> chemical ----------
sc = f[(f.entity_1_type == 'Species') & (f.entity_2_type == 'Chemical')]
sc.to_csv(f'{OUT}/05_species_chemical_directional.csv', index=False)
print('05_species_chemical_directional.csv', sc.shape)

# ---------- 9. microbe-microbe candidates ----------
mm = f[(f.entity_1_type == 'Species') & (f.entity_2_type == 'Species')]
mm.to_csv(f'{OUT}/06_microbe_microbe_candidates_UNVERIFIED.csv', index=False)
print('06_microbe_microbe_candidates_UNVERIFIED.csv', mm.shape)

# ---------- 10. per entity-type pair counts ----------
tc = (main.groupby(['entity_1_type','entity_2_type','relation']).size()
          .reset_index(name='n').sort_values('n', ascending=False))
tc.to_csv(f'{OUT}/07_type_relation_counts.csv', index=False)
print('07_type_relation_counts.csv', tc.shape)

# ---------- 11. article table (identifier columns filled by resolve_article_ids.py) ----------
art = (main.groupby('PMC')
           .agg(n_relations=('relation_id', 'count'), n_sentences=('annotation_id', 'nunique'))
           .reset_index())
art['pmc_url'] = 'https://www.ncbi.nlm.nih.gov/pmc/articles/' + art.PMC + '/'
for c in ['pmid', 'doi', 'title', 'journal', 'year']:
    art[c] = ''
art.to_csv(f'{OUT}/08_articles.csv', index=False)
print('08_articles.csv', art.shape)

# ---------- 12. stratified validation sample ----------
main = main.copy()
main['stratum'] = main.entity_1_type + '-' + main.entity_2_type
TARGET = 150
parts = []
for s, n in main.stratum.value_counts().items():
    g = main[main.stratum == s]
    k = min(len(g), max(2, int(round(TARGET * n / len(main)))))
    parts.append(g.sample(k, random_state=42))
val = pd.concat(parts).sample(frac=1, random_state=42).reset_index(drop=True)
val = val[['relation_id', 'PMC', 'entity_1', 'entity_1_type', 'relation',
           'entity_2', 'entity_2_type', 'candidate_labels', 'original_text']]
for c in ['annot_entity_1_correct', 'annot_entity_2_correct', 'annot_relation_asserted',
          'annot_relation_label_correct', 'annot_direction_correct', 'annot_notes']:
    val[c] = ''
val.to_csv(f'{OUT}/09_validation_sample_TO_ANNOTATE.csv', index=False)
print('09_validation_sample_TO_ANNOTATE.csv', val.shape)
