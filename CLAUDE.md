# CLAUDE.md

## Project Overview

Academic Translator is a Python tool that converts complex academic research papers into plain-English explanations tailored to different audiences and learning styles. It supports PDF, DOCX, and TXT inputs and generates accessible HTML reports.

**Language:** Python 3.8+
**License:** MIT

## Repository Structure

```
Academic-Translator/
├── academic_translator.py       # Main application
│                                # - AcademicTranslationResult dataclass
│                                # - AccessibilityModule ABC
│                                # - AcademicTranslator class
│                                # - CLI entry point (main function)
├── term_matching.py            # Inflection + word-sense matching for the glossary
├── test_academic_translator.py # Test suite (stdlib unittest, no dependencies)
├── modules/                    # Pluggable accessibility modules
│   ├── ADHD_accessibility.py   # Chunks text, progress indicators, brain breaks
│   ├── dyslexia_accessibility.py # Simplified vocabulary, pronunciation guides
│   └── visual_processing.py   # ASCII diagrams, flowcharts, visual metaphors
├── requirements.txt            # Optional per-format document readers
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
   - Jargon translation (~84 terms across multiple fields, see `term_matching.py`)
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
- Name its class `<Name>Module` (e.g. `ADHDModule`) — the CLI short name is derived by stripping `Module` and lowercasing (e.g. `adhd`)

Modules are imported by file path rather than by package name, so the tool
works from any working directory. `discover_modules()` returns a
`{short_name: file_stem}` mapping; `load_module()` accepts either.

## Dependencies

**None are required.** Plain text (`.txt`) and the Python API run on the
standard library alone. The readers below are imported lazily and only needed
for their format; a missing one reports which package to install.

- **PyMuPDF (fitz)** — PDF extraction (tried first)
- **PyPDF2** — PDF extraction fallback
- **python-docx** — Word document handling

Install with: `pip install -r requirements.txt`

BeautifulSoup4 and requests were listed previously but nothing imports them —
the original top-level imports were unused and have been removed.

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

```bash
python test_academic_translator.py     # or: python -m unittest discover
```

52 tests covering translation, inflection and word-sense matching, module
discovery and loading, and report generation. Standard library only — no test
dependencies. Each module also has a runnable demo: `python modules/<file>.py`.

## Code Conventions

- **Style:** Snake_case for functions/variables, PascalCase for classes
- **Type hints** used throughout (`Dict`, `List`, `Optional`, etc.)
- **Dataclasses** for structured data
- **Abstract base classes** for extensibility
- **f-strings** for string formatting
- **Regex-based** text processing (no ML models)
- All translation logic is rule-based pattern matching
- Glossary expansions are written as **noun phrases**, since they get
  substituted into the sentence

## Known Issues

- No `pyproject.toml` for modern Python packaging
- No CI/CD pipeline (the test suite runs locally)
- Word-sense disambiguation uses hand-written cue vectors, not learned
  embeddings; adding a term that is also everyday English means adding its
  cues to `AMBIGUOUS_TERMS` by hand
- The `statistics` glossary is off by default (`include_statistics=True` to
  enable) because those terms are the most context-dependent

## Development Notes

- The project has no build system — it runs directly as a Python script
- No external API integrations; all processing is local and rule-based
- Reading level calculation is a rough heuristic based on word/sentence length
- Jargon matching is inflection-aware (plurals, irregulars, British spellings)
  and sense-aware (cosine similarity between the context window and per-sense
  cue vectors); see the module docstring in `term_matching.py`
- Confidence scoring: base 70% + 10% for recognized subject + 10% for research elements + 10% for methodology found
- HTML output uses inline CSS with gradient headers and color-coded sections
