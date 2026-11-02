# 🌿 EthnoLens AI

### Turning Centuries of Traditional Knowledge into Evidence-Linked, Searchable Insights with AI

## 📖 About the Project

**EthnoLens AI** is an AI-powered platform that transforms scattered historical and ethnobotanical knowledge into structured, searchable, and evidence-linked information.

For centuries, communities have documented knowledge about medicinal plants, their traditional uses, preparation methods, and geographic contexts. Much of this knowledge remains locked inside historical manuscripts, ethnobotanical publications, scanned documents, and scientific literature, making it difficult to search, compare, and analyze at scale.

EthnoLens AI addresses this challenge by combining **Natural Language Processing (NLP), information extraction, and knowledge organization** to identify relevant ethnobotanical information from unstructured text and transform it into structured records.

Instead of simply generating answers, EthnoLens AI connects extracted insights back to their **original sources and supporting evidence**, allowing users to explore how the information was obtained.

---

## 🎯 Problem Statement

Traditional medicinal and ethnobotanical knowledge represents an important part of cultural and scientific heritage. However, accessing and analyzing this information systematically presents several challenges:

- Knowledge is scattered across books, manuscripts, publications, and digital archives.
- Many valuable sources exist as scanned or poorly structured documents.
- Plant names can appear in historical, regional, or multilingual forms.
- Traditional uses and preparation methods are embedded in long, unstructured passages.
- Manually extracting and organizing information is slow and difficult to scale.
- Relationships between plants, uses, plant parts, preparation methods, regions, and historical sources are difficult to explore.
- Researchers often need to return to the original document to verify extracted information.

---

## 💡 Our Solution

**EthnoLens AI** creates an intelligent pipeline for discovering and structuring ethnobotanical knowledge from historical and scientific texts.

The system analyzes source documents and identifies entities and relationships such as:

```text
Plant → Plant Part → Traditional Use → Preparation Method → Region → Historical Source
```

The extracted information is then organized into searchable records while preserving a connection to the original source and supporting evidence.

This allows users to move from large collections of unstructured documents to an interactive knowledge layer that can be searched, filtered, analyzed, and visually explored.

---

## 🧠 How It Works

The proposed pipeline consists of five main stages:

### 1. 📚 Document Collection

Collect publicly available historical manuscripts, ethnobotanical publications, and relevant scientific literature.

### 2. 🔎 Text & OCR Processing

Convert digital and scanned documents into machine-readable text using document processing and OCR where necessary.

### 3. 🤖 AI-Powered Information Extraction

NLP models identify relevant information, including:

- Plant names
- Scientific names
- Plant parts
- Traditional uses
- Preparation methods
- Geographic locations
- Historical context

### 4. 🗂️ Knowledge Structuring

Transform extracted information into structured records and connect related entities.

Example:

```text
Plant
├── Scientific Name
├── Plant Part
├── Traditional Use
├── Preparation Method
├── Region
└── Historical Sources
```

### 5. 🌐 Knowledge Exploration

Users can search and explore the extracted knowledge through an interactive interface while tracing each result back to its original source.

---

## ✨ Key Features

### 🤖 AI-Powered Text Extraction

Automatically identify relevant ethnobotanical information from historical and scientific documents.

### 🌿 Plant Recognition

Identify plant mentions and, where possible, connect historical or common names with scientific classifications.

### 🧪 Traditional Use & Preparation Extraction

Extract documented traditional applications, plant parts, and preparation methods from source text.

### 🔗 Evidence & Source Traceability

Connect extracted records to their original documents and supporting passages, enabling users to verify the information.

### 🔍 Intelligent Search

Search across plants, traditional uses, regions, preparation methods, and historical sources.

### 🕸️ Knowledge Graph

Represent relationships between plants, uses, regions, and sources to reveal connections that are difficult to discover in raw documents.

### 📊 Interactive Exploration

Filter, compare, and visually explore the collected knowledge through an interactive interface.

---

## 📊 Example

A historical text might contain information such as:

> A plant's leaves were traditionally prepared as an infusion in a particular region.

EthnoLens AI can transform this passage into a structured record:

| Field | Extracted Information |
|---|---|
| 🌿 Plant | Identified plant |
| 🔬 Scientific Name | Linked classification |
| 🍃 Plant Part | Leaves |
| 📖 Traditional Use | Documented traditional use |
| 🧪 Preparation | Infusion |
| 📍 Region | Identified location |
| 📚 Source | Historical document |
| 🔗 Evidence | Original supporting passage |

The user can inspect the extracted record and return to the original source to verify the information.

---

## 📊 Data Sources

EthnoLens AI is designed to work with publicly available and scientifically documented sources, including:

- **Curious Cures in Cambridge Libraries** – historical medical recipes and manuscripts
- **HIMERA** – historical medical text resources useful for NLP research and evaluation
- **Biodiversity Heritage Library (BHL)** – historical botanical and biodiversity literature
- Public ethnobotanical publications and scientific literature
- Open botanical and biodiversity databases for taxonomy and plant information

All external sources will be appropriately referenced and used according to their licensing and attribution requirements.

---

## 🛠️ Technology Stack

The implementation will use technologies such as:

- **Programming:** Python
- **AI & NLP:** Natural Language Processing, Named Entity Recognition (NER), Information Extraction
- **OCR:** OCR-based document processing
- **Data Processing:** Pandas
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Frontend:** React
- **Visualization:** Interactive graphs and data visualizations

The final technology stack may be refined during development based on implementation requirements.

---

## 🌍 Expected Impact

EthnoLens AI aims to create value at the intersection of **AI, cultural heritage, biodiversity, and scientific research**.

Potential impact includes:

- Preserving valuable traditional knowledge in a structured digital format.
- Making historical ethnobotanical information easier to discover.
- Supporting researchers in exploring large collections of historical texts.
- Connecting cultural knowledge with botanical information.
- Enabling new ways of discovering relationships between plants, uses, regions, and historical sources.
- Demonstrating how AI can transform unstructured cultural heritage into usable knowledge.

---

## ⚠️ Responsible Use

EthnoLens AI is a **research and knowledge-exploration platform**.

The system reports information documented in historical and ethnobotanical sources. A documented traditional use is **not considered evidence of clinical effectiveness**, and extracted information should not be interpreted as medical advice or a recommendation for treatment.

AI-generated or extracted information should be verified against the original source before being used for research or other purposes.

---

## 🚀 Project Status

**EthnoLens AI is currently being developed for EthnoHack 2026.**

The project will include an end-to-end prototype covering:

- Document processing
- OCR
- AI/NLP-based information extraction
- Structured knowledge storage
- Source and evidence traceability
- Search and filtering
- Interactive knowledge exploration

---

## 👥 Team

### EthnoLens AI – EthnoHack 2026

- **Dafina Keqmezi**
- **Erëza Ismajli**
- **Jeta Syla**

---

## 📄 License

To be defined.

---

<div align="center">

### 🌿 Preserving the past. Structuring knowledge. Exploring it with AI.

</div>
