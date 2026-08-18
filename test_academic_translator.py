#!/usr/bin/env python3
"""
Tests for Academic Translator.

Uses only the standard library, so it runs anywhere Python does:

    python test_academic_translator.py
    python -m unittest discover
"""

import html.parser
import json
import re
import tempfile
import unittest
from pathlib import Path

from academic_translator import AcademicTranslator, AccessibilityModule
from modules.beginner_reading import verb_forms
from term_matching import (
    SenseProfile,
    TermMatcher,
    TermSense,
    count_tokens,
    pluralize_expansion,
    pluralize_term,
    singularize_expansion,
)

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


class InflectionTests(unittest.TestCase):
    """Terms must be caught in the forms papers actually write them in"""

    def setUp(self):
        self.translator = AcademicTranslator()

    def translate(self, text, subject='medical'):
        return self.translator.translate_academic_jargon(text, subject)

    def test_irregular_plurals_are_matched(self):
        self.assertIn('(hypotheses)', self.translate("Three hypotheses were tested."))
        self.assertIn('(meta-analyses)', self.translate("Two meta-analyses agreed."))

    def test_regular_plurals_are_matched(self):
        self.assertIn('(clinical trials)', self.translate("Two clinical trials ran."))
        self.assertIn('(biomarkers)', self.translate("The biomarkers were measured."))
        self.assertIn('(cohort studies)', self.translate("Both cohort studies agreed."))

    def test_plural_match_pluralizes_the_expansion(self):
        self.assertIn(
            'educated guesses about what would happen (hypotheses)',
            self.translate("Three hypotheses were tested."),
        )

    def test_plural_expansion_keeps_verb_agreement(self):
        # 'study that combines' must become 'studies that combine'.
        translated = self.translate("Two meta-analyses were run.")
        self.assertIn('studies that combine results', translated)
        self.assertNotIn('studies that combines', translated)

    def test_singular_match_singularizes_a_plural_expansion(self):
        # The glossary stores 'adverse events'; the singular must not render
        # as "one bad side effects was serious".
        translated = self.translate("One adverse event was serious.")
        self.assertIn('bad side effect (adverse event)', translated)
        self.assertNotIn('bad side effects (adverse event)', translated)

    def test_british_spelling_is_matched(self):
        self.assertIn('(randomised)', self.translate("Patients were randomised."))

    def test_hyphenation_variants_are_matched(self):
        self.assertIn('(peer-reviewed)', self.translate("The paper is peer-reviewed."))
        self.assertIn('(double blind)', self.translate("A double blind design was used."))

    def test_statistical_shorthand_tolerates_missing_spaces(self):
        for source in ("n=240", "n = 240", "n  =  240"):
            with self.subTest(source=source):
                self.assertIn(
                    'number of people/things studied:',
                    self.translate(f"We enrolled {source} patients."),
                )

    def test_term_split_across_a_line_break_is_matched(self):
        # PDF extraction routinely wraps a phrase mid-term.
        self.assertIn('(clinical\ntrial)', self.translate("A clinical\ntrial ran."))

    def test_derived_forms_are_glossed_not_substituted(self):
        # 'correlated' is a verb; replacing it with a noun phrase would break
        # the sentence, so the word stays and the gloss follows it.
        translated = self.translate("Scores correlated with outcomes.")
        self.assertTrue(translated.startswith('Scores correlated ('))
        self.assertIn('with outcomes.', translated)

    def test_gloss_does_not_nest_parentheses(self):
        translated = self.translate("A correlational study.")
        self.assertNotIn('((', translated)
        self.assertNotIn('))', translated)

    def test_longest_term_wins_over_its_own_plural(self):
        translated = self.translate("Two randomized controlled trials were run.")
        self.assertIn('(randomized controlled trials)', translated)

    def test_pluralize_term_rules(self):
        self.assertEqual(pluralize_term('hypothesis'), 'hypotheses')
        self.assertEqual(pluralize_term('clinical trial'), 'clinical trials')
        self.assertEqual(pluralize_term('cohort study'), 'cohort studies')
        self.assertEqual(pluralize_term('meta-analysis'), 'meta-analyses')
        self.assertEqual(pluralize_term('comorbidity'), 'comorbidities')

    def test_pluralize_expansion_leaves_non_noun_phrases_alone(self):
        # Pluralizing these would produce nonsense.
        for expansion in ('how the study was done',
                          'one thing actually causes another',
                          'thinking about thinking - awareness of your own learning'):
            with self.subTest(expansion=expansion):
                self.assertEqual(pluralize_expansion(expansion), expansion)

    def test_pluralize_expansion_handles_noun_phrases(self):
        self.assertEqual(
            pluralize_expansion('educated guess about what would happen'),
            'educated guesses about what would happen',
        )
        # 'didn't' is already correct for a plural subject - leave it be.
        self.assertEqual(
            pluralize_expansion("comparison group that didn't get the treatment"),
            "comparison groups that didn't get the treatment",
        )
        # A present-tense verb does need agreeing.
        self.assertEqual(
            pluralize_expansion('study that combines results from multiple studies'),
            'studies that combine results from multiple studies',
        )

    def test_singularize_expansion(self):
        self.assertEqual(singularize_expansion('bad side effects'), 'bad side effect')
        self.assertEqual(singularize_expansion('how the study was done'),
                         'how the study was done')


