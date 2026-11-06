# Annotation guide (50 recipes)

## Purpose

Create a human reference standard for measuring how accurately the system finds plants and recipe details. Annotate only what can be read in the source passage. Do not fill gaps with modern botanical knowledge.

## How to fill in the CSV

Use `eval/annotations/<name>.csv`. Each row represents one passage. Fill in `historical_name`, `plant_part`, `preparation`, `described_use`, and `notes`.

- `historical_name`: the plant name exactly as it appears in the manuscript, preserving historical spelling. Use one plant per row. If a recipe mentions two plants, copy the row and use the same `passage_id` and `folio` for each.
- `plant_part`: the part explicitly mentioned (e.g. leaf, root, seed). Use lowercase singular English to match the schema. Leave it blank if the passage does not say.
- `preparation`: the words in the passage that describe preparation, copied as written (e.g. “sethe hem togidre”). Leave it blank if no preparation is described.
- `described_use`: the words in the passage that describe the historical use. Do not turn them into advice or a medical claim. Leave it blank if none is given.
- `notes`: reading ambiguities, the span of relevant passage wording, or why an entry remains unresolved. Do not state a modern identification as fact.

## Decision rules

1. Read the entire text under the folio before annotating.
2. Include only plants that can be identified from the text. If it says only “herbe” or the name is missing or unreadable, do not invent a plant name; explain this in `notes`.
3. Preserve different historical spellings as written. Do not merge similar names without clear evidence.
4. Do not annotate non-plant ingredients. Do not infer a plant part, preparation, or use from general knowledge.
5. If a recipe contains several plants, create one row for each plant and repeat the passage identifiers.
6. For uncertain text, annotate only what you can support and note the uncertainty in `notes`.

## Before submitting

- The number of rows may exceed the number of recipes when a passage contains several plants.
- Do not change the provided `passage_id` or `folio`.
- Leave unknown fields blank; do not enter `N/A`, guesses, or placeholders.
- Save the CSV as UTF-8 so historical characters are preserved.

Annotators should work independently. Do not look at the model's extraction results until you have finished annotating, to avoid biasing the reference standard.
