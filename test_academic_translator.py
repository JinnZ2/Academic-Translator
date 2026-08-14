#!/usr/bin/env python3
"""
Tests for Academic Translator.

Uses only the standard library, so it runs anywhere Python does:

    python test_academic_translator.py
    python -m unittest discover
"""

import html.parser
import json
import tempfile
import unittest
from pathlib import Path

from academic_translator import AcademicTranslator, AccessibilityModule

SAMPLE_PAPER = """
Abstract: This randomized controlled trial evaluated whether a supervised exercise
intervention improves glycemic control in adults with type 2 diabetes.

Methods: We enrolled 240 participants (n = 240) at three clinical sites. Participants
were randomly assigned to the experimental group or a control group receiving usual
care from their doctor. Sample size was determined by a power analysis.

Results: Participants receiving the treatment demonstrated statistically significant
improvements compared to controls (p < 0.001). Mean HbA1c fell by 0.7 percent in the
treatment group versus 0.1 percent in controls.

Discussion: These findings suggest that structured exercise should be considered as
adjunct therapy. Limitations of this study include a short follow-up window.
"""


class TagBalanceParser(html.parser.HTMLParser):
    """Minimal well-formedness check for the generated report"""

    VOID = {'meta', 'br', 'hr', 'img', 'link', 'input'}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"unexpected </{tag}>")


class TranslatorCoreTests(unittest.TestCase):
    def setUp(self):
        self.translator = AcademicTranslator()

    def test_detects_medical_subject(self):
        self.assertEqual(self.translator.detect_subject_area(SAMPLE_PAPER), 'medical')

    def test_unmatched_text_falls_back_to_general(self):
        self.assertEqual(
            self.translator.detect_subject_area("colorless green ideas sleep furiously"),
            'general',
        )

    def test_jargon_is_expanded_once(self):
        translated = self.translator.translate_academic_jargon(
            "The control group used a placebo.", 'medical'
        )
        self.assertIn("comparison group that didn't get the treatment (control group)", translated)
        # A term must not be re-translated inside an earlier expansion.
        self.assertEqual(translated.count('control group'), 1)

    def test_jargon_expansion_does_not_cascade(self):
        # 'sample size' expands to text containing 'studied'; 'correlation'
        # expands to text containing 'cause'. Neither may be re-expanded.
        translated = self.translator.translate_academic_jargon(
            "Correlation is not causation. Sample size matters.", 'general'
        )
        self.assertEqual(translated.count('(Correlation)'), 1)
        self.assertEqual(translated.count('(causation)'), 1)
        self.assertEqual(translated.count('(Sample size)'), 1)

    def test_statistical_shorthand_is_translated(self):
        translated = self.translator.translate_academic_jargon("n = 240, p < 0.05", 'general')
        self.assertIn('number of people/things studied:', translated)
        self.assertIn('probability this happened by chance:', translated)

    def test_explain_term_searches_every_glossary(self):
        self.assertEqual(self.translator.explain_term('ANOVA'), 'test to compare averages between groups')
        self.assertEqual(self.translator.explain_term('mortality'), 'death rate')
        self.assertIsNone(self.translator.explain_term('not a real term'))

    def test_reading_level_handles_empty_text(self):
        self.assertEqual(self.translator.calculate_reading_level(""), "Unknown")

    def test_reading_level_of_dense_text(self):
        self.assertEqual(
            self.translator.calculate_reading_level(SAMPLE_PAPER),
            "Graduate/Professional",
        )

    def test_findings_and_methods_are_extracted(self):
        result = self.translator.translate_academic_document(SAMPLE_PAPER)
        self.assertTrue(result.key_findings)
        self.assertTrue(result.methodology_simplified)
        self.assertTrue(result.questions_to_ask)
        self.assertTrue(0.3 <= result.confidence_score <= 0.95)

    def test_findings_are_deduplicated(self):
        findings = self.translator.extract_key_findings(SAMPLE_PAPER, 'medical')
        self.assertEqual(len(findings), len({f.lower() for f in findings}))

    def test_subject_override_is_honored(self):
        result = self.translator.translate_academic_document(SAMPLE_PAPER, subject_area='education')
        self.assertEqual(result.subject_area, 'education')

    def test_unsupported_file_type_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.xyz"
            path.write_text("content", encoding='utf-8')
            with self.assertRaises(ValueError):
                self.translator.extract_text_from_file(str(path))

    def test_missing_file_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.translator.extract_text_from_file("/nonexistent/paper.txt")

    def test_reads_plain_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.txt"
            path.write_text(SAMPLE_PAPER, encoding='utf-8')
            self.assertIn("randomized controlled trial",
                          self.translator.extract_text_from_file(str(path)))


