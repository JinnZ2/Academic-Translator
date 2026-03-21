# CLAUDE.md

## Project Overview

Academic Translator is a Python tool that converts complex academic research papers into plain-English explanations tailored to different audiences and learning styles. It supports PDF, DOCX, and TXT inputs and generates accessible HTML reports.

**Language:** Python 3.7+
**License:** MIT

## Repository Structure

```
Academic-Translator/
├── academic_translator.py       # Main application (~820 lines)
│                                # - AcademicTranslationResult dataclass
│                                # - AccessibilityModule ABC
│                                # - AcademicTranslator class (20 methods)
│                                # - CLI entry point (main function)
├── modules/                    # Pluggable accessibility modules
│   ├── ADHD_accessibility.py   # Chunks text, progress indicators, brain breaks
│   ├── dyslexia_accessibility.py # Simplified vocabulary, pronunciation guides
│   └── visual_processing.py   # ASCII diagrams, flowcharts, visual metaphors
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
└── LICENSE                     # MIT License
```

## Architecture

### Core Components

1. **`AcademicTranslationResult`** (dataclass) — Stores translation output: original text, plain English, findings, methodology, questions, confidence score, etc.

2. **`AccessibilityModule`** (ABC) — Base class for all accessibility modules. Required methods:
   - `get_name()` / `get_description()`
   - `process_text(text, context)` — Transform text for accessibility
   - `get_additional_elements(text, context)` — Return visual aids, action items

3. **`AcademicTranslator`** — Main class handling:
   - Subject area detection (medical, psychology, education, social science)
   - File text extraction (PDF/DOCX/TXT)
   - Jargon translation (200+ terms across multiple fields)
   - Key findings extraction
   - Methodology simplification
   - Reading level estimation
   - HTML report generation
   - Dynamic module discovery and loading from `modules/`

### Module Plugin System

Modules are discovered at runtime from the `modules/` directory via `importlib`. Each module must:
- Inherit from `AccessibilityModule`
- Implement all abstract methods
- Be a `.py` file in `modules/`

## Dependencies

- **PyPDF2** — PDF processing
- **PyMuPDF (fitz)** — Enhanced PDF extraction
- **BeautifulSoup4** — Web content parsing
- **python-docx** — Word document handling
- **requests** — HTTP calls

Install with: `pip install -r requirements.txt`

## Running the Application

```bash
# Translate a file
python academic_translator.py --file <path>

# Translate direct text
python academic_translator.py --text "<text>"

# Apply accessibility modules
python academic_translator.py --file <path> --modules adhd visual

# Override subject detection
python academic_translator.py --file <path> --subject medical

# Custom output filename
python academic_translator.py --file <path> --output <filename>

# List available modules
python academic_translator.py --list-modules
```

Output HTML reports are saved to the `academic_translations/` directory.

## Testing

No formal test suite exists. There are no test files, no pytest/unittest configuration, and no CI/CD pipeline. Testing is done manually.

## Code Conventions

- **Style:** Snake_case for functions/variables, PascalCase for classes
- **Type hints** used throughout (`Dict`, `List`, `Optional`, etc.)
- **Dataclasses** for structured data
- **Abstract base classes** for extensibility
- **f-strings** for string formatting
- **Regex-based** text processing (no ML models)
- All translation logic is rule-based pattern matching

## Known Issues

- No `pyproject.toml` for modern Python packaging
- No formal test suite or CI/CD pipeline

## Development Notes

- The project has no build system — it runs directly as a Python script
- No external API integrations; all processing is local and rule-based
- Reading level calculation is a rough heuristic based on word/sentence length
- Confidence scoring: base 70% + 10% for recognized subject + 10% for research elements + 10% for methodology found
- HTML output uses inline CSS with gradient headers and color-coded sections
