# 📘 Flipbook Generator

This tool converts a PDF magazine into an interactive HTML flipbook and automatically updates the archive (`library.json`).

---

# 🛠️ Installation

## 1. Download the Generator

Download the `/flipbook-generate/` directory and place it inside your magazine project folder.

---

## 2. Folder Structure

Your directory should look like this:
/some-folder/
│
├── flipbook-generate/
│ ├── flipbook-generate.py
│ ├── poppler-25.12.0/
│ ├── script.js
│ ├── style.css
│ └── turn.min.js
│
├── library.json
├── your-magazine.pdf

### Notes:
- `library.json` stores all archived issues
- PDF input files live in the **same directory as `/flipbook-generate/`**
- Output folders will also be created in this same directory

---

## 3. Install Python (if needed)

Download and install Python:
👉 https://www.python.org/downloads/

During installation:
- ✅ Check **“Add Python to PATH”**

Verify installation:
python --version

---

## 4. Install Required Python Packages

Open Command Prompt / Terminal and run:
pip install pdf2image pymupdf

### Packages used:
- `pdf2image` → converts PDF pages to images
- `pymupdf (fitz)` → extracts link data from PDFs

---

## 5. Poppler (Already Included)

Poppler is bundled inside `/flipbook-generate/`:
poppler-25.12.0/

No additional setup required.

---

## 6. Configure Constants (One-Time Setup)

Open:
flipbook-generate.py

Update these variables:
URL = "https://yourdomain.com/"
MAGAZINE = "Your Magazine Name"
GACODE = """ your GA4 script """

Notes:
These values remain the same for each issue. Only needs to be configured once per magazine.

⚠️ Multiple Magazines

Each magazine should have its own setup.

Example:
/Magazine-A/
/Magazine-B/
/Magazine-C/

Each folder should contain:

flipbook-generate/
library.json
PDF files

👉 Run the generator separately for each magazine

---------------------------------------------------------------------------------

# 🚀 Generating a Flipbook

## 1. Prepare Files

Ensure:
Your PDF is in the root folder
library.json exists in the root folder

Example:
/some-folder/
├── flipbook-generate/
├── library.json
├── spring-2026.pdf

📌 About library.json
Stores all archived issues
Script will: preserve existing issues, add new issue to the top

## 2. Open Command Line

Navigate to the generator folder:
cd /path/to/your-folder/flipbook-generate


## 3. Run the Script
python flipbook-generate.py


## 4. Follow Prompts

Output directory name
Example: Spring-2026
👉 This becomes your new issue folder

Input file
Example: spring-2026.pdf
👉 Must include .pdf

Issue name
Example: Spring 2026 Issue
👉 Used for: Page title, Archive listing


## 5. Script Output

After running: A new folder will be created:

Example: /Spring-2026/

Containing:
HTML flipbook
page images
JS/CSS assets

## 6. Upload to Server

Upload via FTP:

Upload:
/Spring-2026/
Also upload updated:
library.json

## ✅ Final Result

Once uploaded:

New issue is live
Archive updates automatically
Flipbook includes:
page turning
zoom
clickable links
thumbnails
archive navigation

## 🎯 Summary Workflow
- Add PDF to root folder
- Run script
- Enter prompts
- Upload output folder + library.json


## 🔥 Notes
Re-running script will append to archive
Script will create library.json if missing
Each issue is self-contained for easy deployment