class SenseDisambiguationTests(unittest.TestCase):
    """Ambiguous words must only expand in their academic sense"""

    def setUp(self):
        self.translator = AcademicTranslator()

    def translate(self, text, subject):
        return self.translator.translate_academic_jargon(text, subject)

    def test_everyday_sense_is_left_alone(self):
        cases = [
            ("Workers erected scaffolding around the building site.", 'education', 'scaffolding'),
            ("GPS triangulation gave the satellite position.", 'social_science', 'triangulation'),
            ("DNA replication occurs in the cell nucleus.", 'general_research', 'replication'),
        ]
        for text, subject, term in cases:
            with self.subTest(term=term):
                self.assertEqual(self.translate(text, subject), text)

    def test_academic_sense_still_expands(self):
        cases = [
            ("Teachers used scaffolding to support student learning in the classroom.",
             'education', 'scaffolding'),
            ("We used triangulation across qualitative data sources to confirm findings.",
             'social_science', 'triangulation'),
            ("A direct replication of the original study failed to reproduce the effect.",
             'general_research', 'replication'),
        ]
        for text, subject, term in cases:
            with self.subTest(term=term):
                self.assertIn(f'({term})', self.translate(text, subject))

    def test_verb_usage_is_not_expanded_as_a_noun(self):
        for text in ("We construct a model of the data.",
                     "They will construct a framework.",
                     "The aim was to construct an algorithm."):
            with self.subTest(text=text):
                self.assertEqual(self.translate(text, 'psychology'), text)

    def test_noun_usage_is_expanded(self):
        translated = self.translate(
            "The construct was measured with a validated scale of items.", 'psychology'
        )
        self.assertIn('(construct)', translated)

    def test_strict_terms_need_positive_evidence(self):
        # 'power' is in the statistics glossary and is strict: with no
        # statistical context it must stay untouched.
        translated = self.translator.translate_academic_jargon(
            "The committee held political power over the budget.",
            'social_science',
            include_statistics=True,
        )
        self.assertNotIn('(power)', translated)

    def test_strict_terms_expand_with_evidence(self):
        translated = self.translator.translate_academic_jargon(
            "Statistical power was low because the sample size could not detect the effect.",
            'general_research',
            include_statistics=True,
        )
        self.assertIn('(power)', translated)

    def test_statistics_glossary_is_off_by_default(self):
        self.assertNotIn(
            '(regression)',
            self.translate("We fitted a logistic regression model.", 'psychology'),
        )
        self.assertIn(
            '(regression)',
            self.translator.translate_academic_jargon(
                "We fitted a logistic regression model with several predictors.",
                'psychology',
                include_statistics=True,
            ),
        )

    def test_unambiguous_terms_bypass_the_gate(self):
        # No sense profile means no gating - behavior is unchanged.
        matcher = TermMatcher({'placebo': 'fake treatment'})
        self.assertIn('(placebo)', matcher.translate("Nonsense words placebo elsewhere."))

    def test_cosine_similarity_bounds(self):
        profile = SenseProfile(['sample', 'effect', 'detect'])
        self.assertEqual(profile.cosine(count_tokens("nothing relevant here")), 0.0)
        self.assertAlmostEqual(profile.cosine(count_tokens("sample effect detect")), 1.0)
        self.assertLess(profile.cosine(count_tokens("sample of unrelated words here")), 0.6)

    def test_sense_decision_reports_a_reason(self):
        sense = TermSense(
            academic=SenseProfile(['statistical', 'sample']),
            everyday=SenseProfile(['electricity', 'grid']),
        )
        verdict, reason = sense.decide("the statistical sample showed", " was adequate")
        self.assertTrue(verdict)
        self.assertIn('academic sense', reason)

        verdict, reason = sense.decide("the electricity grid lost", " last night")
        self.assertFalse(verdict)
        self.assertIn('everyday sense', reason)

    def test_gating_does_not_reintroduce_cascading(self):
        # A skipped expansion must not leave a partial substitution behind.
        text = "We construct a model. The construct was measured on a scale."
        translated = self.translate(text, 'psychology')
        self.assertEqual(translated.count('(construct)'), 1)
        self.assertIn('We construct a model.', translated)


