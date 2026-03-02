import os
import re
import pypdfium2 as pdfium
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def _clean_text(text: str) -> str:
    """
    Normalise PDF extraction noise before chunking.

    Two-pass approach so any future PDF is handled robustly:

    Pass 1 - meaningful substitutions for characters whose intent is known:
      \r\n / \r   Windows/old-Mac line endings              → \n
      \x84        C1 control used as bullet (Maytag PDF)    → •
      \xa0        Non-breaking space                        → (space)
      \xb9        Superscript 1 in fractions (3¹/2)        → 1
      \uf0d8      PUA bullet marker throughout Midea PDF    → •
      \uff08/09   Fullwidth parentheses (Midea)             → ()
      \uff0c      Fullwidth comma (Midea)                   → ,
      \uff1a      Fullwidth colon (Midea)                   → :

    Pass 2 - strip entire garbage Unicode ranges that can never be
    meaningful in technical plain text, regardless of source PDF:
      U+0080–U+009F  C1 control characters (layout codes, not text)
      U+E000–U+F8FF  BMP Private Use Area (font-specific glyphs)
      U+FFFD         Unicode replacement character (corrupted glyph)
      U+FFFE–U+FFFF  Unicode non-characters
    """
    # Pass 1: meaningful substitutions (order matters - CRLF before bare CR)
    SUBSTITUTIONS = [
        ("\r\n",   "\n"),
        ("\r",     "\n"),
        ("\x84",   "•"),
        ("\xa0",   " "),
        ("\xb9",   "1"),
        ("\uf0d8", "•"),
        ("\uff08", "("),
        ("\uff09", ")"),
        ("\uff0c", ","),
        ("\uff1a", ":"),
        ("\u3002", "."),    # CJK full stop (Midea)
        ("\u3010", "["),    # CJK left bracket (Midea - wraps UI mode names)
        ("\u3011", "]"),    # CJK right bracket (Midea)
    ]
    for bad, good in SUBSTITUTIONS:
        text = text.replace(bad, good)

    # Pass 2: strip remaining garbage ranges
    text = re.sub(r"[\x80-\x9f\ue000-\uf8ff\ufffd\ufffe\uffff]", "", text)

    lines = text.splitlines()
    cleaned = [line for line in lines if len(line.strip()) > 2]
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_and_chunk_pdfs() -> list[dict]:
    """
    Load all PDFs from DATA_DIR, extract text page by page,
    and split into chunks with source and page metadata.

    Uses pypdfium2 (PDFium engine) for reliable text extraction -
    pdfminer-based tools (pdfplumber, PyPDF2) produce garbled text
    on the Maytag manual due to font encoding issues.

    Returns a list of dicts: {"text": str, "source": str, "page": int}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    chunks = []

    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"Warning: no PDF files found in {DATA_DIR}")
        return chunks

    for filename in pdf_files:
        filepath = os.path.join(DATA_DIR, filename)
        print(f"Processing: {filename}")

        try:
            pdf = pdfium.PdfDocument(filepath)
            for page_num, page in enumerate(pdf, start=1):
                textpage = page.get_textpage()
                text = textpage.get_text_range()

                if not text or not text.strip():
                    continue

                # Use the PDF's own page label (e.g. "3-5") so source citations
                # match what the mechanic sees in the physical manual.
                # Fall back to the absolute page number if no label is set.
                label = pdf.get_page_label(page_num - 1) or str(page_num)

                text = _clean_text(text)
                page_chunks = splitter.split_text(text)

                for chunk in page_chunks:
                    chunks.append({
                        "text": chunk,
                        "source": filename,
                        "page": label,
                    })

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    print(f"Total chunks created: {len(chunks)}")
    return chunks