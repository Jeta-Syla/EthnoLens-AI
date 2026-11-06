# EthnoLens AI

Slide text for the submission. Each heading is one slide. Figures are from the README of 6 November 2026. Where a measurement is still open, the slide says so.

## 1. Problem

Plant knowledge sits in manuscripts, old books, and field studies. The names are historical, the spelling changes, and the source is easy to lose as soon as someone summarises a page.

A researcher has to read page after page, decide whether a word is a plant, and keep the link to the folio by hand.

EthnoLens AI keeps every fact beside the passage it came from. It is not medical advice.

## 2. Solution

Four steps, each one checkable:

- **Scan and discover.** A page is uploaded. The plant name comes back marked inside the passage.
- **Archive.** Search by name, part, preparation, source, and language. The plant sheet shows what the text says and what is only a candidate.
- **EthnoMap.** A point appears only for a documented region in Kosovo or Albania. The popup shows the Albanian name and the source. The point is the region, not a village coordinate.
- **Ask.** An answer appears only with a passage that can be opened. With no source, the screen says "Nuk ka të dhëna në arkivë". A question about dose or treatment is refused.

## 3. Demo

What the audience sees:

1. Upload a page in Scan. A loading line stays up until the API answers. The plant name is marked in gold in the passage.
2. Open the same record in the Archive. An empty archive, a failed connection, and a search with no matches are three different screens.
3. On EthnoMap, a point appears only after a documented Kosovo or Albania region is loaded. The popup shows the Albanian name and the source. With no such region, the map says so instead of inventing a pin.
4. In Ask, a dosage question is refused. A question with no supporting passage gets "Nuk ka të dhëna në arkivë".

Every page carries the warning: described uses are historical records, not instructions.

## 4. Architecture

- The pages are Streamlit. The map is Leaflet through folium.
- The API is FastAPI: `GET /records`, `POST /documents`, `GET /map`, `POST /ask`.
- Text and records live in SQLite. Ask searches passages with Chroma.
- OCR for printed pages is Tesseract. Record extraction is a language model in JSON mode, checked against the contract in `schema/record.json`.
- A scientific name is compared with GBIF. Albanian names come from Mustafa et al. 2012 and are tied to the accepted name.

Every record keeps its source, folio, passage, confidence, and whether the name is stated in the text or inferred.

## 5. Results

What has been measured:

- 183 transcribed pages of MS Add. 9308, split into 221 recipes. 100 are loaded into the database, with source, folio, language, and period.
- OCR: mean character error rate 2.7% on 25 BHL pages. About 1.2% on prose. 38% on one two-column contents page.
- 100 Albanian names for 98 species, from the Albanian Alps field study in Kosovo. Seven outdated names in the article are linked to the accepted GBIF name.
- Ask refuses a personal medical question: 15 of 15 in the smoke test, in Albanian and English. With no passage to support an answer, it does not answer.
- Extraction scoring on 50 recipes is still open. 33 are annotated and 17 remain. 17 of the annotated recipes were marked with model assistance, so the metrics will also be reported on the 33 hand-annotated recipes alone. There is no final accuracy figure yet.

## 6. Ethics

- It does not give medical advice, a dose, or a treatment. The warning stays on the page, and Ask refuses the question.
- A candidate scientific name is not shown as a confirmed identification.
- What the text says and what the model infers are kept apart.
- Local names are used only from published sources, with a citation.
- Texts whose licence is unclear are not redistributed. Restricted material is linked, not copied.

## 7. Roadmap

1. Finish the evaluation on 50 recipes, and report the hand-annotated set separately.
2. Add more sources from Kosovo, Albania, and the Balkans, and grow the map only with documented regions.
3. Handwritten text recognition for pages a user uploads.
4. Review tools for researchers, students, and heritage institutions.