class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.translator = AcademicTranslator()

    def test_short_names_map_to_their_files(self):
        # Short names come from the class (ADHDModule -> adhd), not the file,
        # so filenames are free to describe what the module does.
        self.assertEqual(
            self.translator.available_modules,
            {
                'adhd': 'ADHD_accessibility',
                'audio': 'audio_optimization',
                'autism': 'autism_accessibility',
                'beginner': 'beginner_reading',
                'dyslexia': 'dyslexia_accessibility',
                'esl': 'esl_support',
                'visual': 'visual_processing',
            },
        )

    def test_modules_load_by_short_name_and_file_stem(self):
        for short_name, stem in self.translator.available_modules.items():
            with self.subTest(module=short_name):
                by_short = self.translator.load_module(short_name)
                by_stem = self.translator.load_module(stem)
                self.assertIsInstance(by_short, AccessibilityModule)
                self.assertIsInstance(by_stem, AccessibilityModule)
                self.assertIs(type(by_short), type(by_stem))
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


class AutismModuleTests(unittest.TestCase):
    def setUp(self):
        self.module = AcademicTranslator().load_module('autism')
        self.context = {'subject_area': 'psychology', 'reading_level': 'College'}

    def test_idioms_become_literal_with_original_kept(self):
        output = self.module.process_text("This study sheds light on memory.", self.context)
        self.assertIn('helps explain', output)
        self.assertIn('[the paper says: "sheds light on"]', output)

    def test_replacement_keeps_sentence_capitalization(self):
        output = self.module.process_text(
            "A growing body of evidence supports this.", self.context
        )
        self.assertIn('An increasing number of studies', output)
        self.assertNotIn('an increasing number of studies [', output)

    def test_vague_quantities_are_flagged(self):
        output = self.module.process_text("We tested several participants.", self.context)
        self.assertIn('several [VAGUE]', output)

    def test_connectives_are_explained(self):
        output = self.module.process_text(
            "The effect was small. However, it was consistent.", self.context
        )
        self.assertIn('this contradicts what was just said', output)

    def test_hedges_are_listed_but_text_is_unchanged(self):
        output = self.module.process_text("Sleep may improve memory.", self.context)
        self.assertIn('it is possible, but not certain', output)
        # The hedge itself stays in the sentence.
        self.assertIn('Sleep may improve', output)

    def test_document_ends_predictably(self):
        output = self.module.process_text("A plain sentence about results.", self.context)
        self.assertTrue(output.rstrip().endswith('There is nothing after this line.'))


