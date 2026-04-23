import os
import shutil
import html
import fitz
import json
from datetime import datetime
from pdf2image import convert_from_path

# ===== CONFIG =====
URL = "https://ohioasphaltmagazine.com/"
MAGAZINE = "Ohio Asphalt Magazine"
GACODE = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-GGGG4GEPZB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-GGGG4GEPZB');
</script>"""

# ===== INPUTS =====
PDF_PATH = "input.pdf"  # change this to your PDF
OUTPUT_DIR = "output"
IMAGE_FORMAT = "webp"  # png, jpg, or webp
DPI = 150
ISSUE_NAME = "Flipbook"
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


def generate_html(image_paths, page_links):
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

        f.write("""
            <div class="archive-toggle">▼</div>

            <div class="archive-menu">
                <div class="archive-content">
                    Archive
                </div>
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
                    <img src="{img}">
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
        
        f.write("""

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
        
        f.write("""
    </div>
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
    generate_html(images, links)
    update_library_json(images)
    print("Done.")

if __name__ == "__main__":
    main()