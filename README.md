# EthnoLens AI
### AI that preserves botanical and medicinal heritage

> **EthnoLens AI is a historical research and heritage-preservation platform. It does not provide medical advice, does not recommend treatments or dosages, and does not validate the effectiveness of historical remedies.**

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

> *Illustrative example of the record format only. It is not a verified extraction or a historical finding.*

A Middle English recipe mentions **"sauge"**. EthnoLens creates the following record:

| Field | Value |
|---|---|
| Historical name (as written) | `sauge` |
| Normalised historical name | sage |
| Candidate scientific name | *Salvia officinalis* L. |
| Mapping confidence | High (common, well-attested name) |
| Albanian local name | sherebelë |
| Plant part | leaf |
| Preparation | `[as stated in passage]` |
| Described use | `[as stated in passage, quoted verbatim]` |
| Source | `[manuscript ID, folio]` |
| Original passage | `[exact transcribed text]` |
| Evidence type | Plant & part: *stated*; scientific name: *inferred* |
| Review status | Pending verification |

The same plant page then collects mentions from other manuscripts, from BHL botanical works and from Balkan ethnobotanical field records, and EthnoMap shows the regions where a local name is documented.

---

## 6. Data Sources

| Source | Role | Notes |
|---|---|---|
| [Curious Cures in Cambridge Libraries](https://www.lib.cam.ac.uk/curiouscures) ([CUDL collection](https://cudl.lib.cam.ac.uk/collections/medievalmedicalrecipes)) | Primary historical medical recipes | 190 manuscript volumes (186 listed on CUDL), 7,000+ pages and 7,738 identified texts in Latin and Middle English. **1,179 texts were transcribed in full** (mostly recipes and charms), and these are the demo corpus. The project did not transcribe every recipe. EthnoLens does not run HTR itself. |
| [Biodiversity Heritage Library](https://www.biodiversitylibrary.org/) ([HF dataset](https://huggingface.co/datasets/common-pile/biodiversity_heritage_library)) | Historical printed botanical literature | Printed pages and OCR text. Supplies historical terminology and botanical context. |
| [Mustafa et al. (2012), *Medical ethnobotany of the Albanian Alps in Kosovo*](https://ethnobiomed.biomedcentral.com/articles/10.1186/1746-4269-8-6) | Balkan ethnobotanical field record for EthnoMap | *Journal of Ethnobiology and Ethnomedicine* 8:6, open access (CC BY). Fieldwork in 36 villages with 91 informants, documenting 98 plant species and their Albanian local names. This is a **modern field study, not a historical document**, and is labelled as such. |
| [World Flora Online](https://www.worldfloraonline.org/) / [POWO](https://powo.science.kew.org/) / [GBIF Backbone](https://www.gbif.org/) | Taxonomic reference | Accepted scientific names and synonyms, used to map historical names to modern ones. |
| [HIMERA](https://www.nactem.ac.uk/himera/) | Secondary NLP evaluation | Expert-annotated historical medical texts. Its annotations focus on medical concepts (conditions, symptoms, etc.) rather than plant names, parts or preparations, so it is used only for the overlapping categories. |
| [FineBooks BHL IMPACT GT](https://huggingface.co/datasets/finebooks/bhl-impact-gt) | OCR evaluation | 2,165 page scans from six natural-history books (1708–1913), with expert transcriptions. CC BY 3.0. |

Before implementation, the team will verify the availability, format and **licence** of each source. Some digitised manuscript images have restrictions on reuse.

> **Critical dependency: Curious Cures transcriptions.**
> The demo, the main evaluation set and the example in Section 5 all depend on the 1,179 transcriptions being accessible from CUDL in a usable form (text/TEI export, or copyable per item), under a licence that allows this use. **Status: to be verified by the team.**
>
> If they are not accessible, this is a **change of demo plan**, not a silent fallback:
> - the primary corpus switches to BHL printed botanical works through OCR;
> - recipe-specific fields (preparation, other ingredients, described use) will often be empty, so the demo focuses on plant names, parts, historical terminology and taxonomic mapping;
> - the hand-annotated evaluation set is built from ~50 BHL pages instead;
> - the Section 5 example and the demo targets are updated to a BHL source.

---

## 7. System Architecture

```text
                 HISTORICAL & REGIONAL SOURCES
     Curious Cures | BHL | Balkan studies | User uploads
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
       candidate scientific names (WFO / POWO / GBIF)
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
| OCR quality | Character/word error rate against FineBooks ground truth |
| Entity extraction | **Primary:** precision, recall and F1 on a hand-annotated sample of **~50 transcribed Curious Cures recipes** (plants, parts, preparations, uses). **Secondary:** HIMERA, for the overlapping medical-concept categories only. |
| Relation extraction | Accuracy of plant–part–preparation–use links on the same hand-annotated sample |
| Taxonomic mapping | Manual review of a sample of historical → scientific name matches |
| Traceability | Share of records that link to the correct original passage (target: **100%**) |
| Grounded answers | Share of Ask EthnoLens answers that cite a supporting passage. Unsupported questions must be declined. |
| Usability | Time for a user to find all sources that mention a given plant (target: **< 1 minute**, compared with manual search) |

**Demo targets (to be confirmed by the team):**
- a curated subset of the 1,179 transcribed Curious Cures texts processed end to end;
- a selection of BHL pages processed through OCR;
- ~50 hand-annotated recipes as the extraction test set;
- the Albanian Alps (Kosovo) field study integrated, with Albanian local names shown on EthnoMap;
- every record traceable to its original passage.

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
| LLM | *To be decided* |
| Database | SQLite ([`backend/app/db.py`](backend/app/db.py)) |
| Vector search (Ask EthnoLens) | Chroma |
| Taxonomy | GBIF species match API |

---

## 15. Repository Structure

```text
EthnoLens-AI/
├── backend/app/        # FastAPI app: main.py, models.py, db.py
├── pipeline/           # ingest.py, ocr.py, extract.py, taxonomy.py, rag.py
├── frontend/           # Streamlit app: Scan & Discover, Archive, EthnoMap, Ask
├── schema/record.json  # The record contract shared by pipeline, API and frontend
├── data/raw/           # Downloaded sources (not in Git)
├── data/processed/     # Processed data, e.g. Albanian names CSV
├── eval/               # annotations/ and metrics.py
└── .env.example        # API keys template (the real .env is never committed)
```

---

## 16. Getting Started

> Full installation and run instructions will be added once the first prototype is available.

Create the local database:

```bash
python -m backend.app.db
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

- **Dafina Keqmezi**
- **Erëza Ismajli**
- **Jeta Syla**

---

**Project:** EthnoLens AI
**Track:** Track 1: Historical Knowledge to Structured Knowledge
**Core concept:** Historical documents → OCR → AI/NLP extraction → Taxonomic mapping → Searchable archive, map & grounded assistant