class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.translator = AcademicTranslator()

    def test_all_shipped_modules_are_discovered(self):
        self.assertEqual(
            sorted(self.translator.available_modules),
            ['adhd_module', 'dyslexia_module', 'visual_module'],
        )

    def test_modules_load_by_short_and_full_name(self):
        for short_name in ('adhd', 'dyslexia', 'visual'):
            with self.subTest(module=short_name):
                by_short = self.translator.load_module(short_name)
                by_full = self.translator.load_module(f"{short_name}_module")
                self.assertIsInstance(by_short, AccessibilityModule)
                self.assertIs(by_short, by_full)
                self.assertTrue(by_short.get_name())
                self.assertTrue(by_short.get_description())

    def test_unknown_module_returns_none(self):
        self.assertIsNone(self.translator.load_module('telepathy'))

    def test_modules_transform_text_and_add_elements(self):
        for short_name in ('adhd', 'dyslexia', 'visual'):
            with self.subTest(module=short_name):
                module = self.translator.load_module(short_name)
                context = {'subject_area': 'medical', 'reading_level': 'College'}

                processed = module.process_text(SAMPLE_PAPER, context)
                self.assertIsInstance(processed, str)
                self.assertNotEqual(processed.strip(), "")

                extras = module.get_additional_elements(SAMPLE_PAPER, context)
                self.assertTrue(extras['visual_elements'])
                self.assertTrue(extras['action_items'])

    def test_translation_records_applied_modules(self):
        result = self.translator.translate_academic_document(
            SAMPLE_PAPER, modules=['adhd', 'visual']
        )
        self.assertEqual(
            result.modules_applied,
            ['ADHD-Friendly Format', 'Visual Processing Support'],
        )
        self.assertTrue(result.action_items)
        self.assertTrue(result.visual_elements)

    def test_unknown_module_does_not_abort_translation(self):
        result = self.translator.translate_academic_document(
            SAMPLE_PAPER, modules=['telepathy']
        )
        self.assertEqual(result.modules_applied, [])
        self.assertTrue(result.plain_english)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.translator = AcademicTranslator()
        self.result = self.translator.translate_academic_document(
            SAMPLE_PAPER, modules=['adhd'], source_file='paper.txt'
        )

    def test_html_report_is_well_formed(self):
        parser = TagBalanceParser()
        parser.feed(self.translator.generate_html_report(self.result))
        self.assertEqual(parser.errors, [])
        self.assertEqual(parser.stack, [])

    def test_html_report_escapes_source_text(self):
        result = self.translator.translate_academic_document(
            SAMPLE_PAPER + "\n<script>alert('xss')</script>\n"
        )
        report = self.translator.generate_html_report(result)
        self.assertNotIn("<script>alert", report)
        self.assertIn("&lt;script&gt;", report)

    def test_saves_json_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = self.translator.save_translation(self.result, "report", tmp)

            self.assertTrue(saved['html'].exists())
            self.assertTrue(saved['json'].exists())

            data = json.loads(saved['json'].read_text(encoding='utf-8'))
            self.assertEqual(data['source_file'], 'paper.txt')
            self.assertEqual(data['subject_area'], self.result.subject_area)

    def test_creates_nested_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "reports"
            saved = self.translator.save_translation(self.result, "report", str(target))
            self.assertTrue(saved['html'].exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
