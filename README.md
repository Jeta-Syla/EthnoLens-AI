# EthnoLens AI
### Turning Historical Traditional Medicine Knowledge into Structured, Searchable Insights with AI

## 1. Project Overview

**EthnoLens AI** is an AI-powered knowledge extraction platform designed to transform historical medical and botanical texts into structured, searchable information about traditional medicinal plants.

Historical manuscripts and books contain valuable information about how plants were traditionally used, which parts were collected, and how remedies were prepared. However, this knowledge is often scattered across old documents, written in historical languages, and difficult to search, analyse, and compare.

EthnoLens AI aims to bridge this gap by combining **Historical Sources, Optical Character Recognition (OCR), Natural Language Processing (NLP), AI-based Knowledge Extraction, and Modern Botanical References**.

The platform focuses on preserving historical knowledge, making it accessible, and connecting historical plant terminology with modern botanical classifications.

## 2. Problem Statement

A significant amount of traditional medicinal knowledge is preserved in historical manuscripts, pharmacopoeias, and botanical books.

Despite the availability of digitised historical collections, extracting meaningful information from these sources remains challenging.

Researchers often need to:

- Manually search through hundreds of historical pages.
- Interpret old terminology, spelling variations, and languages.
- Identify medicinal plants and their ingredients.
- Extract plant parts and traditional preparation methods.
- Identify the traditional uses described in historical texts.
- Connect historical plant names with modern scientific names.
- Preserve references to the original manuscripts and passages.

This process is time-consuming and makes it difficult to systematically analyse and compare historical knowledge.

**EthnoLens AI addresses this challenge by automatically extracting, organising, linking, and presenting historical knowledge through an AI-powered platform.**

## 3. Main Objectives

The main objective is to develop an AI-based system that converts unstructured historical knowledge into structured and searchable information.

Given a historical text describing a traditional remedy, the system should:

1. Read and process the historical document.
2. Identify plant names as they appear in the original text.
3. Extract the plant parts used (leaves, roots, seeds, flowers, bark, etc.).
4. Identify traditional preparation methods (infusion, decoction, powder, ointment, etc.).
5. Extract the traditional uses or ailments mentioned.
6. Map historical plant names to modern scientific names where possible.
7. Store extracted information in a structured database.
8. Preserve the original source, relevant passage, and confidence level for each extraction.

The system will distinguish between information explicitly stated in historical sources and information inferred through AI or external botanical references.

## 4. Dataset Sources

The project will combine several complementary historical and annotated datasets.

### 4.1 Curious Cures in Cambridge Libraries

**Role: Primary historical medical source**

- Approximately 8,000 historical medical recipes.
- Around 190 digitised manuscripts.
- Transcriptions in Latin and Middle English.
- Historical recipes containing ingredients and preparation methods.

This is the primary source because its recipe-oriented content is particularly relevant to identifying plants, ingredients, traditional uses, and preparation methods.

Source: https://www.lib.cam.ac.uk/curiouscures

### 4.2 Biodiversity Heritage Library (BHL)

**Role: Supporting historical botanical literature**

- Historical botanical and biological books.
- Digitised publications and OCR-derived text.
- Historical plant descriptions and scientific terminology.
- Large-scale historical literature collections.

The BHL collection can help identify historical plant terminology and provide additional botanical context.

Sources:
- https://www.biodiversitylibrary.org/
- https://huggingface.co/datasets/common-pile/biodiversity_heritage_library

### 4.3 HIMERA Corpus

**Role: NLP development and evaluation**

- Historical medical texts.
- Expert-annotated entities and semantic relationships.
- Useful examples for developing and evaluating NLP extraction methods.

HIMERA can support the development of Named Entity Recognition and relation extraction components.

Source: https://www.nactem.ac.uk/himera/

### 4.4 FineBooks BHL IMPACT Ground Truth

**Role: OCR evaluation**

- 2,165 historical pages.
- Expert-corrected transcriptions.
- Reference material for evaluating OCR quality.