class BeginnerModuleTests(unittest.TestCase):
    def setUp(self):
        self.module = AcademicTranslator().load_module('beginner')
        self.context = {'subject_area': 'medical', 'reading_level': 'Graduate'}

    def test_word_swaps_keep_tense_and_number(self):
        swapped, _ = self.module.use_shorter_words(
            "Researchers utilized methods and required more data."
        )
        self.assertIn('used', swapped)
        self.assertIn('needed', swapped)
        self.assertNotIn('utilized', swapped)
        # The naive version produced 'use' and 'need' here.
        self.assertNotIn(' use ', swapped)

    def test_gerunds_are_handled(self):
        swapped, _ = self.module.use_shorter_words("Prior to implementing the plan")
        self.assertIn('carrying out', swapped)
        self.assertIn('Before', swapped)

    def test_phrases_beat_the_words_inside_them(self):
        swapped, _ = self.module.use_shorter_words("A considerable majority of patients")
        self.assertIn('Most patients', swapped)
        self.assertNotIn('large most', swapped)

    def test_long_sentence_splits_when_second_half_stands_alone(self):
        result = self.module.shorten_sentences(
            "The researchers looked at the problem for a long time and the "
            "participants showed a large improvement on every measure."
        )
        self.assertGreater(result.count('.'), 1)

    def test_long_sentence_is_left_alone_when_splitting_would_break_it(self):
        # The second clause shares the first clause's subject, so cutting at
        # 'and' would leave a fragment with no subject.
        source = ("The researchers looked at the problem for a long time and "
                  "later decided that the effect was real.")
        self.assertEqual(self.module.shorten_sentences(source), source)

    def test_no_sentence_fragments_are_produced(self):
        output = self.module.process_text(
            "Researchers utilized a comprehensive methodology to ascertain whether "
            "the intervention would facilitate improvements, and the participants "
            "subsequently demonstrated significant enhancement.", self.context
        )
        # A fragment shows up as a full stop directly followed by a lowercase word.
        self.assertIsNone(re.search(r'\.\s+[a-z]', output))

    def test_reading_level_drops(self):
        source = ("Researchers utilized a comprehensive methodology to ascertain "
                  "whether the intervention would facilitate substantial improvements.")
        simplified = self.module.process_text(source, self.context)
        self.assertLess(
            self.module.estimate_grade_level(simplified),
            self.module.estimate_grade_level(source),
        )

    def test_glossary_lists_kept_words(self):
        output = self.module.process_text("The treatment reduced symptoms.", self.context)
        self.assertIn('**treatment**', output)
        self.assertIn('**symptom**', output)

    def test_verb_forms_are_correct(self):
        self.assertEqual(verb_forms('utilize'), ('utilizes', 'utilized', 'utilizing'))
        self.assertEqual(verb_forms('carry out'), ('carries out', 'carried out', 'carrying out'))
        self.assertEqual(verb_forms('show'), ('shows', 'showed', 'showing'))
        self.assertEqual(verb_forms('watch'), ('watches', 'watched', 'watching'))


class ESLModuleTests(unittest.TestCase):
    def setUp(self):
        self.module = AcademicTranslator().load_module('esl')
        self.context = {'subject_area': 'medical', 'reading_level': 'College'}

    def test_phrasal_verbs_are_glossed(self):
        output = self.module.process_text("They carried out the study.", self.context)
        self.assertIn('carried out (= did or performed)', output)

    def test_phrasal_verb_glossed_only_once(self):
        output = self.module.process_text(
            "They carried out one study. Then they carried out another.", self.context
        )
        self.assertEqual(output.count('(= did or performed)'), 1)

    def test_imperial_units_are_converted(self):
        output = self.module.process_text("Participants weighed 150 lbs.", self.context)
        self.assertIn('68.0 kg', output)

    def test_fahrenheit_conversion_is_correct(self):
        output = self.module.process_text("Temperature was 98.6 degrees Fahrenheit.", self.context)
        self.assertIn('37.0 °C', output)

    def test_false_friends_are_reported(self):
        output = self.module.process_text(
            "Eventually the authors realize the problem.", self.context
        )
        self.assertIn('FALSE FRIENDS', output)
        self.assertIn('eventually', output.lower())

    def test_us_terms_are_explained(self):
        output = self.module.process_text("Approved by the IRB.", self.context)
        self.assertIn('Institutional Review Board', output)

    def test_lowercase_act_is_not_mistaken_for_the_exam(self):
        output = self.module.process_text(
            "The participants act in their own interest.", self.context
        )
        self.assertNotIn('university entrance exam', output)


