#!/usr/bin/env python3
"""
Academic Translator - Making ALL Knowledge Accessible to ALL Minds

Translates academic papers, research studies, and technical documents into formats
that work for different learning styles, reading levels, and cognitive differences.

Modular architecture allows community contributions for specific accessibility needs.
"""

import argparse
import html
import importlib.util
import json
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Running this file as a script would normally make it "__main__", so a module
# doing `from academic_translator import AccessibilityModule` would import a
# *second* copy of this file and get a different AccessibilityModule class -
# breaking every issubclass() check in load_module(). Aliasing keeps one copy.
if __name__ == "__main__" and "academic_translator" not in sys.modules:
    sys.modules["academic_translator"] = sys.modules["__main__"]

# Document readers are optional: plain text works with no third-party packages
# at all, and you should not need a PDF library installed to translate a .txt.
try:
    import fitz  # PyMuPDF - best text extraction for academic layouts
except ImportError:
    fitz = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None


@dataclass
class AcademicTranslationResult:
    original_text: str
    plain_english: str
    key_findings: List[str]
    why_this_matters: List[str]
    methodology_simplified: List[str]
    questions_to_ask: List[str]
    action_items: List[str]
    visual_elements: List[str]
    confidence_score: float
    subject_area: str
    reading_level: str
    modules_applied: List[str] = field(default_factory=list)
    source_file: str = "Direct input"


