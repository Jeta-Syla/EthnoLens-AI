"""OCR printed pages with Tesseract.

The BHL website sits behind a browser check that blocks scripts, so the demo pages come from
the FineBooks BHL IMPACT ground-truth set on Hugging Face: BHL page scans with expert
transcriptions (CC BY 3.0). Having the transcription lets us measure OCR quality on the same pages.

Writes data/raw/bhl/<barcode>/pages.jsonl, one line per page in the shape of the `passages`
table, plus the ground truth and the character error rate (CER).

Requires the Tesseract program itself, not only the pytesseract package.
ocr_pdf() also needs Poppler (used by pdf2image).

Usage (from the repo root):
  python -m pipeline.ocr                                   # 25 pages of birdsofgreatbrit02butl
  python -m pipeline.ocr --book birdsofgreatbrit02butl --pages 30
"""

import argparse
import io
import json
import os
import shutil
from pathlib import Path

import pytesseract
import requests
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "bhl"

DATASET = "finebooks/bhl-impact-gt"
ROWS_URL = "https://datasets-server.huggingface.co/rows"
BHL_PAGE_URL = "https://www.biodiversitylibrary.org/page/{page_id}"
HEADERS = {"User-Agent": "EthnoLens-AI/0.1 (student research prototype)"}
MIN_TRUTH_CHARS = 800  # skip plates, title pages and near-empty pages

# The Windows installer does not add Tesseract to PATH; fall back to TESSERACT_CMD or its default location.
WINDOWS_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if not shutil.which("tesseract"):
    pytesseract.pytesseract.tesseract_cmd = os.environ.get("TESSERACT_CMD", str(WINDOWS_TESSERACT))


def ocr_image(image: Image.Image, lang: str = "eng") -> str:
    return pytesseract.image_to_string(image, lang=lang).strip()


def ocr_pdf(path: str | Path, lang: str = "eng") -> list[tuple[int, str]]:
    """OCR every page of a PDF; returns (page number, text) pairs, numbered from 1."""
    from pdf2image import convert_from_path

    return [(n, ocr_image(img, lang)) for n, img in enumerate(convert_from_path(str(path)), start=1)]


def cer(hypothesis: str, reference: str) -> float:
    """Character error rate: edit distance / reference length, whitespace normalised."""
    hyp, ref = " ".join(hypothesis.split()), " ".join(reference.split())
    if not ref:
        return 0.0 if not hyp else 1.0
    previous = list(range(len(ref) + 1))
    for i, h in enumerate(hyp, start=1):
        current = [i]
        for j, r in enumerate(ref, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (h != r)))
        previous = current
    return previous[-1] / len(ref)


def book_pages(barcode: str) -> list[dict]:
    """All dataset rows of one book, in page order. Rows are grouped by book, so paging stops after it."""
    rows, offset = [], 0
    while True:
        resp = requests.get(ROWS_URL, headers=HEADERS, timeout=60, params={
            "dataset": DATASET, "config": "default", "split": "train", "offset": offset, "length": 100,
        })
        resp.raise_for_status()
        batch = [r["row"] for r in resp.json()["rows"]]
        mine = [r for r in batch if r["BarCode"] == barcode]
        rows += mine
        offset += len(batch)
        if len(batch) < 100 or (rows and len(mine) < len(batch)):
            break
    return sorted(rows, key=lambda r: int(r["PageID"]))


def run(barcode: str, n_pages: int) -> None:
    pages = book_pages(barcode)
    selected = [(seq, p) for seq, p in enumerate(pages, start=1) if len(p["text"]) >= MIN_TRUTH_CHARS][:n_pages]
    out_dir = RAW_DIR / barcode
    out_dir.mkdir(parents=True, exist_ok=True)

    errors = []
    with open(out_dir / "pages.jsonl", "w", encoding="utf-8") as out:
        for seq, page in selected:
            image_bytes = requests.get(page["image"]["src"], headers=HEADERS, timeout=60).content
            text = ocr_image(Image.open(io.BytesIO(image_bytes)))
            page_cer = cer(text, page["text"])
            errors.append(page_cer)
            out.write(json.dumps({
                "id": f"{barcode}:{page['PageID']}",
                "document_id": barcode,
                "folio": f"p. {seq}",  # position in the scanned volume
                "seq": seq,
                "text": text,
                "method": "ocr",
                "url": BHL_PAGE_URL.format(page_id=page["PageID"]),
                "ground_truth": page["text"],
                "cer": round(page_cer, 4),
            }, ensure_ascii=False) + "\n")
            print(f"p. {seq:>4}  BHL {page['PageID']}  CER {page_cer:.1%}")

    if errors:
        print(f"{barcode}: {len(errors)} pages, mean CER {sum(errors) / len(errors):.1%} -> {out_dir / 'pages.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR BHL pages with Tesseract and measure CER.")
    parser.add_argument("--book", default="birdsofgreatbrit02butl", help="FineBooks BarCode")
    parser.add_argument("--pages", type=int, default=25, help="number of text pages to OCR")
    args = parser.parse_args()
    run(args.book, args.pages)


if __name__ == "__main__":
    main()
