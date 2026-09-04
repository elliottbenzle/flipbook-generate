import os
import shutil
import html
import fitz
import json
from datetime import datetime
from pdf2image import convert_from_path

# ===== CONFIG =====
URL = "https://ohiocontractormagazine.com/"
MAGAZINE = "Ohio Contractor Magazine"
GACODE = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-SCWX9YGD84"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-SCWX9YGD84');
</script>"""

# ===== INPUTS =====
PDF_PATH = "input.pdf"  # change this to your PDF
OUTPUT_DIR = "output"
IMAGE_FORMAT = "webp"  # png, jpg, or webp
DPI = 150
ISSUE_NAME = "Ohio Contractor Magazine"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))



# If on Windows, set Poppler path
POPPLER_PATH = os.path.join(SCRIPT_DIR, "poppler-25.12.0", "Library", "bin")

# ==================

def ensure_output():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def copy_assets():
    print("Copying CSS and JS files...")

    files_to_copy = ["style.css", "script.js", "turn.min.js", "zoom.min.js"]

    for file_name in files_to_copy:
        src = os.path.join(SCRIPT_DIR, file_name)
        dst = os.path.join(OUTPUT_DIR, file_name)

        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"Copied {file_name}")
        else:
            print(f"WARNING: {file_name} not found in script directory")

def convert_pdf_to_images():
    print("Converting PDF to images...")
    
    pages = convert_from_path(
        PDF_PATH,
        dpi=DPI,
        poppler_path=POPPLER_PATH
    )

    image_paths = []

    for i, page in enumerate(pages):
        filename = f"page-{i+1}.{IMAGE_FORMAT}"
        filepath = os.path.join(OUTPUT_DIR, filename)

        page.save(filepath, IMAGE_FORMAT.upper())
        image_paths.append(filename)

        print(f"Saved {filename}")

    return image_paths


def extract_pdf_links():
    """
    Returns a list where each item corresponds to a PDF page and contains
    overlay data for that page.

    Each overlay is stored as percentage values relative to the page size:
    {
        "url": "https://example.com",
        "left_pct": 12.34,
        "top_pct": 45.67,
        "width_pct": 20.12,
        "height_pct": 3.45
    }
    """
    print("Extracting links from PDF...")

    doc = fitz.open(PDF_PATH)
    pages_links = []

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        page_links = []

        for link in page.get_links():
            url = link.get("uri")
            rect = link.get("from")

            # Only handle external URI links for now
            if not url or not rect:
                continue

            # rect is in PDF coordinates (origin at top-left in PyMuPDF page space)
            left = rect.x0
            top = rect.y0
            width = rect.width
            height = rect.height

            overlay = {
                "url": url,
                "left_pct": (left / page_width) * 100,
                "top_pct": (top / page_height) * 100,
                "width_pct": (width / page_width) * 100,
                "height_pct": (height / page_height) * 100
            }

            page_links.append(overlay)

        pages_links.append(page_links)
        print(f"Page {page_index + 1}: found {len(page_links)} link(s)")

    doc.close()
    return pages_links

def _join_pdf_lines(lines):
    """Join wrapped PDF lines into readable text while preserving real breaks."""
    cleaned = []
    for line in lines:
        line = " ".join(line.split()).strip()
        if line:
            cleaned.append(line)

    if not cleaned:
        return ""

    result = cleaned[0]
    for line in cleaned[1:]:
        if result.endswith("-") and line and line[0].islower():
            result = result[:-1] + line
        else:
            result += " " + line

    return result.strip()


def extract_pdf_text():
    """Extract cleaned, ordered text blocks from each PDF page."""
    print("Extracting text from PDF...")

    doc = fitz.open(PDF_PATH)
    pages_text = []

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        page_dict = page.get_text("dict", sort=True)
        raw_blocks = []
        all_font_sizes = []

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            lines = []
            block_font_sizes = []

            for line in block.get("lines", []):
                line_parts = []
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if span_text.strip():
                        line_parts.append(span_text)
                        size = float(span.get("size", 0) or 0)
                        if size > 0:
                            block_font_sizes.append(size)
                            all_font_sizes.append(size)

                if line_parts:
                    lines.append("".join(line_parts))

            text = _join_pdf_lines(lines)
            if text:
                raw_blocks.append({
                    "text": text,
                    "max_font_size": max(block_font_sizes) if block_font_sizes else 0,
                    "line_count": len(lines),
                })

        if all_font_sizes:
            sorted_sizes = sorted(all_font_sizes)
            body_size = sorted_sizes[len(sorted_sizes) // 2]
        else:
            body_size = 0

        blocks = []
        for block in raw_blocks:
            text = block["text"]
            word_count = len(text.split())
            max_size = block["max_font_size"]
            is_heading = False

            if word_count <= 18 and len(text) <= 180:
                if body_size and max_size >= body_size * 1.22:
                    is_heading = True
                elif block["line_count"] <= 2 and text.isupper() and word_count <= 12:
                    is_heading = True

            blocks.append({
                "type": "heading" if is_heading else "paragraph",
                "text": text,
            })

        pages_text.append(blocks)
        char_count = sum(len(block["text"]) for block in blocks)
        print(f"Page {page_index + 1}: extracted {char_count} character(s) in {len(blocks)} block(s)")

    doc.close()
    return pages_text


def copy_pdf_to_output():
    pdf_filename = os.path.basename(PDF_PATH)
    dst = os.path.join(OUTPUT_DIR, pdf_filename)

    shutil.copy(PDF_PATH, dst)
    print(f"Copied PDF: {pdf_filename}")

    return pdf_filename
    
def generate_html(image_paths, page_links, page_text, pdf_download_file):
    print("Generating HTML...")

    html_path = os.path.join(OUTPUT_DIR, "index.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>""" + ISSUE_NAME + """</title>
    <link rel="stylesheet" href="style.css">
    
    """ + GACODE + """
    
    <!-- TURN.JS REQUIREMENTS -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="turn.min.js"></script>
    <script src="zoom.min.js"></script>
    
</head>
<body>

    <div class="book">
        
     <!-- ARCHIVE MODAL -->
    <div class="archive-modal">
        <div class="archive-modal-content">
            
            <div class="archive-header">
                <span>Archive</span>
                <button class="archive-close">&times;</button>
            </div>

            <div class="archive-body">
                <div class="archive-title">Library</div>
                <div class="archive-subtitle">""" + MAGAZINE + """</div>

                <div class="archive-grid"></div>
            </div>

        </div>
    </div>
    
    """)

        f.write(f"""
            <div class="archive-toggle">▼</div>

            <div class="archive-menu">
                <div class="archive-content">Archive</div>
                <a class="download-content" href="{pdf_download_file}" download>Download</a>
                <button class="top-menu-button" onclick="printAllPages()">Print All</button>
                <button class="top-menu-button" onclick="printCurrentPages()">Print Current Pages</button>
                <button class="top-menu-button text-view-menu-button" onclick="openTextView()">Text View</button>
            </div>
            <button class="nav prev" onclick="prevPage()">❮</button>
            <button class="nav next" onclick="nextPage()">❯</button>
            
            <div id="zoom-container">
                <div class="zoom-close" onclick="closeZoom()">✕</div>
                <div id="flipbook">
        """)
        
        for page_index, img in enumerate(image_paths):
            f.write(f'''
            <div class="page">
                <div class="page-inner">
                    <div class="inner-shadow left"></div>
                    <div class="inner-shadow right"></div>
                    <img src="{img}" alt="Page {page_index + 1} of {html.escape(ISSUE_NAME, quote=True)}">
            ''')
            
            # Add overlays for this page
            if page_index < len(page_links):
                for link in page_links[page_index]:
                    safe_url = html.escape(link["url"], quote=True)
                    left_pct = f'{link["left_pct"]:.4f}'
                    top_pct = f'{link["top_pct"]:.4f}'
                    width_pct = f'{link["width_pct"]:.4f}'
                    height_pct = f'{link["height_pct"]:.4f}'

                    f.write(f"""
                    <a class="link-overlay"
                       href="{safe_url}"
                       target="_blank"
                       rel="noopener noreferrer"
                       style="left:{left_pct}%; top:{top_pct}%; width:{width_pct}%; height:{height_pct}%;"
                       aria-label="PDF link"></a>
            """)
            
            
            f.write(f'''
                </div>
            </div>
            ''')

        f.write("""
            </div>
        </div>
        """)

        # Text View: all extracted text remains in semantic HTML. CSS/JS displays
        # one page at a time when the reader opens the alternate reading view.
        f.write("""
        <div class="text-view-overlay" id="text-view-overlay" aria-hidden="true">
            <div class="text-view-shell" role="dialog" aria-modal="true" aria-labelledby="text-view-title">
                <div class="text-view-header">
                    <div>
                        <div class="text-view-kicker">Text View</div>
                        <h1 id="text-view-title">""" + html.escape(ISSUE_NAME) + """</h1>
                    </div>
                    <button class="text-view-close" type="button" onclick="closeTextView()" aria-label="Close Text View">&times;</button>
                </div>
                <div class="text-view-content">
        """)

        for page_index, blocks in enumerate(page_text):
            page_number = page_index + 1
            f.write(f"""
                    <article class="text-page" data-text-page="{page_number}" aria-label="Page {page_number}">
                        <div class="text-page-number">Page {page_number}</div>
            """)

            if blocks:
                for block in blocks:
                    safe_text = html.escape(block["text"])
                    if block["type"] == "heading":
                        f.write(f'<h2 class="text-block-heading">{safe_text}</h2>\n')
                    else:
                        f.write(f'<p>{safe_text}</p>\n')
            else:
                f.write('<p class="text-empty-page">No extractable text was found on this page.</p>\n')

            f.write('                    </article>\n')

        page_options = "".join(
            f'<option value="{i}">{i}</option>'
            for i in range(1, len(page_text) + 1)
        )

        f.write(f"""
                </div>
                <nav class="text-view-pagination" aria-label="Text page navigation">
                    <button type="button" class="text-page-nav" id="text-prev-page" onclick="changeTextPage(-1)">Previous</button>
                    <label class="text-page-select-label" for="text-page-select">
                        <span>Page</span>
                        <select id="text-page-select" onchange="showTextPage(parseInt(this.value, 10))">
                            {page_options}
                        </select>
                        <span>of {len(page_text)}</span>
                    </label>
                    <button type="button" class="text-page-nav" id="text-next-page" onclick="changeTextPage(1)">Next</button>
                </nav>
            </div>
        </div>

            <div class="thumb-toggle">⌃</div>

            <div class="thumb-bar">
                <button class="thumb-nav left" onclick="scrollThumbs(-1)">❮</button>

                <div class="thumb-viewport">
                    <div class="thumb-track">
        """)

        for i, img in enumerate(image_paths):
            f.write(f"""
                <div class="thumb" onclick="goToPage({i+1})">
                    <img src="{img}" title="Page {i+1}">
                </div>
            """)

        f.write("""
                        </div>
                    </div>

                    <button class="thumb-nav right" onclick="scrollThumbs(1)">❯</button>
                </div>
        """)
        
        f.write(f"""
    </div>
    <script>
        window.FLIPBOOK_PAGES = {json.dumps(image_paths)};
        window.FLIPBOOK_TITLE = {json.dumps(ISSUE_NAME)};
    </script>
<script src="script.js"></script>
</body>
</html>
""")

    print(f"HTML created: {html_path}")