This dataset can help measure how accurately the system converts historical printed pages into machine-readable text.

Source: https://huggingface.co/datasets/finebooks/bhl-impact-gt

## 5. Dataset Strategy

Each dataset has a specific purpose within the project.

| Dataset | Role |
|---|---|
| Curious Cures | Primary historical medical recipes |
| BHL | Supporting botanical literature |
| HIMERA | NLP development and evaluation |
| FineBooks | OCR testing and evaluation |

**Recommended combination:** Curious Cures + selected BHL material + HIMERA.

FineBooks can be used as an additional OCR evaluation resource.

Before implementation, the team will verify dataset availability, full-text access, formats, and licensing conditions.

## 6. Proposed System Architecture

The system will follow this processing pipeline:

```text
              HISTORICAL SOURCES
         Curious Cures | BHL | Other texts
                       |
                       v
               DOCUMENT INGESTION
            PDFs, images, metadata, texts
                       |
                       v
                    OCR LAYER
             Scanned documents to text
                       |
                       v
              TEXT PREPROCESSING
          Cleaning, segmentation, language
                       |
                       v
                AI / NLP EXTRACTION
        Plant Names | Plant Parts | Preparation
             Traditional Uses | Ingredients
                       |
                       v
              ENTITY NORMALISATION
         Historical terminology and variants
                       |
                       v
             MODERN BOTANICAL MAPPING
          Historical names to scientific names
                       |
                       v
               STRUCTURED DATABASE
        Extracted information, sources, evidence
                       |
                       v
                 ETHNOLENS AI
          Search | Filter | Explore | Compare
```

### 6.1 Document Ingestion

Import historical documents and relevant metadata, including titles, authors, dates, languages, manuscript identifiers, and page numbers.

### 6.2 OCR and Text Preprocessing

Convert scanned pages into machine-readable text using OCR.

Clean and segment the extracted text while preserving the original content and historical spelling.

### 6.3 AI / NLP Knowledge Extraction

Apply NLP techniques to identify:

- Plant names.
- Plant parts.
- Preparation methods.
- Traditional uses.
- Other ingredients.
- Quantities and measurements, where available.

### 6.4 Entity Normalisation and Botanical Mapping

Resolve historical spelling variations and connect historical plant names with possible modern scientific names using botanical reference sources.

Uncertain identifications should be marked for human review rather than presented as confirmed matches.

### 6.5 Structured Data Storage

Store the extracted information in a database, preserving source references and evidence passages.

### 6.6 Dashboard

Provide a user-friendly interface for searching, filtering, exploring, and comparing historical plant knowledge.

## 7. Proposed Data Model

Each extracted historical remedy can be represented through structured fields.

| Field | Description |
|---|---|
| Historical Plant Name | Name found in the original text |
| Normalised Plant Name | Standardised historical name |
| Modern Scientific Name | Candidate modern botanical name |
| Plant Part | Leaf, root, seed, flower, bark, etc. |
| Traditional Use | Historical use or ailment described |
| Preparation Method | Infusion, decoction, powder, ointment, etc. |
| Other Ingredients | Additional ingredients in the recipe |
| Historical Source | Book, manuscript, or collection |
| Page Reference | Original page or passage location |
| Original Passage | Supporting historical text |
| Language | Language of the source |
| Extraction Confidence | Confidence in AI/NLP extraction |
| Mapping Confidence | Confidence in botanical identification |
| Review Status | Pending, verified, or rejected |

The database should support multiple historical names, sources, and traditional uses associated with the same candidate plant.

## 8. Proposed Dashboard Features

The EthnoLens AI dashboard will allow users to explore extracted historical knowledge.

### Main Features

- **Plant Search:** Search using historical or modern plant names.
- **Historical Knowledge Explorer:** Browse extracted information from historical documents.
- **Plant Information:** View plant parts, traditional uses, and preparation methods.
- **Botanical Mapping:** Explore connections between historical and modern scientific names.
- **Source References:** Access original passages and historical documents.
- **Confidence Indicators:** Identify reliable and uncertain extractions.
- **Filtering:** Filter by plant part, preparation, language, historical source, or period.
- **Knowledge Comparison:** Compare how different historical sources describe the same plant.