class AccessibilityModule(ABC):
    """Base class for all accessibility modules"""

    @abstractmethod
    def get_name(self) -> str:
        """Return module name"""

    @abstractmethod
    def get_description(self) -> str:
        """Return module description"""

    @abstractmethod
    def process_text(self, text: str, context: Dict) -> str:
        """Process text according to module's accessibility needs"""

    @abstractmethod
    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Return additional elements this module provides"""


class AcademicTranslator:
    def __init__(self):
        self.academic_jargon = self.load_academic_jargon()
        self.subject_patterns = self.load_subject_patterns()
        self.methodology_keywords = self.load_methodology_keywords()
        self.loaded_modules = {}
        self.available_modules = self.discover_modules()

    def load_academic_jargon(self) -> Dict[str, Dict[str, str]]:
        """Academic jargon translation dictionary organized by field"""
        return {
            'general_research': {
                'methodology': 'how the study was done',
                'literature review': 'summary of previous research on this topic',
                'hypothesis': 'educated guess about what would happen',
                'null hypothesis': 'assumption that there\'s no real effect',
                'sample size': 'number of people/things studied',
                'control group': 'comparison group that didn\'t get the treatment',
                'experimental group': 'group that got the treatment being tested',
                'placebo': 'fake treatment with no active ingredient',
                'double-blind': 'neither participants nor researchers knew who got real treatment',
                'randomized': 'people were randomly assigned to groups',
                'correlation': 'things that tend to happen together (doesn\'t prove cause)',
                'causation': 'one thing actually causes another',
                'statistical significance': 'result is probably not due to chance',
                'p-value': 'probability the result happened by accident',
                'confidence interval': 'range where the true answer probably lies',
                'peer review': 'other experts checked this research before publication',
                'replication': 'repeating the study to see if results hold up',
                'meta-analysis': 'study that combines results from multiple studies',
            },
            'medical': {
                'clinical trial': 'research study testing treatments on people',
                'randomized controlled trial': 'gold standard study where people are randomly assigned treatments',
                'cohort study': 'following a group of people over time',
                'case-control study': 'comparing people with a condition to those without',
                'systematic review': 'comprehensive summary of all research on a topic',
                'efficacy': 'how well treatment works in ideal conditions',
                'effectiveness': 'how well treatment works in real-world conditions',
                'adverse events': 'bad side effects',
                'contraindication': 'reason not to use this treatment',
                'comorbidity': 'having multiple health conditions at once',
                'prevalence': 'how common a condition is',
                'incidence': 'how many new cases occur in a time period',
                'mortality': 'death rate',
                'morbidity': 'illness rate',
                'biomarker': 'measurable sign of disease or treatment effect',
                'pharmacokinetics': 'how the body processes medication',
                'pharmacodynamics': 'how medication affects the body',
            },
            'psychology': {
                'construct': 'concept being measured (like intelligence or depression)',
                'validity': 'whether a test measures what it claims to measure',
                'reliability': 'whether a test gives consistent results',
                'operational definition': 'exact way researchers define and measure something',
                'confounding variable': 'outside factor that might affect results',
                'cognitive bias': 'systematic error in thinking',
                'effect size': 'how big the difference actually is (practical importance)',
                'standard deviation': 'measure of how spread out the data is',
                'normal distribution': 'bell curve - most people in the middle, few at extremes',
                'outlier': 'unusual result that doesn\'t fit the pattern',
            },
            'education': {
                'pedagogical': 'related to teaching methods',
                'scaffolding': 'providing support that\'s gradually removed as students learn',
                'differentiation': 'adapting teaching for different student needs',
                'formative assessment': 'checking understanding during learning',
                'summative assessment': 'final test of what was learned',
                'metacognition': 'thinking about thinking - awareness of your own learning',
                'zone of proximal development': 'sweet spot between too easy and too hard',
                'intrinsic motivation': 'motivation from internal satisfaction',
                'extrinsic motivation': 'motivation from external rewards',
            },
            'social_science': {
                'qualitative research': 'studying experiences, meanings, and perspectives',
                'quantitative research': 'studying numbers and statistics',
                'ethnography': 'studying culture by observing and participating',
                'phenomenology': 'studying people\'s lived experiences',
                'grounded theory': 'developing theory from data rather than testing existing theory',
                'triangulation': 'using multiple methods to confirm findings',
                'thick description': 'rich, detailed account of what was observed',
                'reflexivity': 'researcher reflecting on how they might bias the study',
            },
            'statistics': {
                'mean': 'average',
                'median': 'middle value when all values are arranged in order',
                'mode': 'most common value',
                'range': 'difference between highest and lowest values',
                'variance': 'measure of how spread out data is',
                'regression': 'method to predict one variable from others',
                'anova': 'test to compare averages between groups',
                't-test': 'test to compare averages between two groups',
                'chi-square': 'test for relationships between categories',
                'power': 'ability of a test to detect a real effect',
                'type i error': 'false positive - finding an effect that isn\'t really there',
                'type ii error': 'false negative - missing a real effect',
            }
        }

    def load_subject_patterns(self) -> Dict[str, Dict]:
        """Patterns to identify different academic subjects"""
        return {
            'medical': {
                'keywords': ['patient', 'clinical', 'treatment', 'therapy', 'diagnosis', 'symptoms', 'disease', 'health', 'medical', 'hospital', 'doctor', 'physician', 'nurse', 'medication', 'drug', 'surgery', 'intervention'],
                'journals': ['nejm', 'lancet', 'jama', 'bmj', 'nature medicine', 'cell', 'science translational medicine'],
                'methods': ['randomized controlled trial', 'clinical trial', 'cohort study', 'case-control', 'systematic review', 'meta-analysis']
            },
            'psychology': {
                'keywords': ['behavior', 'cognitive', 'mental', 'psychological', 'emotion', 'personality', 'memory', 'learning', 'perception', 'consciousness', 'therapy', 'depression', 'anxiety'],
                'journals': ['psychological science', 'journal of personality', 'cognitive psychology', 'developmental psychology'],
                'methods': ['survey', 'experiment', 'longitudinal study', 'cross-sectional', 'qualitative interview']
            },
            'education': {
                'keywords': ['student', 'learning', 'teaching', 'classroom', 'curriculum', 'pedagogy', 'instruction', 'academic achievement', 'educational', 'school'],
                'journals': ['journal of educational psychology', 'educational researcher', 'review of educational research'],
                'methods': ['action research', 'case study', 'mixed methods', 'educational intervention']
            },
            'social_science': {
                'keywords': ['social', 'society', 'culture', 'community', 'policy', 'economic', 'political', 'demographic', 'inequality', 'justice'],
                'journals': ['american sociological review', 'social forces', 'sociology of education'],
                'methods': ['ethnography', 'survey research', 'content analysis', 'field study']
            },
            'science': {
                'keywords': ['experiment', 'hypothesis', 'theory', 'model', 'analysis', 'data', 'results', 'conclusion', 'research', 'study'],
                'journals': ['nature', 'science', 'cell', 'pnas', 'journal of biological chemistry'],
                'methods': ['laboratory experiment', 'field study', 'modeling', 'simulation']
            }
        }

    def load_methodology_keywords(self) -> Dict[str, str]:
        """Common research methodology terms simplified"""
        return {
            'n =': 'number of people/things studied:',
            'p <': 'probability this happened by chance:',
            'r =': 'strength of relationship:',
            'f =': 'statistical test result:',
            't =': 'statistical test result:',
            'χ² =': 'chi-square test result:',
            'df =': 'degrees of freedom (technical statistical term):',
            'ci =': 'confidence interval (range where true answer likely falls):',
            'm =': 'average:',
            'sd =': 'standard deviation (how spread out the data is):',
        }

    # ------------------------------------------------------------------
    # Accessibility modules
    # ------------------------------------------------------------------

    @property
    def modules_dir(self) -> Path:
        return Path(__file__).resolve().parent / 'modules'

    def discover_modules(self) -> List[str]:
        """Discover available accessibility modules"""
        if not self.modules_dir.exists():
            return []

        return sorted(path.stem for path in self.modules_dir.glob('*_module.py'))

    def resolve_module_name(self, module_name: str) -> Optional[str]:
        """Accept both 'adhd' and 'adhd_module' as ways to name a module"""
        if module_name in self.available_modules:
            return module_name

        suffixed = f"{module_name}_module"
        if suffixed in self.available_modules:
            return suffixed

        return None

    def load_module(self, module_name: str) -> Optional[AccessibilityModule]:
        """Load a specific accessibility module"""
        resolved = self.resolve_module_name(module_name)
        if resolved is None:
            print(f"Unknown module: {module_name}")
            return None

        if resolved in self.loaded_modules:
            return self.loaded_modules[resolved]

        # Load by file path so modules work no matter which directory the
        # translator is invoked from.
        spec = importlib.util.spec_from_file_location(
            f"academic_translator_modules.{resolved}",
            self.modules_dir / f"{resolved}.py",
        )

        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:
            print(f"Could not load module {resolved}: {exc}")
            return None

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, AccessibilityModule)
                    and attr is not AccessibilityModule):

                instance = attr()
                self.loaded_modules[resolved] = instance
                return instance

        print(f"No AccessibilityModule subclass found in {resolved}")
        return None

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def detect_subject_area(self, text: str) -> str:
        """Identify the academic subject area"""
        text_lower = text.lower()

        scores = {}
        for subject, patterns in self.subject_patterns.items():
            score = 0

            # Check keywords
            for keyword in patterns['keywords']:
                score += text_lower.count(keyword) * 2

            # Check journal patterns
            for journal in patterns.get('journals', []):
                if journal.lower() in text_lower:
                    score += 5

            # Check methodology patterns
            for method in patterns.get('methods', []):
                if method.lower() in text_lower:
                    score += 3

            scores[subject] = score

        best = max(scores, key=scores.get) if scores else 'general'

        # Nothing matched at all - don't claim a subject we didn't detect.
        return best if scores.get(best, 0) > 0 else 'general'

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various academic document formats"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"No such file: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self.extract_text_from_pdf(str(file_path))
        elif suffix in ['.docx', '.doc']:
            return self.extract_text_from_docx(str(file_path))
        elif suffix in ['.txt', '.text', '.md']:
            try:
                return file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                return file_path.read_text(encoding='latin-1')
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF - academic papers often have complex layouts"""
        text = ""

        if fitz is None and PyPDF2 is None:
            raise ImportError(
                "Reading PDFs needs PyMuPDF or PyPDF2. Install with: "
                "pip install -r requirements.txt"
            )

        if fitz is not None:
            try:
                # Try PyMuPDF first (better for academic papers)
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                doc.close()

                if len(text.strip()) > 100:
                    return text

            except Exception as e:
                print(f"PyMuPDF failed: {e}, trying PyPDF2...")

        if PyPDF2 is not None:
            try:
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""

            except Exception as e:
                print(f"PyPDF2 also failed: {e}")
                return ""

        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word documents"""
        if Document is None:
            raise ImportError(
                "Reading Word documents needs python-docx. Install with: "
                "pip install -r requirements.txt"
            )

        try:
            doc = Document(file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception as e:
            print(f"Error reading Word document: {e}")
            return ""

    def translate_academic_jargon(self, text: str, subject_area: str) -> str:
        """Replace academic jargon with plain English"""
        replacements = {}
        replacements.update(self.academic_jargon['general_research'])
        if subject_area in self.academic_jargon:
            replacements.update(self.academic_jargon[subject_area])

        # One combined pass, longest term first. Replacing term-by-term would
        # let an earlier replacement's plain English get re-translated by a
        # later term, garbling the output.
        term_patterns = [
            r'\b' + re.escape(term) + r'\b'
            for term in sorted(replacements, key=len, reverse=True)
        ]
        term_patterns += [
            re.escape(term)
            for term in sorted(self.methodology_keywords, key=len, reverse=True)
        ]

        lookup = {term.lower(): plain for term, plain in replacements.items()}
        stat_lookup = {
            term.lower(): plain
            for term, plain in self.methodology_keywords.items()
        }

        def substitute(match: re.Match) -> str:
            matched = match.group(0)
            key = matched.lower()

            if key in lookup:
                return f"{lookup[key]} ({matched})"
            if key in stat_lookup:
                return stat_lookup[key]
            return matched

        return re.sub('|'.join(term_patterns), substitute, text, flags=re.IGNORECASE)

    def explain_term(self, term: str) -> Optional[str]:
        """Look up a single academic term across every field's glossary"""
        needle = term.strip().lower()

        for field_terms in self.academic_jargon.values():
            for jargon, plain in field_terms.items():
                if jargon.lower() == needle:
                    return plain

        return None

    def extract_key_findings(self, text: str, subject_area: str) -> List[str]:
        """Extract the main research findings"""
        findings = []

        # Look for results/findings sections
        results_patterns = [
            r'(?:results?|findings?|outcomes?)[:\s]([^.]*(?:\.[^.]*){0,2})',
            r'(?:we found|our findings|the study found|results showed)[:\s]([^.]*(?:\.[^.]*){0,2})',
            r'(?:conclusion|conclusions)[:\s]([^.]*(?:\.[^.]*){0,2})'
        ]

        for pattern in results_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                finding = match.group(1).strip()
                if len(finding) > 20:  # Filter out very short matches
                    findings.append(f"🔍 {finding}")

        # Look for statistically significant results
        sig_patterns = [
            r'(p\s*[<>=]\s*0\.0[0-5][^.]*)',
            r'(significant(?:ly)?\s+[^.]*)',
            r'([^.]*significant\s+(?:difference|effect|relationship)[^.]*)'
        ]

        for pattern in sig_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                result = match.group(1).strip()
                findings.append(f"📊 {result}")

        return self._dedupe(findings)[:8]  # Limit to most important

    def extract_methodology_simplified(self, text: str, subject_area: str) -> List[str]:
        """Simplify the research methods section"""
        methods = []

        # Look for methods section
        methods_patterns = [
            r'(?:methods?|methodology|procedure|design)[:\s]([^.]*(?:\.[^.]*){0,3})',
            r'(?:participants?|subjects?)[:\s]([^.]*(?:\.[^.]*){0,2})',
            r'(?:data collection|analysis)[:\s]([^.]*(?:\.[^.]*){0,2})'
        ]

        for pattern in methods_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                method = match.group(1).strip()
                if len(method) > 15:
                    methods.append(f"⚙️ {method}")

        # Look for sample size information
        sample_patterns = [
            r'(n\s*=\s*\d+[^.]*)',
            r'(\d+\s+(?:participants?|subjects?|patients?)[^.]*)',
            r'(sample\s+(?:of|size)[^.]*\d+[^.]*)'
        ]

        for pattern in sample_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                sample_info = match.group(1).strip()
                methods.append(f"👥 {sample_info}")

        return self._dedupe(methods)[:6]

    def generate_why_this_matters(self, text: str, subject_area: str) -> List[str]:
        """Generate "why this matters" explanations"""
        matters = []

        # Subject-specific implications
        if subject_area == 'medical':
            matters.extend([
                "💊 Could lead to better treatments for patients",
                "🏥 May change how doctors diagnose or treat conditions",
                "⚠️ Might reveal new risks or benefits of treatments",
                "🔬 Advances our understanding of how the body works"
            ])
        elif subject_area == 'psychology':
            matters.extend([
                "🧠 Helps us understand how the mind works",
                "🤝 Could improve relationships and social interactions",
                "📚 May change how we approach learning and education",
                "💭 Provides insights into human behavior and decision-making"
            ])
        elif subject_area == 'education':
            matters.extend([
                "🎓 Could improve how students learn",
                "👩‍🏫 May help teachers be more effective",
                "📈 Might boost academic achievement",
                "🌍 Could reduce educational inequalities"
            ])

        # Look for implications/discussion sections
        impl_patterns = [
            r'(?:implications?|significance|impact)[:\s]([^.]*(?:\.[^.]*){0,2})',
            r'(?:these findings|our results|this study)\s+(?:suggest|indicate|show)[s]?\s+([^.]*)',
            r'(?:clinical|practical|policy)\s+implications[:\s]([^.]*)'
        ]

        for pattern in impl_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                implication = match.group(1).strip()
                if len(implication) > 20:
                    matters.append(f"🎯 {implication}")

        return self._dedupe(matters)[:6]

    def generate_questions_to_ask(self, text: str, subject_area: str) -> List[str]:
        """Generate questions people should ask professionals"""
        questions = []

        if subject_area == 'medical':
            questions.extend([
                "🩺 Ask your doctor: 'Does this research apply to my specific condition?'",
                "💊 'Should I change my current treatment based on this?'",
                "⚠️ 'What are the risks and benefits for someone like me?'",
                "🔍 'Are there clinical trials I could participate in?'"
            ])
        elif subject_area == 'psychology':
            questions.extend([
                "🧠 Ask a therapist: 'How might this apply to my situation?'",
                "📚 'Could this research help me understand my behavior better?'",
                "🤝 'How can I use this information in my relationships?'"
            ])
        elif subject_area == 'education':
            questions.extend([
                "👩‍🏫 Ask teachers: 'How could this improve my child's learning?'",
                "📖 'Should we change our study methods based on this?'",
                "🎓 'What does this mean for educational policy?'"
            ])

        # Look for limitations mentioned in the study
        if re.search(r'limitation[s]?\s+(?:of this study\s+)?(?:include|are)[:\s]', text, re.IGNORECASE):
            questions.append(
                "❓ Ask experts: 'How do the study limitations affect the conclusions?'"
            )

        return self._dedupe(questions)[:6]

    def calculate_reading_level(self, text: str) -> str:
        """Estimate reading level of the text"""
        # Simple reading level estimation based on sentence length and word complexity
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()

        if not sentences or not words:
            return "Unknown"

        avg_sentence_length = len(words) / len(sentences)

        # Count complex words (3+ syllables, rough estimate)
        sample = words[:1000]
        complex_words = sum(1 for word in sample if len(word) > 6)
        complex_ratio = complex_words / len(sample)

        # Very rough reading level estimation
        if avg_sentence_length < 15 and complex_ratio < 0.1:
            return "Middle School"
        elif avg_sentence_length < 20 and complex_ratio < 0.15:
            return "High School"
        elif avg_sentence_length < 25 and complex_ratio < 0.2:
            return "College"
        else:
            return "Graduate/Professional"

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        """Drop repeats while keeping the original order"""
        seen = set()
        unique = []

        for item in items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    def translate_academic_document(self, text: str, modules: List[str] = None,
                                    source_file: str = None,
                                    subject_area: str = None) -> AcademicTranslationResult:
        """Main translation function with modular accessibility support"""

        # Detect subject area (unless the caller told us what it is)
        subject_area = subject_area or self.detect_subject_area(text)
        reading_level = self.calculate_reading_level(text)

        # Apply core translation
        plain_text = self.translate_academic_jargon(text, subject_area)

        # Extract core information
        key_findings = self.extract_key_findings(text, subject_area)
        methodology = self.extract_methodology_simplified(text, subject_area)
        why_matters = self.generate_why_this_matters(text, subject_area)
        questions = self.generate_questions_to_ask(text, subject_area)

        # Apply accessibility modules
        applied_modules = []
        additional_elements = {'visual_elements': [], 'action_items': []}

        for module_name in modules or []:
            module = self.load_module(module_name)
            if not module:
                continue

            context = {
                'subject_area': subject_area,
                'reading_level': reading_level,
                'key_findings': key_findings
            }

            # Apply module transformations
            plain_text = module.process_text(plain_text, context)

            # Get additional elements
            module_elements = module.get_additional_elements(text, context)
            for key, values in module_elements.items():
                if key in additional_elements:
                    additional_elements[key].extend(values)

            applied_modules.append(module.get_name())

        confidence = self.calculate_confidence(text, subject_area, applied_modules)

        return AcademicTranslationResult(
            original_text=text,
            plain_english=plain_text,
            key_findings=key_findings,
            why_this_matters=why_matters,
            methodology_simplified=methodology,
            questions_to_ask=questions,
            action_items=additional_elements.get('action_items', []),
            visual_elements=additional_elements.get('visual_elements', []),
            confidence_score=confidence,
            subject_area=subject_area,
            reading_level=reading_level,
            modules_applied=applied_modules,
            source_file=source_file or "Direct input"
        )

    def calculate_confidence(self, text: str, subject_area: str, modules: List[str]) -> float:
        """Calculate confidence in translation quality"""
        base_score = 0.7

        # Boost for recognized subject area
        if subject_area != 'general':
            base_score += 0.1

        # Boost for finding key research elements
        if re.search(r'(?:results?|findings?|conclusion)', text, re.IGNORECASE):
            base_score += 0.1
        if re.search(r'(?:methods?|methodology)', text, re.IGNORECASE):
            base_score += 0.1

        # Boost for applied modules
        base_score += len(modules) * 0.02

        # Penalize very short or very long texts
        if len(text) < 1000:
            base_score -= 0.1
        elif len(text) > 50000:
            base_score -= 0.1

        return max(0.3, min(0.95, base_score))

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def save_translation(self, result: AcademicTranslationResult, filename: str,
                         output_dir: str = "academic_translations") -> Dict[str, Path]:
        """Save translation results"""
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)

        json_path = directory / f"{filename}.json"
        html_path = directory / f"{filename}.html"

        json_path.write_text(
            json.dumps(asdict(result), indent=2, ensure_ascii=False),
            encoding='utf-8',
        )
        html_path.write_text(self.generate_html_report(result), encoding='utf-8')

        return {'json': json_path, 'html': html_path}

    def generate_html_report(self, result: AcademicTranslationResult) -> str:
        """Generate comprehensive HTML report"""

        def list_items(items: List[str]) -> str:
            return "".join(f"<li>{html.escape(item)}</li>" for item in items)

        def optional_section(title: str, items: List[str]) -> str:
            if not items:
                return ""
            return f"""
    <div class="section">
        <h2>{title}</h2>
        <ul>
        {list_items(items)}
        </ul>
    </div>"""

        paragraphs = "".join(
            f'<p style="text-align: justify; line-height: 1.8;">{html.escape(para)}</p>'
            for para in result.plain_english.split("\n") if para.strip()
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Academic Translation: {html.escape(result.subject_area.title())}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .subject {{ font-size: 28px; font-weight: bold; }}
        .reading-level {{ font-size: 16px; opacity: 0.9; margin-top: 10px; }}
        .modules {{ font-size: 14px; margin-top: 15px; }}
        .section {{ margin: 25px 0; padding: 20px; border-left: 5px solid #667eea; background: #f8faff; border-radius: 5px; }}
        .findings {{ border-left-color: #4CAF50; background: #f8fff8; }}
        .methodology {{ border-left-color: #FF9800; background: #fff8f0; }}
        .matters {{ border-left-color: #E91E63; background: #fdf8fb; }}
        .questions {{ border-left-color: #9C27B0; background: #faf8ff; }}
        .confidence {{ text-align: center; font-size: 20px; margin: 30px 0; padding: 15px; background: #e3f2fd; border-radius: 8px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 10px 0; }}
        .key-point {{ font-weight: bold; color: #1976D2; }}
        h2 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .visual-note {{ background: #fff3e0; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ff9800; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="subject">📚 {html.escape(result.subject_area.title())} Research Translation</div>
        <div class="reading-level">📖 Original Reading Level: {html.escape(result.reading_level)}</div>
        <div class="modules">🔧 Accessibility Modules Applied: {html.escape(', '.join(result.modules_applied)) if result.modules_applied else 'None'}</div>
    </div>

    <div class="confidence">
        <strong>🎯 Translation Confidence: {result.confidence_score:.0%}</strong>
    </div>

    <div class="section findings">
        <h2>🔍 Key Findings (What They Discovered)</h2>
        <ul>
        {list_items(result.key_findings)}
        </ul>
    </div>

    <div class="section matters">
        <h2>🎯 Why This Matters (Real-World Impact)</h2>
        <ul>
        {list_items(result.why_this_matters)}
        </ul>
    </div>

    <div class="section methodology">
        <h2>⚙️ How They Did It (Methods Simplified)</h2>
        <ul>
        {list_items(result.methodology_simplified)}
        </ul>
    </div>

    <div class="section questions">
        <h2>❓ Questions to Ask Professionals</h2>
        <ul>
        {list_items(result.questions_to_ask)}
        </ul>
    </div>
{optional_section("🎬 Visual Elements", result.visual_elements)}
{optional_section("📋 Action Items", result.action_items)}

    <div class="section">
        <h2>📖 Full Translation</h2>
        <div class="visual-note">
            <strong>💡 Reading Tip:</strong> Technical terms are explained in parentheses. Look for colored highlights if you're using accessibility modules.
        </div>
        {paragraphs}
    </div>

    <hr style="margin: 40px 0;">
    <div style="text-align: center; color: #666; font-size: 14px;">
        <p><strong>Academic Translator</strong> - Making knowledge accessible to all minds</p>
        <p>Source: {html.escape(result.source_file)}</p>
        <p><em>This translation provides information, not professional advice. Always consult experts for important decisions.</em></p>
    </div>
</body>
</html>
"""


def main():
    """Command line interface for academic translation"""
    translator = AcademicTranslator()

    # Offer whatever modules are actually installed, rather than a hardcoded
    # list that promises modules nobody has written yet.
    module_choices = sorted(
        {name for name in translator.available_modules}
        | {name[:-len('_module')] for name in translator.available_modules}
    )

    parser = argparse.ArgumentParser(description='Translate academic papers into accessible formats')
    parser.add_argument('--file', '-f', help='Academic paper file (PDF, DOCX, TXT)')
    parser.add_argument('--text', '-t', help='Direct text input')
    parser.add_argument('--modules', '-m', nargs='*', default=[],
                        help='Accessibility modules to apply', choices=module_choices)
    parser.add_argument('--subject', '-s', help='Subject area override',
                        choices=['medical', 'psychology', 'education', 'social_science', 'science'])
    parser.add_argument('--output', '-o', help='Output filename')
    parser.add_argument('--output-dir', default='academic_translations',
                        help='Directory for saved reports (default: academic_translations)')
    parser.add_argument('--list-modules', action='store_true', help='List available modules')

    args = parser.parse_args()

    if args.list_modules:
        print("📚 Available Accessibility Modules:")
        if not translator.available_modules:
            print("   (none found in modules/)")
        for module_name in translator.available_modules:
            module = translator.load_module(module_name)
            if module:
                short_name = module_name[:-len('_module')]
                print(f"   • {short_name}: {module.get_name()} - {module.get_description()}")
        return 0

    # Get text input
    if args.file:
        print(f"📄 Reading academic document: {args.file}")
        try:
            text = translator.extract_text_from_file(args.file)
        except (FileNotFoundError, ValueError, ImportError) as exc:
            print(f"❌ {exc}")
            return 1
        source_file = args.file
    elif args.text:
        text = args.text
        source_file = "Direct input"
    else:
        print("❌ Please provide --file or --text")
        return 1

    if not text or len(text.strip()) < 200:
        print("❌ Not enough text to translate (need at least 200 characters)")
        return 1

    print(f"🧠 Analyzing academic content ({len(text):,} characters)...")

    # Apply modules
    modules = args.modules or []
    if modules:
        print(f"🔧 Applying accessibility modules: {', '.join(modules)}")

    # Translate
    result = translator.translate_academic_document(
        text,
        modules=modules,
        source_file=source_file,
        subject_area=args.subject,
    )

    # Show results
    print(f"\n📚 Subject Area: {result.subject_area.title()}")
    print(f"📖 Reading Level: {result.reading_level}")
    print(f"🎯 Translation Confidence: {result.confidence_score:.0%}")

    if result.key_findings:
        print(f"\n🔍 Key Findings ({len(result.key_findings)} found):")
        for finding in result.key_findings[:3]:
            print(f"   {finding}")

    if result.why_this_matters:
        print(f"\n💡 Why This Matters ({len(result.why_this_matters)} reasons):")
        for matter in result.why_this_matters[:3]:
            print(f"   {matter}")

    if result.questions_to_ask:
        print(f"\n❓ Questions to Ask Experts ({len(result.questions_to_ask)} suggestions):")
        for question in result.questions_to_ask[:2]:
            print(f"   {question}")

    # Save detailed report
    output_name = args.output or f"{result.subject_area}_research_translation"
    output_name = re.sub(r'[^a-zA-Z0-9_]', '_', output_name)

    saved = translator.save_translation(result, output_name, args.output_dir)
    print(f"\n💾 Full translation saved: {saved['html']}")

    if result.modules_applied:
        print(f"🔧 Modules applied: {', '.join(result.modules_applied)}")

    print(f"\n✨ This research is now accessible to {result.reading_level.lower()} readers!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