class AudioModuleTests(unittest.TestCase):
    def setUp(self):
        self.module = AcademicTranslator().load_module('audio')
        self.context = {'subject_area': 'medical', 'reading_level': 'Graduate'}

    def test_abbreviations_are_spoken(self):
        # Checked on the body directly: the spoken intro quotes "et al" when
        # explaining what it replaced.
        spoken = self.module.expand_abbreviations("Smith et al. found this, e.g. in adults.")
        self.assertIn('and colleagues', spoken)
        self.assertIn('for example', spoken)
        self.assertNotIn('et al', spoken)

    def test_citations_are_removed(self):
        text, removed = self.module.remove_citations(
            "The effect held (Smith, 2019) across trials [12]."
        )
        self.assertEqual(removed, 2)
        self.assertNotIn('Smith', text)
        self.assertNotIn('[12]', text)

    def test_notation_is_case_sensitive(self):
        # 'OR' is an odds ratio; 'or' is a conjunction.
        self.assertIn('odds ratio', self.module.expand_notation("The OR was 2.3"))
        self.assertNotIn('odds ratio', self.module.expand_notation("one or two"))

    def test_comparison_after_a_letter_is_spoken(self):
        output = self.module.process_text("The effect was large, p < .001.", self.context)
        self.assertIn('is less than', output)

    def test_decimals_are_spelled_out(self):
        output = self.module.process_text("The mean was 8.4 units.", self.context)
        self.assertIn('8 point 4', output)

    def test_unit_slashes_say_per_not_or(self):
        spoken = self.module.speak_symbols("levels of 120 mg/dL")
        self.assertIn('milligrams per deciliter', spoken)
        self.assertNotIn('mg or dL', spoken)

    def test_articles_agree_after_substitution(self):
        self.assertIn('an approximately', self.module.fix_articles('a approximately 15'))
        # Words that break the vowel-letter rule.
        self.assertIn('a university', self.module.fix_articles('an university'))
        self.assertIn('an hour', self.module.fix_articles('a hour'))

    def test_listening_time_is_reported(self):
        output = self.module.process_text("word " * 300, self.context)
        self.assertIn('minutes to listen to', output)


class AllModulesContractTests(unittest.TestCase):
    """Every shipped module must honour the AccessibilityModule contract"""

    def setUp(self):
        self.translator = AcademicTranslator()

    def test_seven_modules_ship(self):
        self.assertEqual(
            sorted(self.translator.available_modules),
            ['adhd', 'audio', 'autism', 'beginner', 'dyslexia', 'esl', 'visual'],
        )

    def test_every_module_returns_usable_output(self):
        for short_name in self.translator.available_modules:
            with self.subTest(module=short_name):
                module = self.translator.load_module(short_name)
                context = {'subject_area': 'medical', 'reading_level': 'College'}

                output = module.process_text(SAMPLE_PAPER, context)
                self.assertIsInstance(output, str)
                self.assertTrue(output.strip())

                extras = module.get_additional_elements(SAMPLE_PAPER, context)
                self.assertTrue(extras['visual_elements'])
                self.assertTrue(extras['action_items'])
                self.assertTrue(module.get_name())
                self.assertTrue(module.get_description())

    def test_every_module_survives_empty_and_tiny_input(self):
        for short_name in self.translator.available_modules:
            for text in ("", "   ", "Short."):
                with self.subTest(module=short_name, text=repr(text)):
                    module = self.translator.load_module(short_name)
                    output = module.process_text(text, {'subject_area': 'general'})
                    self.assertIsInstance(output, str)

    def test_modules_chain_without_error(self):
        result = self.translator.translate_academic_document(
            SAMPLE_PAPER,
            modules=sorted(self.translator.available_modules),
        )
        self.assertEqual(len(result.modules_applied), 7)
        self.assertTrue(result.plain_english.strip())

    def test_short_names_are_unique(self):
        names = list(self.translator.available_modules)
        self.assertEqual(len(names), len(set(names)))


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
