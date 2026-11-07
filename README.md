# EthnoLens AI
### AI that preserves botanical and medicinal heritage

> **EthnoLens AI is a historical research and heritage-preservation platform. It does not provide medical advice, does not recommend treatments or dosages, and does not validate the effectiveness of historical remedies.**

---

## Project Status

*Updated 6 November 2026. This prototype was built during EthnoHack 2026; the table says honestly what works and what does not yet.*

| Part | Status | Details |
|---|---|---|
| Curious Cures ingestion | ✅ Works | 183 transcribed pages of MS Add. 9308 downloaded from CUDL, split into 221 recipes; 100 loaded into the database with source, folio, language and period |
| Record contract and database | ✅ Works | [`schema/record.json`](schema/record.json), SQLite schema, Pydantic models |
| API | ✅ Works | `GET /health`, `GET /records` (search and filters), `POST /documents` (text and images; PDFs need Poppler), `GET /plants/{scientific name}`, `GET /map`, `POST /ask` |
| OCR | ✅ Works | Tesseract on 25 BHL page scans: mean character error rate **2.7%** (about 1.2% on prose pages, 38% on a two-column contents page) |
| Albanian local names | ✅ Works | 100 names for 98 species from Mustafa et al. (2012), joined to records through GBIF accepted names (7 outdated names in the article resolved, e.g. *Matricaria recutita* → *M. chamomilla*) |
| Streamlit frontend | ✅ Works | Four pages (Scan & Discover, Archive, EthnoMap, Ask) on the live API, no mock data; the full flow (upload → records → archive → map → Ask) tested end to end 3 times with text, image and PDF uploads; the API's reason is shown when an upload fails or extraction is skipped |
| LLM extraction | ✅ Implemented | OpenAI `gpt-4o-mini` in JSON mode; every record is validated against the contract, with one retry on an invalid response; needs an API key |
| One-command rebuild | ✅ Works | `python -m pipeline.rebuild` builds the database from zero and keeps extracted records |
| GBIF mapping | ✅ Works | `pipeline/taxonomy.py`: high only for an exact species-level match; spelling variants are medium; genus-only, no match, or a near-miss that lands on a synonym stay *candidate* |
| Ask EthnoLens (RAG) | ✅ Works | Cites a passage only if it contains a word of the question or the plant's historical spelling (found from its English or Albanian name); otherwise "no data". Chroma orders the matches. Personal medical questions refused (15/15 in `eval.rag_smoke`, English and Albanian); without an API key it returns the cited passages |
| Evaluation on 50 annotated recipes | 🟡 In progress | 47 of 50 recipes currently annotated; `eval/metrics.py` reports precision, recall and F1 while excluding blank rows; 3 recipes remain to reach the target |
| Handwritten text recognition (HTR) | ❌ Not planned for the prototype | See [Roadmap](#11-roadmap) |

---

## 1. Overview

**EthnoLens AI** turns historical botanical and medicinal documents into an interactive, searchable digital archive.

For centuries, knowledge about plants, the properties attributed to them, and the ways they were prepared has been preserved in manuscripts, old books, traditional recipes and botanical works. Much of it remains hard to reach: it is written in historical languages and spellings, stored in formats that are difficult to search, and scattered across collections.

EthnoLens AI connects this heritage with modern technology. Using OCR, NLP and large language models, the platform reads historical documents and identifies:

- plant names as they appear in the original text,
- other ingredients,
- the plant parts used (leaf, root, seed, flower, bark…),
- traditional preparation methods (infusion, decoction, powder, ointment…),
- the uses described in the source.

It then organises everything into a structured database, where **every record keeps its source, the original passage and a confidence level.**

The initial regional focus is **Kosovo, Albania and the wider Balkans**.

---

## 2. The Problem

Researchers who work with historical plant knowledge typically have to:

- search manually through hundreds of scanned pages,
- interpret old terminology, spelling variants and languages (Latin, Middle English, old Albanian…),
- work out which modern plant a historical name refers to, often with no certain answer,
- keep track of exactly where each piece of information came from.

As a result, historical knowledge is hard to analyse systematically, compare across sources or connect to modern botany. Local plant names and regional traditions are especially at risk of being lost.

---

## 3. What Makes EthnoLens Different

| Principle | What it means in practice |
|---|---|
| **Evidence first** | Every extracted fact links to its source document, page and original passage. |
| **Honest uncertainty** | Every record carries an extraction confidence and a botanical-mapping confidence. Uncertain identifications are marked as *candidates* and are never shown as facts. |
| **Stated vs. inferred** | The platform distinguishes what the historical text *says* from what the AI or a botanical reference *infers*. |
| **Historical ↔ modern names** | Historical and local plant names are linked to current scientific names, so traditional names are preserved and changes over time stay visible. |
| **Grounded AI answers** | Ask EthnoLens answers only from documents in the archive and cites its sources. If there is no source, it says so. |

---

## 4. Core Features

### 4.1 Scan & Discover
Upload a historical document as a PDF or image. EthnoLens:
1. runs OCR on printed pages, or uses the existing transcription when one is available. HTR for handwritten uploads is planned (see [Roadmap](#11-roadmap));
2. extracts plants, ingredients, parts, preparations and described uses;
3. highlights each extracted item **on the original page/passage**, so the user can check it immediately;
4. sends low-confidence items to a review queue.

### 4.2 Historical Archive
A searchable archive of every extracted record. Users can:
- search by historical name, local name or modern scientific name;
- filter by plant part, preparation, language, source, period or region;
- open a plant page that shows all of its historical mentions side by side;
- compare how different sources describe the same plant.

### 4.3 EthnoMap
An interactive map of botanical heritage by region. It shows local plant names from documented historical sources and ethnobotanical field records, **only where a documented source exists.** Each point indicates whether it comes from a historical document or a modern field study. The first version covers Kosovo, Albania and the Balkans.

### 4.4 Ask EthnoLens
An AI research assistant for questions about the archive, for example *"Which sources mention sage, and how was it prepared?"*

- It retrieves the relevant passages first (retrieval-augmented generation), then answers.
- Every answer includes **citations** to the documents and passages it used.
- If the archive has no evidence, it says so instead of guessing.
- It **refuses** to give medical advice, dosages or treatment recommendations.

### MVP priority
For the first prototype, the end-to-end path is **Scan & Discover → Historical Archive → Ask EthnoLens**. EthnoMap starts as a lightweight view of the records that already have a region, and grows as Balkan sources are added.

---

## 5. Example: From Manuscript to Archive Record

> *A real passage with the record written by hand to show the target format. It is not pipeline output and not a verified identification.*

[MS Add. 9308, f. 5v](https://cudl.lib.cam.ac.uk/view/MS-ADD-09308/24), a Middle English recipe book of the late 14th/early 15th century:

> *For þe coughe . tak sauge and rue and comyn and pouder of peper and seth hem to gedere in hony and mak a letuarie and vse þerof a sponful at euen . and an oþer at morwen .*

| Field | Value |
|---|---|
| Historical name (as written) | `sauge` |
| Normalised name | sage |
| Candidate scientific name | *Salvia officinalis* L. (*inferred*) |
| Mapping confidence | from the GBIF match: high only for an exact species-level match with confidence ≥ 90 |
| Albanian local name | Sherbela ([Mustafa et al. 2012](https://doi.org/10.1186/1746-4269-8-6)) |
| Plant part | *empty*: the passage does not say which part |
| Preparation | "seth hem to gedere in hony and mak a letuarie" |
| Described use | "For þe coughe" |
| Other ingredients | rue, comyn, pouder of peper, hony |
| Source | MS Add. 9308, f. 5v |
| Evidence type | plant: *stated*; scientific name: *inferred* |
| Review status | pending |

The plant part stays empty rather than guessed. The same plant page then collects other mentions of sage in the archive (for example ff. 4r and 24r–25r of the same manuscript) and shows where the Albanian name is documented on EthnoMap.

---

## 6. Data Sources

| Source | Role | Notes |
|---|---|---|
| [Curious Cures in Cambridge Libraries](https://www.lib.cam.ac.uk/curiouscures) ([CUDL collection](https://cudl.lib.cam.ac.uk/collections/medievalmedicalrecipes)) | Primary historical medical recipes | The collection has 190 manuscript volumes and 1,179 texts transcribed in full (mostly recipes and charms). **The prototype uses [MS Add. 9308](https://cudl.lib.cam.ac.uk/view/MS-ADD-09308)** (*Medical recipes and charms*, Middle English with some Latin, late 14th/early 15th century): 183 of its 194 pages have a diplomatic transcription. EthnoLens does not run HTR itself. |
| [Mustafa et al. (2012), *Medical ethnobotany of the Albanian Alps in Kosovo*](https://ethnobiomed.biomedcentral.com/articles/10.1186/1746-4269-8-6) | Albanian local names for EthnoMap | *Journal of Ethnobiology and Ethnomedicine* 8:6, CC BY 2.0. Fieldwork in 36 villages with 91 informants; Table 1 gives 98 species with their Albanian folk names. This is a **modern field study, not a historical document**, and is labelled as such. |
| [FineBooks BHL IMPACT GT](https://huggingface.co/datasets/finebooks/bhl-impact-gt) | OCR on printed pages and its evaluation | 2,165 [Biodiversity Heritage Library](https://www.biodiversitylibrary.org/) page scans from six natural-history books (1708–1913), with expert transcriptions. CC BY 3.0. The BHL website blocks automated downloads, so BHL pages are taken from this dataset. |
| [GBIF](https://www.gbif.org/) species match API (`https://api.gbif.org/v1/species/match`) | Taxonomic reference | Candidate scientific names and match confidence for historical and local names. |
| [HIMERA](https://www.nactem.ac.uk/himera/) | Optional, not used yet | Expert-annotated historical medical texts. Its annotations cover medical concepts rather than plant names, parts or preparations, so the main evaluation uses our own hand-annotated recipes instead. |

> **Licence of the Curious Cures transcriptions.** CUDL does not state a licence for the transcriptions (images: CC BY-NC 3.0; metadata: CC BY-NC-ND 3.0). The transcribed text is therefore **not included in this repository**: scripts download it into `data/raw/` (see [Getting Started](#16-getting-started)). The team will ask Cambridge University Library to confirm the licence.

---

## 7. System Architecture

```text
                 HISTORICAL & REGIONAL SOURCES
   Curious Cures | BHL (FineBooks) | Mustafa et al. | User uploads
                            |
                            v
                    DOCUMENT INGESTION
          PDFs, images, transcriptions, metadata
                            |
              +-------------+-------------+
              v                           v
         OCR (printed)       HTR (handwritten, planned)
              +-------------+-------------+
                            v
                   TEXT PREPROCESSING
     cleaning, segmentation, language detection,
          historical spelling preserved
                            |
                            v
                  AI / NLP EXTRACTION
   plants | ingredients | parts | preparation | uses
                            |
                            v
                  ENTITY NORMALISATION
           spelling variants, local names
                            |
                            v
                 TAXONOMIC MAPPING
            candidate scientific names (GBIF)
             + mapping confidence
                            |
                            v
           STRUCTURED DATABASE + VECTOR INDEX
          records, sources, passages, regions
                            |
     +-----------+----------+-----------+-------------+
     v           v                      v             v
 Scan &      Historical              EthnoMap       Ask
 Discover    Archive                                EthnoLens (RAG)
                            |
                            v
                HUMAN-IN-THE-LOOP REVIEW
          verify / correct / reject low-confidence items
```

---

## 8. Data Model

| Field | Description |
|---|---|
| Historical Plant Name | Name exactly as written in the source |
| Normalised Plant Name | Standardised historical name |
| Local / Vernacular Name | Regional name (e.g., Albanian), when documented |
| Candidate Scientific Name | Modern accepted name from the taxonomic reference |
| Plant Part | Leaf, root, seed, flower, bark, etc. |
| Described Use | The use as described in the source, quoted rather than paraphrased into a medical claim |
| Preparation Method | Infusion, decoction, powder, ointment, etc. |
| Other Ingredients | Additional ingredients in the recipe |
| Source | Book, manuscript or collection |
| Page / Folio Reference | Location of the passage |
| Original Passage | Supporting text |
| Language | Language of the source |
| Region | Geographic region, when documented |
| Period | Date or period of the source |
| Evidence Type | *Stated* in source or *inferred* by AI/reference |
| Extraction Confidence | Confidence in the AI/NLP extraction |
| Mapping Confidence | Confidence in the botanical identification |
| Review Status | Pending, verified or rejected |

A single plant can have many historical names, local names, sources and uses.

---

## 9. AI & NLP Components

| Technology | Purpose |
|---|---|
| OCR / HTR | Convert printed pages to text; HTR for handwritten pages is planned |
| Named Entity Recognition | Identify plants, ingredients, parts and preparations |
| Relation Extraction | Link plants to parts, preparations and described uses |
| Entity Linking | Map historical and local names to taxonomic references |
| Confidence Estimation | Score extraction and mapping uncertainty |
| Retrieval-Augmented Generation | Answer questions only from archived passages, with citations |
| Human-in-the-loop Review | Expert verification of uncertain records |

The prototype starts with existing models, LLM-based extraction and rule-based methods. Specialised or fine-tuned models will be considered based on evaluation results.

---

## 10. Evaluation & Demo Targets

| What | How it is measured |
|---|---|
| OCR quality | Character error rate against FineBooks ground truth. **Result: 2.7% mean CER on 25 pages** (`python -m pipeline.ocr`) |
| Entity extraction | Precision, recall and F1 on **50 Curious Cures recipes annotated by the team** (17/17/16 per team member; [`eval/annotations/`](eval/annotations/)). One set of 17 recipes (rows marked `[AI-assisted]`) was annotated with AI assistance rather than independently by a person, so metrics are also reported on the 33 recipes annotated by hand alone. A match is the same plant and part, ignoring case. |
| Relation extraction | Accuracy of plant–part–preparation–use links on the same hand-annotated sample |
| Taxonomic mapping | Manual review of a sample of historical → scientific name matches |
| Traceability | Share of records that link to the correct original passage (target: **100%**) |
| Grounded answers | Share of Ask EthnoLens answers that cite a supporting passage. Unsupported questions must be declined. |
| Usability | Time for a user to find all sources that mention a given plant (target: **< 1 minute**, compared with manual search) |

Current run on the local 100-recipe corpus: **174 records** have been extracted so far. All records are traceable to a stored passage (**100% traceability**) and 174/175 stored spans are valid (**99.43% span validity**). Across the 47 currently annotated passages, precision is **79.07%**, recall **54.40%**, and F1 **64.45%**; three more recipes are needed for the 50-recipe target. The Ask smoke suite currently passes **15/15 medical refusals**, **3/3 historical questions not refused**, and the no-data citation check.

**Demo targets:**
- 100 recipes from MS Add. 9308 processed end to end (loaded ✅, extraction in progress);
- 25 BHL pages processed through OCR ✅;
- 50 hand-annotated recipes as the extraction test set (47/50 complete);
- the Albanian Alps (Kosovo) field study integrated, with Albanian local names shown on EthnoMap (names ✅, map in progress);
- every record traceable to its original passage (enforced by the database: each record belongs to a passage).

---

## 11. Roadmap

1. **MVP:** Scan & Discover on transcriptions and printed pages, Historical Archive, Ask EthnoLens with citations, and a basic EthnoMap.
2. **Balkan expansion:** more Kosovo/Albania/Balkan sources and local names, and a richer EthnoMap.
3. **Handwriting:** HTR for user-uploaded handwritten documents.
4. **Collaboration:** review and annotation tools for researchers, students and cultural institutions.

---

## 12. Ethics, Licensing & Limitations

- **Not medical advice.** Described uses are historical records, not recommendations. The assistant refuses requests for treatment or dosage advice.
- **Uncertainty is shown, not hidden.** Ambiguous plant identifications remain *candidates* until they are reviewed.
- **Attribution.** Traditional and local knowledge is used only from published sources, which are credited on every record.
- **Licensing.** Each source is used according to its licence. Restricted material is linked, not redistributed.
- **Known challenges:** OCR/HTR errors, historical spelling and language variation, ambiguous names, taxonomic changes over time, incomplete or contradictory sources, and AI extraction errors.

---

## 13. Who It Is For & Why It Matters

- **Researchers** in ethnobotany, history of medicine and digital humanities
- **Students** learning about historical sources and botany
- **Libraries, museums and cultural institutions** that want their collections to be searchable
- **The public** interested in local plant heritage

EthnoLens AI is more than a digitisation tool. It turns historical plant knowledge into structured, connected and verifiable information, so that knowledge preserved in documents of the past does not remain locked in archives and becomes a living, searchable resource for everyone.

---

## 14. Tech Stack

| Layer | Technology |
|---|---|
| Backend / API | Python 3.11+, FastAPI, Pydantic |
| Frontend | Streamlit, one page per feature |
| Map | folium (Leaflet) + streamlit-folium |
| OCR | Tesseract via pytesseract + pdf2image; HTR planned |
| Extraction | LLM in JSON mode, validated against [`schema/record.json`](schema/record.json) |
| LLM | OpenAI `gpt-4o-mini` (JSON mode, temperature 0) |
| Database | SQLite ([`backend/app/db.py`](backend/app/db.py)) |
| Vector search (Ask EthnoLens) | Chroma |
| Taxonomy | GBIF species match API |

---

## 15. Repository Structure

```text
EthnoLens-AI/
├── backend/app/        # FastAPI app: main.py, models.py, db.py
├── pipeline/           # rebuild.py (one command), ingest.py, load_cudl.py, load_names.py,
│                       # ocr.py, extract.py, taxonomy.py, rag.py
├── frontend/           # Streamlit app: Scan & Discover, Archive, EthnoMap, Ask
├── schema/record.json  # The record contract shared by pipeline, API and frontend
├── data/raw/           # Downloaded sources (not in Git)
├── data/processed/     # Processed data, e.g. Albanian names CSV
├── eval/               # annotations/ and metrics.py
└── .env.example        # API keys template (the real .env is never committed)
```

---

## 16. Getting Started

### 1. Prerequisites

- **Python 3.11+**
- **Tesseract OCR**, for images and PDFs ([Windows installer](https://github.com/UB-Mannheim/tesseract/wiki), `brew install tesseract`, or `sudo apt install tesseract-ocr`). On Windows, if it is not on `PATH`, set `TESSERACT_CMD` in `.env`.
- **Poppler**, only for PDF uploads (`brew install poppler`, `sudo apt install poppler-utils`, or the Windows build from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)).

### 2. Install

```bash
git clone https://github.com/Jeta-Syla/EthnoLens-AI.git
cd EthnoLens-AI
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

For LLM extraction and generated answers, `.env` supports OpenAI-compatible providers. For the Groq key used by this project, set:

```env
LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1/chat/completions
LLM_MODEL=openai/gpt-oss-20b
LLM_API_KEY=...
```

Then run `python -m pipeline.extract`. Without a key, uploads still store text and Ask EthnoLens returns cited passages instead of generated answers.

### 3. Build the database (one command)

Some data cannot be redistributed, so it is **not in this repository**. One command downloads it from the original sources and builds `data/ethnolens.db` from zero (run from the repo root):

```bash
python -m pipeline.rebuild             # sources, recipes, Albanian names, GBIF mapping, Ask index
python -m pipeline.rebuild --extract   # also runs the LLM on recipes that have no records yet
```

A rebuild never throws extracted records away: it exports them to `data/raw/records_export.jsonl` first and restores them afterwards, and keeps the old database as `data/ethnolens.db.bak`. To share extractions without paying for them twice, copy a teammate's `records_export.jsonl` into your `data/raw/` and run the rebuild.

What the rebuild does, step by step:

| Data | In the repo? | How to get it |
|---|---|---|
| Curious Cures transcriptions (MS Add. 9308) | No, licence not stated | `python -m pipeline.ingest MS-ADD-09308` downloads 183 pages into `data/raw/cudl/` (about 3 minutes, 1 request per second) |
| Recipes in the database | No, built locally | `python -m pipeline.load_cudl MS-ADD-09308` splits the pages into recipes and loads 100 into `data/ethnolens.db` |
| Albanian local names | Yes: [`data/processed/albanian_names.csv`](data/processed/albanian_names.csv) (CC BY 2.0) | `python -m pipeline.load_names` loads them into the database under GBIF accepted names. To rebuild the CSV from the article: `python -m pipeline.albanian_names` |
| Extracted records | No, they quote the transcriptions | `python -m pipeline.extract` (needs `LLM_API_KEY`), then `python -m pipeline.taxonomy` maps the scientific names with GBIF |
| Ask EthnoLens index | No, built locally | `pipeline.rag.index_passages()` indexes the passages in Chroma (`data/chroma/`) |
| BHL page scans for OCR | No, downloaded on demand | `python -m pipeline.ocr` OCRs 25 pages from FineBooks and reports the CER (not part of the rebuild) |
| Recipe texts for annotation | No | `python -m eval.make_annotation_sets` writes them to `data/raw/annotation/` (not part of the rebuild) |

### 4. Run

```bash
uvicorn backend.app.main:app --reload    # API, docs at http://localhost:8000/docs
streamlit run frontend/Home.py           # frontend, in a second terminal
```

### 5. Evaluate

```bash
python -m eval.metrics                   # precision, recall, F1 on the annotated recipes
python -m eval.metrics --human-only      # only the recipes annotated by hand (no [AI-assisted] note)
python -m eval.rag_smoke                 # medical questions refused, no-data questions cite nothing (no API key needed)
python -m pipeline.ocr                   # OCR character error rate on 25 BHL pages
```

### Git workflow

| Branch | Owner | Scope |
|---|---|---|
| `main` | everyone | Working, demo-ready code only; merged from the branches below |
| `data` | Dafina | Sources, OCR, database, GBIF mapping, API |
| `ai` | Erëza | Extraction prompt, confidence, RAG, evaluation |
| `ui` | Jeta | Streamlit frontend |

- Pull `main` into your branch before starting work each day.
- `.env` and `data/raw/` are never committed.
- Any change to `schema/record.json` is announced to the whole team before it is made.

---

## 17. Team

- **Dafina Keqmezi**: data sources, OCR, database and API
- **Erëza Ismajli**: AI extraction, Ask EthnoLens and evaluation
- **Jeta Syla**: frontend and presentation

---

## 18. License

The code is released under the [MIT License](LICENSE). The data keeps its own licence: Mustafa et al. (2012) is CC BY 2.0, FineBooks BHL IMPACT is CC BY 3.0, and the Curious Cures transcriptions are not redistributed here (see [Data Sources](#6-data-sources)).

---

**Project:** EthnoLens AI
**Track:** Track 1: Historical Knowledge to Structured Knowledge
**Core concept:** Historical documents → OCR → AI/NLP extraction → Taxonomic mapping → Searchable archive, map & grounded assistant
