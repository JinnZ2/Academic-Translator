# Academic Translator

**Making ALL Knowledge Accessible to ALL Minds**

Transform academic papers, research studies, and technical documents into formats that work for different learning styles, reading levels, and cognitive differences. No more brilliant discoveries locked behind impenetrable jargon.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Accessibility](https://img.shields.io/badge/accessibility-focused-brightgreen.svg)
![Modular](https://img.shields.io/badge/modular-architecture-orange.svg)

## 🧠 Why This Matters

Academic research affects everyone’s life, but it’s written for academics. Medical breakthroughs that could help your condition. Educational strategies that could help your kids learn. Psychology research that explains human behavior. **All locked behind PhD-level language.**

**That stops now.**

This tool:

- 🔬 **Translates research papers** into plain English
- 🧩 **Modular accessibility** - ADHD, dyslexia, visual, audio support
- 🎯 **Extracts what matters** - key findings, real-world impact
- 📚 **Multi-subject support** - medical, psychology, education, social science
- ❓ **Generates questions** to ask doctors, teachers, therapists
- 📊 **Simplifies statistics** - what the numbers actually mean
- 🎨 **Visual elements** - converts concepts to diagrams

## 🚀 Real-World Transformations

### Medical Research

**Before:** “Participants receiving the intervention demonstrated statistically significant improvements in glycemic control (HbA1c reduction: -0.7%, p<0.001, 95% CI: -0.9 to -0.5) compared to controls.”

**After:** “People who got the treatment had much better blood sugar control. Their long-term blood sugar measure improved by 0.7% - that’s a meaningful improvement that almost certainly wasn’t due to chance.”

**Questions Generated:**

- 🩺 “Ask your doctor: ‘Could this treatment help my diabetes?’”
- 💊 “What are the side effects for someone like me?”

### Psychology Research

**Before:** “The construct validity of the measure was established through confirmatory factor analysis (χ² = 45.23, df = 24, p = .006, CFI = .95, RMSEA = .06).”

**After:** “We verified that our test actually measures what we claimed it measures using statistical analysis. The test passed the validity checks.”

### Education Research

**Before:** “Implementation of scaffolded metacognitive strategies yielded significant gains in reading comprehension (Cohen’s d = .68) across diverse learners.”

**After:** “Teaching students to think about their own thinking while providing support helped them understand reading much better. This worked for all types of learners.”

## ⚡ Quick Start

```bash
# Install
git clone https://github.com/JinnZ2/Academic-Translator.git
cd Academic-Translator

# Translate a plain-text paper - no dependencies needed
python academic_translator.py --file research_paper.txt

# For PDF and Word files, install the readers first
pip install -r requirements.txt
python academic_translator.py --file research_paper.pdf

# Apply accessibility modules
python academic_translator.py --file study.pdf --modules adhd visual dyslexia

# Get beautiful accessible report
open academic_translations/medical_research_translation.html
```

## 🧩 Accessibility Modules

**Mix and match modules for your specific needs.**

Run `python academic_translator.py --list-modules` to see what is installed.

### ✅ Shipped

**Learning differences**

- **`adhd`** - Chunked text, progress indicators, TL;DR summaries, brain breaks
- **`autism`** - Idioms replaced with their literal meaning, logical connections
  spelled out, vague quantities and hedging flagged, fixed predictable structure
- **`dyslexia`** - Shorter sentences, simpler vocabulary, phonetic guides, extra spacing
- **`visual`** - Converts text to ASCII diagrams, flowcharts, and visual metaphors

**Reading the claim itself**

- **`scope`** - Connects headline → abstract → methods → findings, and flags
  claims the study design cannot support. Checks the causal-claim ceiling of
  each design, who was actually studied, sample size, study duration against
  long-term claims, significance reported without an effect size, surrogate
  outcomes, and hedging that the title drops. Every flag quotes the text that
  raised it.

  Pass the headline that brought you to the paper and it checks *that* instead
  of the paper's own title — the usual case, since papers are often careful
  where the coverage is not:

  ```bash
  python academic_translator.py --file study.pdf --modules scope \
      --headline "Your morning coffee prevents dementia, scientists prove"
  ```

**Reading levels and language**

- **`beginner`** - Long words swapped for short ones *keeping tense and number*
  (“utilized” → “used”), sentences split only where the halves stand alone,
  glossary of the hard words it kept, reading level reported before and after
- **`esl`** - Phrasal verbs glossed inline, false-friend warnings, Latin/Greek
  roots decoded, US institutions explained, imperial units converted to metric
- **`audio`** - Abbreviations and statistical notation spoken properly
  (“et al.” → “and colleagues”, “p < .001” → “p is less than 0 point 0 0 1”),
  inline citations stripped, spoken signposts and listening time

Every module can be combined with any other:

```bash
python academic_translator.py --file study.pdf --modules autism beginner esl
```

### 🎯 Subject areas (built in, no module needed)

Subject area is detected automatically and tunes the glossary, the “why this
matters” notes, and the questions generated. Override it with `--subject`.

- **`medical`** - Patient-focused translations, “ask your doctor” prompts
- **`education`** - Teacher/parent applications, classroom implementation
- **`psychology`** - Real-world behavior applications, therapy connections
- **`social_science`**, **`science`** - Field-specific jargon glossaries

## 🔬 Supported Research Areas

### Medical & Health

- Clinical trials and treatment studies
- Drug research and safety studies
- Public health and epidemiology
- Medical device effectiveness

### Psychology & Behavioral Science

- Cognitive psychology research
- Social psychology studies
- Developmental psychology
- Mental health research

### Education & Learning

- Learning strategy research
- Educational intervention studies
- Curriculum effectiveness
- Special education research

### Social Sciences

- Policy research and analysis
- Economic studies
- Sociology and demographics
- Environmental research

## 🛠 Installation

```bash
git clone https://github.com/JinnZ2/Academic-Translator.git
cd Academic-Translator
pip install -r requirements.txt   # optional - see below
```

**Requirements:**

- Python 3.8+ — that is all you need for `.txt` files and the Python API

Everything in `requirements.txt` is optional, installed only for the document
formats you want to read:

- PyMuPDF and/or PyPDF2 — PDF files (PyMuPDF is tried first, PyPDF2 is the fallback)
- python-docx — Word `.docx` files

If a reader is missing, the tool tells you which package to install instead of
crashing.

### 🧪 Running the tests

```bash
python test_academic_translator.py
```

No test dependencies — it uses `unittest` from the standard library.

## 📖 Usage Examples

### Command Line Interface

```bash
# Basic translation
python academic_translator.py --file "medical_study.pdf"

# With accessibility modules
python academic_translator.py --file "research.pdf" --modules adhd visual

# Specify subject area
python academic_translator.py --file "paper.pdf" --subject medical

# List available modules
python academic_translator.py --list-modules

# Custom output name
python academic_translator.py --file "study.pdf" --output "my_study_explained"

# Choose where reports are written (default: academic_translations/)
python academic_translator.py --file "study.pdf" --output-dir ~/Documents/translations

# Translate text directly, no file needed
python academic_translator.py --text "Participants receiving the intervention..."
```

### Python API

```python
from academic_translator import AcademicTranslator

translator = AcademicTranslator()

# Basic translation
result = translator.translate_academic_document(research_text)

# With accessibility modules
result = translator.translate_academic_document(
    research_text, 
    modules=['adhd', 'visual', 'dyslexia']
)

# Force a subject area instead of detecting it
result = translator.translate_academic_document(research_text, subject_area='medical')

# Access results
print(f"Key findings: {result.key_findings}")
print(f"Why this matters: {result.why_this_matters}")
print(f"Questions to ask: {result.questions_to_ask}")

# Look up a single term across every field's glossary
print(translator.explain_term('ANOVA'))   # 'test to compare averages between groups'

# Save the HTML + JSON report
saved = translator.save_translation(result, "my_study")
print(saved['html'])
```

## 🎯 Perfect For

### Students & Researchers

- **Grad students** understanding papers outside their field
- **Undergrads** accessing primary research
- **Independent researchers** without institutional access
- **Interdisciplinary work** - psychology + medicine, education + tech

### Healthcare

- **Patients** understanding research about their conditions
- **Caregivers** learning about treatment options
- **Healthcare workers** staying current with research
- **Patient advocates** translating research for communities

### Education

- **Teachers** applying educational research in classrooms
- **Parents** understanding child development research
- **Special education** professionals accessing learning research
- **Administrators** using research for policy decisions

### General Public

- **Anyone** who wants to understand research that affects their life
- **Policy makers** using research for decisions
- **Journalists** reporting on scientific studies
- **Advocates** using research to support causes

## 🧩 Building Custom Modules

**The community builds what they need!** Create modules for specific accessibility requirements:

### Module Template

Drop any `.py` file into `modules/`. The CLI name comes from your **class**
name, not the filename: `AutismModule` becomes `--modules autism`, whatever you
call the file.

```python
from academic_translator import AccessibilityModule

class YourCustomModule(AccessibilityModule):
    def get_name(self) -> str:
        return "Your Module Name"
    
    def get_description(self) -> str:
        return "What your module does"
    
    def process_text(self, text: str, context: dict) -> str:
        # Transform text for accessibility
        return transformed_text
    
    def get_additional_elements(self, text: str, context: dict) -> dict:
        # Return visual aids, action items, etc.
        return {"visual_elements": [], "action_items": []}
```

`context` carries `subject_area`, `reading_level`, and `key_findings`, so your
module can adapt to what kind of paper it is looking at.

Check that it loads:

```bash
python academic_translator.py --list-modules
```

### Module Ideas Needed

- **🤟 Sign Language Module** - Gloss ordering and visual-first structure
- **🎵 Music Module** - Rhythm and melody learning aids
- **🤝 Social Module** - Group discussion prompts
- **📱 Mobile Module** - Thumb-friendly micro-learning
- **🧓 Senior Module** - Larger type, familiar reference points
- **👶 Parent Module** - Family-relevant applications
- **🌐 Translation Module** - Output in languages other than English

**The most useful contribution is not a new module — it is telling us where an
existing one gets it wrong.** The `autism` module's idiom list, the `esl`
module's false friends, and the `beginner` module's word swaps are all
hand-written and incomplete by definition. If a paper you actually needed to
read defeated one of them, that is the bug report we want.

## 📊 How It Works

### 1. **Intelligent Analysis**

- Detects subject area (medical, psychology, education, etc.)
- Identifies research methodology and study design
- Estimates original reading level
- Extracts key structural elements

### 2. **Jargon Translation**

- **80+ academic terms** translated by field (and growing — PRs welcome)
- Statistical terms simplified (“p<0.05” → “almost certainly not due to chance”)
- Methodology explanations (“double-blind” → “neither participants nor researchers knew who got real treatment”)

Matching is **inflection-aware** and **sense-aware**, because exact string
matching fails in both directions (see `term_matching.py`):

| Written in the paper | Naive matching | What we do |
| --- | --- | --- |
| “three **hypotheses**” | missed — glossary says *hypothesis* | “three educated **guesses** about what would happen (hypotheses)” |
| “**n=240**” | missed — glossary says `n =` | “number of people/things studied: 240” |
| “**randomised**” | missed — British spelling | matched |
| “scores **correlated** with…” | “scores *things that tend to happen together* with…” | “scores correlated (things that tend to happen together) with…” |
| “we **construct** a model” | “we *concept being measured* a model” | left alone — it’s a verb here |
| “erected **scaffolding**” | “erected *support that’s gradually removed as students learn*” | left alone — wrong sense |

Three mechanisms do this:

1. **Inflection** — each term expands into its plural, irregular plural
   (*analysis → analyses*), and spelling variants. When a plural matches, the
   plain-English expansion is pluralized to agree, verb included:
   *“study that combines”* → *“studies that combine”*.
2. **Vector-space sense matching** — ambiguous terms carry two cue-word
   vectors, one per sense. The words around each occurrence become a vector
   too, and the term expands only when the context sits closer to the academic
   sense by cosine similarity. Terms marked `strict` (*power*, *mean*,
   *range*) need positive evidence before they expand at all.
3. **Grammar guard** — a term declared a noun is skipped where local grammar
   says it’s a verb (“to construct”, “we construct”).

Words that aren’t ambiguous skip the gate entirely, so the common case stays
fast and predictable.

**Adding your own:** put spelling variants in `TERM_VARIANTS`, different word
classes (verbs, adjectives) in `TERM_DERIVED` — those are glossed in place
rather than substituted, so they can’t break the sentence — and ambiguous
words in `AMBIGUOUS_TERMS` with cue words for each sense.

The statistics glossary (*mean*, *median*, *regression*, *ANOVA*) is off by
default since those words are the most context-dependent of all. Enable it
with `translate_academic_jargon(text, subject, include_statistics=True)`.

### 3. **Content Extraction**

- **Key findings** from results sections
- **Methodology** simplified for general understanding
- **Real-world implications** - why this research matters
- **Professional questions** to ask doctors, teachers, therapists
- **Action items** based on findings

### 4. **Accessibility Enhancement**

- Apply selected modules for specific needs
- Generate visual elements and diagrams
- Create audio-friendly formats
- Adapt for different reading levels

## 🎨 Example Outputs

### Research Finding Translation

**Original:** “The intervention group showed statistically significant improvements on the Beck Depression Inventory (BDI-II) scores (M = 8.4, SD = 3.2) compared to the control group (M = 12.7, SD = 4.1), t(156) = 7.23, p < .001, Cohen’s d = 1.15.”

**Translated:** “People who got the therapy had much lower depression scores than those who didn’t. The improvement was large (depression scores went from about 13 to 8 on a scale where lower is better) and almost certainly wasn’t due to chance.”

**ADHD Module:** Adds progress indicators, highlights key numbers, breaks into bullet points

**Visual Module:** Creates before/after comparison chart

### Methodology Simplification

**Original:** “A randomized, double-blind, placebo-controlled trial with parallel groups…”

**Translated:** “Gold standard study design: People were randomly put into groups, nobody knew who got real treatment vs fake treatment until the end, and we compared the groups…”

## 🚨 Important Notes

**This tool provides understanding, not medical/professional advice.** Always:

- ✅ Consult professionals for important decisions
- ✅ Verify information with experts in the field
- ✅ Check if research applies to your specific situation
- ✅ Look for more recent studies that might update findings

**Accessibility Focus:** Different minds process information differently. Our modular approach means you can customize translation for your specific needs.

**Research Quality:** We help you understand research - we don’t evaluate if it’s good research. Always check study quality, sample size, and limitations.

The `scope` module comes closest to this line, so it is worth being precise about where the line is. It reports **mismatches between a claim and the stated method** — “the headline says *prevents*; the methods say *cross-sectional*, which cannot show cause.” Study design is a fact about the paper. Whether the research is *good* — whether the measures were sensible, the analysis appropriate, the authors honest — is not something a regex can assess, and the module does not try. Every flag it raises quotes the text that triggered it, so you can overrule it.

## 🤝 Contributing

**Help make research accessible to everyone!**

### Add Academic Terms

Know confusing academic jargon? Add translations:

```python
# In academic_translator.py, add to load_academic_jargon():
'your_field': {
    'confusing_term': 'plain English explanation',
}
```

Write the explanation as a **noun phrase** — it gets substituted into the
sentence, so “study following a group over time” works where “following a
group over time” reads badly after “two”.

Plurals and spelling variants are handled automatically. If your term is also
an everyday English word, add it to `AMBIGUOUS_TERMS` in `term_matching.py`
with cue words for each sense, so it only expands where it means the
technical thing.

Then run `python test_academic_translator.py` to check nothing broke.

### Create Accessibility Modules

Build modules for specific learning needs:

- ADHD, dyslexia, autism, visual impairment modules
- Reading level adaptations
- Subject-specific enhancements
- Cultural and language adaptations

### Test Real Papers

The best contributions:

1. Try the tool on research papers you need to understand
1. Report what works well and what needs improvement
1. Share (anonymized) examples of confusing language
1. Suggest better explanations

### Research Areas Needed

- **Climate science** - environmental research translation
- **Computer science** - AI/tech research for general public
- **Economics** - financial research implications
- **Law** - legal research and case law
- **Engineering** - technical innovation research

## 🎖️ Community

**Join researchers, educators, healthcare workers, students, and advocates making knowledge accessible:**

- 🩺 **Healthcare professionals** translating research for patients
- 🎓 **Educators** bringing research into classrooms
- 🧠 **Accessibility advocates** improving learning for all minds
- 📚 **Students** understanding research in other fields
- 👨‍👩‍👧‍👦 **Parents** accessing child development research

## 📄 License

MIT License - Use it, modify it, share it. Let’s democratize human knowledge together.

## 🙏 Acknowledgments

Built for everyone who’s ever stared at an academic paper that could change their life but couldn’t understand it.

**Special thanks to:**

- Researchers who care about public understanding of science
- Educators working with diverse learning needs
- Healthcare workers who translate research for patients
- Parents advocating for evidence-based approaches
- Students who refuse to let academic jargon stop their learning
- Anyone who believes knowledge should be accessible to all minds

-----

## 🐛 Found Issues?

**Tell us:**

- What type of research paper you were processing
- Which modules you applied
- What worked vs. what was confusing
- Confidence score the tool reported

## 💡 Feature Requests

**Especially want to hear from:**

- People with learning differences who need specific accommodations
- Healthcare professionals who translate research for patients
- Teachers who want to use research in classrooms
- Students accessing research outside their field
- Parents researching child development, education, health topics

## 🔮 Roadmap

- [ ] **Web interface** - Upload and translate online
- [ ] **Mobile app** - Accessibility features for phone/tablet
- [ ] **Browser extension** - Translate papers while browsing
- [ ] **API integration** - Connect with research databases
- [ ] **Real-time collaboration** - Team annotation and discussion
- [ ] **Audio generation** - Full paper audio with explanations
- [ ] **Video summaries** - Animated explanations of key concepts
- [ ] **Multi-language** - Translate into other languages
- [ ] **AI tutoring** - Interactive Q&A about research papers

**Together, we can make sure brilliant discoveries reach every mind that needs them.**

-----

*“The best research in the world is useless if people can’t understand it. Let’s change that.”*
