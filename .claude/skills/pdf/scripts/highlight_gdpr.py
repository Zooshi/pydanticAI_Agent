"""
Script to highlight all mentions of "GDPR" in a PDF and add annotation.
Uses OCR for PDFs with vector-drawn text.
"""

import sys
import fitz  # PyMuPDF
import pytesseract
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight, Text as TextAnnotation
from pypdf.generic import ArrayObject, FloatObject
from PIL import Image
import io

def find_text_coordinates_with_ocr(pdf_path, search_term):
    """Find all occurrences of search term using OCR."""
    coordinates = []

    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Render page to high-resolution image
        mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better OCR
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Get OCR data with bounding boxes
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        # Scale factor to convert back to PDF coordinates
        scale = 1.0 / 3.0
        page_height = page.rect.height

        # Search for the term
        for i, text in enumerate(ocr_data['text']):
            if text and search_term.upper() in text.upper():
                # Get bounding box from OCR (image coordinates)
                left = ocr_data['left'][i] * scale
                top = ocr_data['top'][i] * scale
                width = ocr_data['width'][i] * scale
                height = ocr_data['height'][i] * scale

                # Convert to PDF coordinates (origin at bottom-left)
                x0 = left
                x1 = left + width
                y1 = page_height - top  # Flip Y
                y0 = page_height - (top + height)

                coordinates.append({
                    'page': page_num,
                    'rect': [x0, y0, x1, y1],
                    'text': text
                })

    doc.close()
    return coordinates

def highlight_text_in_pdf(input_pdf, output_pdf, search_term, annotation_text):
    """Add highlights and annotation to PDF."""
    # Find all coordinates using OCR
    print(f"Searching for '{search_term}' using OCR...")
    coords = find_text_coordinates_with_ocr(input_pdf, search_term)
    print(f"Found {len(coords)} occurrence(s) of '{search_term}'")

    if not coords:
        print("No matches found. Exiting.")
        return

    # Open PDF for writing
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    writer.append(reader)

    # Add highlights
    for coord in coords:
        page_num = coord['page']
        rect = coord['rect']

        # Create highlight annotation
        # Highlight needs QuadPoints (4 coordinates per corner)
        quad_points = ArrayObject([
            FloatObject(rect[0]), FloatObject(rect[3]),  # top-left
            FloatObject(rect[2]), FloatObject(rect[3]),  # top-right
            FloatObject(rect[0]), FloatObject(rect[1]),  # bottom-left
            FloatObject(rect[2]), FloatObject(rect[1]),  # bottom-right
        ])

        highlight = Highlight(
            rect=(rect[0], rect[1], rect[2], rect[3]),
            quad_points=quad_points,
        )

        writer.add_annotation(page_number=page_num, annotation=highlight)
        print(f"  Highlighted '{coord['text']}' on page {page_num + 1}")

    # Add text annotation on first page
    if len(reader.pages) > 0:
        first_page = reader.pages[0]
        page_height = float(first_page.mediabox.height)

        # Place annotation in top-right corner
        text_annot = TextAnnotation(
            rect=(500, page_height - 40, 520, page_height - 20),
            text=annotation_text,
        )

        writer.add_annotation(page_number=0, annotation=text_annot)
        print(f"\nAdded annotation: '{annotation_text}'")

    # Save
    with open(output_pdf, "wb") as f:
        writer.write(f)

    print(f"\nSaved to: {output_pdf}")
    print(f"Total highlights: {len(coords)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: highlight_gdpr.py [input_pdf] [output_pdf]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    highlight_text_in_pdf(
        input_path,
        output_path,
        search_term="GDPR",
        annotation_text="modified by claude"
    )