def update_library_json(image_paths):
    print("Updating library.json...")
    
    library_path = os.path.join(PARENT_DIR, "library.json")

    # ✅ If file does NOT exist → create it
    if not os.path.exists(library_path):
        print("⚠️ library.json not found. Creating a new one...")

        data = {
            "menu": {
                "item": [
                    {
                        "_sTitle": MAGAZINE,
                        "item": []
                    }
                ]
            }
        }

        # Write initial structure
        with open(library_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print("✅ library.json created")

    # ✅ Now load it (either existing or newly created)
    with open(library_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Navigate structure safely
    try:
        items = data["menu"]["item"][0]["item"]
    except (KeyError, IndexError):
        print("❌ Unexpected library.json structure")
        return

    # ✅ Create new entry
    new_item = {
        "_sCover": f"{URL}{os.path.basename(OUTPUT_DIR)}/{image_paths[0]}",
        "_sDate": datetime.today().strftime("%Y-%m-%d"),
        "_sPublished": True,
        "_sTitle": ISSUE_NAME,
        "_sURL": f"{URL}{os.path.basename(OUTPUT_DIR)}/index.html",
        "_sVersion": "9.x"
    }

    # Insert at top
    items.insert(0, new_item)

    # Write back
    with open(library_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("library.json updated")


def main():
    global OUTPUT_DIR, PDF_PATH, ISSUE_NAME

    # OUTPUT FOLDER
    user_output = input("Output directory name (leave blank for 'output'): ").strip()
    if user_output:
        OUTPUT_DIR = os.path.join(PARENT_DIR, user_output if user_output else "output")

    # INPUT FILE
    user_input = input("Input file (include .pdf): ").strip()

    if not user_input:
        print("❌ You must enter a file name.")
        return

    if not user_input.lower().endswith(".pdf"):
        print("❌ File must include .pdf extension (example: spring-2026.pdf)")
        return

    PDF_PATH = os.path.join(PARENT_DIR, user_input)

    if not os.path.exists(PDF_PATH):
        print(f"❌ File not found: {PDF_PATH}")
        return

    # ISSUE NAME
    user_issue = input("Issue name (used for page title): ").strip()
    if user_issue:
        ISSUE_NAME = user_issue

    print(f"Using input file: {PDF_PATH}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Issue name: {ISSUE_NAME}")
        
    ensure_output()
    copy_assets()
    images = convert_pdf_to_images()
    links = extract_pdf_links()
    page_text = extract_pdf_text()
    pdf_download_file = copy_pdf_to_output()
    generate_html(images, links, page_text, pdf_download_file)
    update_library_json(images)
    print("Done.")

if __name__ == "__main__":
    main()