#!/usr/bin/env python3
"""
Audio Optimization Module for Academic Translator

Rewrites text so a screen reader or text-to-speech engine reads it correctly.
Academic writing is full of things that sound wrong when spoken:

- "et al." read as "et all", "e.g." read as "eee gee"
- "p < .001" read as "p less than point zero zero one" or worse, silently
- "(Smith, 2019; Jones, 2021)" read aloud in the middle of a sentence
- "HbA1c", "95% CI", "n=240", "SD", "±"
- Symbols: %, &, /, ~, ≥, °

It also adds a spoken-word structure: an introduction saying what is coming,
signposts between sections, and a closing summary - because a listener cannot
skim back to check where they are.

Output is plain spoken English, meant to be piped into a TTS engine or read
aloud. It is not meant to be read on screen.
"""

import re
from typing import Dict, List, Tuple

try:
    from academic_translator import AccessibilityModule
except ImportError:  # running this file directly
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from academic_translator import AccessibilityModule


class AudioModule(AccessibilityModule):
    def __init__(self):
        self.words_per_minute = 150

        # Abbreviations that TTS engines mangle. Order matters: the longest
        # are replaced first so 'et al.' is not half-matched.
        self.spoken_abbreviations = {
            'et al.': 'and colleagues',
            'et al': 'and colleagues',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'cf.': 'compare with',
            'vs.': 'versus',
            'vs': 'versus',
            'etc.': 'and so on',
            'ibid.': 'the same source',
            'approx.': 'approximately',
            'no.': 'number',
            'fig.': 'figure',
            'ca.': 'about',
            'p.': 'page',
            'pp.': 'pages',
        }

        # Statistical notation, spelled out as a person would say it.
        self.spoken_notation = {
            'SD': 'standard deviation',
            'SE': 'standard error',
            'CI': 'confidence interval',
            'OR': 'odds ratio',
            'RR': 'relative risk',
            'IQR': 'interquartile range',
            'ANOVA': 'analysis of variance',
            'RCT': 'randomized controlled trial',
            'df': 'degrees of freedom',
        }

        # Clinical shorthand that TTS spells out letter by letter.
        self.spoken_clinical = {
            'HbA1c': 'hemoglobin A one C',
            'BMI': 'body mass index',
            'BP': 'blood pressure',
            'IQ': 'I Q',
        }

        # Symbols. TTS either skips these or reads them unhelpfully.
        # Order matters: unit slashes are handled before the generic slash,
        # so 'mg/dL' becomes 'milligrams per deciliter', not 'mg or dL'.
        self.spoken_symbols = [
            (r'\bmg\s*/\s*dL\b', 'milligrams per deciliter'),
            (r'\bmg\s*/\s*kg\b', 'milligrams per kilogram'),
            (r'\bmmol\s*/\s*L\b', 'millimoles per litre'),
            (r'\bg\s*/\s*L\b', 'grams per litre'),
            (r'\bmL\s*/\s*min\b', 'millilitres per minute'),
            (r'\bkm\s*/\s*h\b', 'kilometres per hour'),
            (r'\bm\s*/\s*s\b', 'metres per second'),
            (r'≥', ' greater than or equal to '),
            (r'≤', ' less than or equal to '),
            (r'≠', ' not equal to '),
            (r'±', ' plus or minus '),
            (r'~(?=\d)', ' approximately '),
            (r'&', ' and '),
            (r'(?<=\w)/(?=\w)', ' or '),
            (r'(?<=\d)\s*%', ' percent'),
            (r'(?<=\d)\s*°\s*C', ' degrees Celsius'),
            (r'(?<=\d)\s*°\s*F', ' degrees Fahrenheit'),
            # A letter may precede the comparison: 'p < .001'.
            (r'(?<=\w)\s*<\s*(?=[\d.])', ' is less than '),
            (r'(?<=\w)\s*>\s*(?=[\d.])', ' is greater than '),
            (r'(?<=[a-zA-Z])\s*=\s*(?=[\d.])', ' equals '),
        ]

        # "a" becomes "an" before a vowel SOUND, which is not the same as a
        # vowel letter. These are the words that break the simple rule.
        self.consonant_sound_vowels = (
            'university', 'universal', 'unique', 'unit', 'union', 'user',
            'useful', 'uniform', 'usual', 'one', 'once',
        )
        self.vowel_sound_consonants = ('hour', 'honest', 'honour', 'honor', 'heir')

    def get_name(self) -> str:
        return "Audio / Text-to-Speech"

    def get_description(self) -> str:
        return "Expands abbreviations and notation, removes citations, and adds spoken signposts for listening"

    def process_text(self, text: str, context: Dict) -> str:
        """Rewrite for listening rather than reading"""

        spoken, removed_citations = self.remove_citations(text)
        spoken = self.expand_abbreviations(spoken)
        spoken = self.expand_notation(spoken)
        spoken = self.speak_symbols(spoken)
        spoken = self.speak_numbers(spoken)
        spoken = self.fix_articles(spoken)
        spoken = self.tidy_whitespace(spoken)

        sections = self.add_signposts(spoken)

        intro = self.create_intro(spoken, context, removed_citations)
        outro = self.create_outro(context)

        return f"{intro}\n\n{sections}\n\n{outro}"

    def estimate_listening_minutes(self, text: str) -> int:
        """How long this will take to listen to, in whole minutes"""
        return max(1, round(len(text.split()) / self.words_per_minute))

    def create_intro(self, text: str, context: Dict, citations: int) -> str:
        """Say what is coming, because a listener cannot skim ahead"""
        subject_area = context.get('subject_area', 'research').replace('_', ' ')
        minutes = self.estimate_listening_minutes(text)

        citation_note = (
            f"{citations} citation references were removed so they do not "
            "interrupt the sentences. "
        ) if citations else ""

        return f"""
🎧 LISTENING VERSION

Welcome. This is a plain English reading of a {subject_area} research paper.

It will take about {minutes} minutes to listen to.

Before we start, three things. First, abbreviations have been spelled out,
so you will hear "and colleagues" rather than "et al". Second, statistics
are read as full sentences rather than symbols. Third, {citation_note}nothing
about the findings themselves has been changed.

Let us begin.

-----
""".strip()

    def remove_citations(self, text: str) -> Tuple[str, int]:
        """Strip inline citations, which break a sentence when spoken"""
        patterns = [
            # (Smith, 2019), (Smith & Jones, 2019; Lee, 2021)
            r'\s*\([^()]*\b(?:19|20)\d{2}[a-z]?\s*(?:;[^()]*)?\)',
            # Numeric styles: [12], [3-5], [1,2,7]
            r'\s*\[\d+(?:\s*[-,]\s*\d+)*\]',
        ]

        result = text
        removed = 0

        for pattern in patterns:
            result, count = re.subn(pattern, '', result)
            removed += count

        return result, removed

    def expand_abbreviations(self, text: str) -> str:
        """Replace abbreviations with the words a person would say"""
        result = text

        for abbreviation in sorted(self.spoken_abbreviations, key=len, reverse=True):
            spoken = self.spoken_abbreviations[abbreviation]
            # Escaped so the dots are literal, not any-character.
            pattern = re.escape(abbreviation)
            if abbreviation[0].isalpha():
                pattern = r'\b' + pattern
            result = re.sub(pattern, spoken, result, flags=re.IGNORECASE)

        return result

    def expand_notation(self, text: str) -> str:
        """Spell out statistical abbreviations, case-sensitively.

        Case matters: 'OR' is an odds ratio, 'or' is a conjunction.
        """
        result = text

        for abbreviation in sorted(self.spoken_notation, key=len, reverse=True):
            spoken = self.spoken_notation[abbreviation]
            result = re.sub(r'\b' + re.escape(abbreviation) + r'\b', spoken, result)

        return result

    def speak_symbols(self, text: str) -> str:
        """Replace symbols with their spoken form"""
        result = text

        for pattern, spoken in self.spoken_symbols:
            result = re.sub(pattern, spoken, result)

        for abbreviation, spoken in self.spoken_clinical.items():
            result = re.sub(r'\b' + re.escape(abbreviation) + r'\b', spoken, result)

        return result

    def fix_articles(self, text: str) -> str:
        """Correct a/an after substitution changed the following word.

        Expanding '~' into 'approximately' leaves 'a approximately', which is
        audible in a way it would not be on the page.
        """
        def correct(match: re.Match) -> str:
            article, following = match.group(1), match.group(2)
            lowered = following.lower()

            if lowered.startswith(self.consonant_sound_vowels):
                wanted = 'a'
            elif lowered.startswith(self.vowel_sound_consonants):
                wanted = 'an'
            elif lowered[:1] in 'aeiou':
                wanted = 'an'
            else:
                wanted = 'a'

            if article[:1].isupper():
                wanted = wanted.capitalize()

            return f"{wanted} {following}"

        return re.sub(r'\b([Aa]n?)\s+([A-Za-z]+)', correct, text)

    def speak_numbers(self, text: str) -> str:
        """Make numbers readable aloud.

        A leading decimal point is the main offender: TTS reads '.001' as
        'dot zero zero one' or skips the point entirely.
        """
        # .001 -> 0.001
        result = re.sub(r'(?<![\d.])\.(\d+)', r'0.\1', text)

        # 0.001 -> "0 point 0 0 1", which is unambiguous when spoken.
        def spell_decimal(match: re.Match) -> str:
            whole, fraction = match.group(1), match.group(2)
            digits = ' '.join(fraction)
            return f"{whole} point {digits}"

        return re.sub(r'\b(\d+)\.(\d+)\b', spell_decimal, result)

    @staticmethod
    def tidy_whitespace(text: str) -> str:
        """Collapse the gaps left behind by removals"""
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r' ([,.;:!?])', r'\1', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def add_signposts(self, text: str) -> str:
        """Announce each section, so a listener knows where they are"""
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

        if not paragraphs:
            return text

        ordinals = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth',
                    'Seventh', 'Eighth', 'Ninth', 'Tenth']

        spoken_sections = []
        for index, paragraph in enumerate(paragraphs):
            if index < len(ordinals):
                label = ordinals[index]
            else:
                label = f"Part {index + 1}"

            if index == len(paragraphs) - 1 and len(paragraphs) > 1:
                signpost = "And finally."
            else:
                signpost = f"{label}."

            spoken_sections.append(f"{signpost}\n\n{paragraph}")

        return "\n\n[pause]\n\n".join(spoken_sections)

    def create_outro(self, context: Dict) -> str:
        """Close with what a listener should do next"""
        subject_area = context.get('subject_area', 'general')

        next_step = {
            'medical': "If any of this applies to your own health, write your "
                       "questions down and take them to your doctor.",
            'psychology': "If this relates to your own experience, it may be "
                          "worth discussing with a therapist or counsellor.",
            'education': "If this relates to a learner you support, consider "
                         "which part of it applies to their situation.",
        }.get(subject_area,
              "If this research matters to you, look for more recent studies "
              "on the same question.")

        return f"""
-----

🎧 END OF READING

That is the end of the paper.

Remember that this is a plain English summary, not professional advice.
{next_step}

To hear any part again, use your player's rewind control. Sections were
announced in order, so you can count forward to the one you want.
""".strip()

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide audio-specific additional elements"""

        minutes = self.estimate_listening_minutes(text)

        visual_elements = [
            f"🎧 Estimated listening time: about {minutes} minutes at 150 words per minute",
            "🔊 Abbreviations expanded so TTS pronounces them correctly",
            "⏸️ [pause] markers between sections for engines that honour them",
            "📢 Spoken signposts, since a listener cannot see headings",
            "🚫 Inline citations removed - they break sentences when read aloud",
            "🔢 Decimals spelled out digit by digit to avoid mis-reading",
        ]

        action_items = [
            "🎧 Listen at a speed that suits you - slower is not worse",
            "⏸️ Pause after each section and say the main point out loud",
            "🔁 Replay any section with numbers in it; numbers are hardest to hear",
            "📝 Record a voice note of what you understood",
            "🚶 Listen while walking if that helps you concentrate",
        ]

        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.append("🩺 Replay the findings section before a medical appointment")
        elif subject_area == 'education':
            action_items.append("🎓 Share the audio with others who support the same learner")

        return {
            'visual_elements': visual_elements,
            'action_items': action_items,
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
Smith et al. (2019) reported that the intervention group improved (M = 8.4,
SD = 3.2) compared with controls [12]. The effect was significant, p < .001,
95% CI: -0.9 to -0.5.

Follow-up at 6 months showed a ~15% reduction in HbA1c (Jones & Lee, 2021).
Participants were weighed and measured; temperature was 37°C. The OR was 2.3
(e.g. twice the odds), and the RCT design means causation can be inferred.
"""

    module = AudioModule()
    context = {'subject_area': 'medical', 'reading_level': 'Graduate'}

    print("🎧 AUDIO MODULE TEST")
    print("=" * 60)
    print(module.process_text(sample_text, context))