### Example Result

| Field | Example |
|---|---|
| Historical Plant Name | Name found in manuscript |
| Modern Scientific Name | Candidate scientific identification |
| Plant Part | Root |
| Traditional Use | Use described in historical text |
| Preparation | Decoction |
| Historical Source | Manuscript title |
| Extraction Confidence | 0.91 |
| Mapping Confidence | 0.78 |
| Review Status | Pending verification |

*Illustrative example only. These values do not represent verified historical findings.*

## 9. AI and NLP Technologies

The project will demonstrate several AI/NLP techniques.

| Technology | Purpose |
|---|---|
| OCR | Extract text from historical scanned documents |
| Named Entity Recognition (NER) | Identify plants, ingredients, and relevant entities |
| Relation Extraction | Identify relationships between plants, parts, preparations, and uses |
| Entity Linking | Connect historical plant names with modern botanical references |
| Confidence Estimation | Estimate extraction and identification uncertainty |
| Human-in-the-loop Review | Allow expert verification of extracted information |

The implementation can begin with existing NLP models and rule-based methods. Fine-tuning or specialised models can be considered based on evaluation results.

## 10. Evaluation Strategy

The system will be evaluated through several measurable criteria:

- **OCR Accuracy:** Compare extracted text against expert-corrected transcriptions.
- **Entity Recognition:** Evaluate precision, recall, and F1-score.
- **Relation Extraction:** Measure the accuracy of relationships between plants, parts, preparations, and traditional uses.
- **Botanical Mapping:** Manually evaluate historical-to-modern plant name matches.
- **Source Traceability:** Verify that extracted information links to the correct original passage.
- **Usability:** Evaluate how efficiently users can search and explore the knowledge.

HIMERA will be used only for evaluation tasks that match its available annotation categories. Additional manually annotated examples may be created when necessary.

## 11. Scope and Limitations

The initial prototype will focus on a selected collection of historical recipes and botanical texts.

Potential challenges include:

- OCR errors and difficult historical handwriting.
- Historical spelling and language variations.
- Ambiguous plant names.
- Changes in botanical classification over time.
- Incomplete or contradictory historical descriptions.
- Incorrect AI-generated extractions.
- Different dataset access and licensing restrictions.

All extracted information will retain its historical context and supporting evidence.

**EthnoLens AI is a historical knowledge preservation and research platform. It does not validate the medical effectiveness of historical remedies and does not provide medical advice or treatment recommendations.**

## 12. Expected Outcome

The expected outcome is a functional prototype demonstrating how AI and NLP can transform historical medicinal-plant knowledge into structured, searchable information.

The prototype should include:

1. A selected collection of historical documents.
2. A document ingestion and OCR pipeline.
3. An NLP-based knowledge extraction component.
4. Historical plant name normalisation.
5. Modern botanical name mapping.
6. A structured database with source references.
7. A web dashboard for searching, filtering, and exploring information.
8. An evaluation of extraction and mapping performance.

## 13. Project Value

EthnoLens AI combines Artificial Intelligence, Natural Language Processing, digital humanities, and botanical knowledge in a practical research-oriented platform.

Its main value is not simply generating answers about medicinal plants, but transforming historical information into structured knowledge while preserving the evidence behind every extracted fact.

By connecting historical documents with modern botanical terminology, EthnoLens AI can support researchers, libraries, students, and anyone interested in the history of traditional plant knowledge.

---

**Project Name:** EthnoLens AI  
**Track:** Track 1 — Historical Knowledge to Structured Knowledge  
**Core Concept:** Historical Documents → OCR → AI/NLP → Knowledge Extraction → Botanical Mapping → Searchable Knowledge System

**Important:** EthnoLens AI is a historical research and knowledge-preservation platform, not a medical advice or treatment system.
