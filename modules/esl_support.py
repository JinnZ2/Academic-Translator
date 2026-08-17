#!/usr/bin/env python3
"""
ESL Support Module for Academic Translator

For readers whose first language is not English. Academic English is hard
for native speakers too, but it carries specific traps for second-language
readers, and this module targets those:

- Phrasal verbs ("carry out", "rule out") - the meaning is not the sum of
  the two words, and dictionaries often list them separately
- False friends - words that look like a word in your language but mean
  something else. "Eventually" does not mean "eventualmente".
- Latin and Greek roots - if your language borrowed from Latin, long English
  words are often easier than short ones
- US-specific institutions and terms that papers assume you know
- Imperial units, converted to metric inline

Nothing here assumes which language you speak, and nothing is simplified
away - vocabulary is explained, not removed.
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


class ESLModule(AccessibilityModule):
    def __init__(self):
        # Phrasal verbs: the meaning is not the two words added together.
        self.phrasal_verbs = {
            'carry out': 'do or perform',
            'carried out': 'did or performed',
            'carrying out': 'doing or performing',
            'point out': 'say or show',
            'pointed out': 'said or showed',
            'points out': 'says or shows',
            'bring about': 'cause',
            'brought about': 'caused',
            'come up with': 'invent or think of',
            'came up with': 'invented or thought of',
            'rule out': 'eliminate as a possibility',
            'ruled out': 'eliminated as a possibility',
            'account for': 'explain, or be the cause of',
            'accounted for': 'explained, or was the cause of',
            'accounts for': 'explains, or is the cause of',
            'follow up': 'check again at a later time',
            'followed up': 'checked again at a later time',
            'break down': 'separate into parts',
            'broken down': 'separated into parts',
            'set out': 'begin, or state clearly',
            'put forward': 'propose',
            'draw on': 'use as a source',
            'drawn on': 'used as a source',
            'build on': 'use as a foundation',
            'built on': 'used as a foundation',
            'look into': 'investigate',
            'looked into': 'investigated',
            'take into account': 'consider',
            'taken into account': 'considered',
            'give rise to': 'cause',
            'gave rise to': 'caused',
            'gives rise to': 'causes',
            'result in': 'cause',
            'resulted in': 'caused',
            'lead to': 'cause',
            'led to': 'caused',
            'rely on': 'depend on',
            'relied on': 'depended on',
            'consist of': 'be made of',
            'consists of': 'is made of',
            'refer to': 'mention, or point to',
            'referred to': 'mentioned, or pointed to',
            'turn out': 'be revealed as',
            'turned out': 'was revealed as',
            'figure out': 'understand',
            'figured out': 'understood',
            'make up': 'form or constitute',
            'made up': 'formed or constituted',
            'single out': 'choose one from a group',
            'sort out': 'organize or resolve',
        }

        # Words that resemble a word in another language but mean something
        # different. The language is named so you can tell if it applies to you.
        self.false_friends = {
            'actually': ('in reality', 'Spanish "actualmente" and French "actuellement" mean CURRENTLY, not this'),
            'eventually': ('in the end, after some time', 'Spanish "eventualmente" means POSSIBLY, not this'),
            'assist': ('help', 'Spanish "asistir" usually means TO ATTEND, not this'),
            'attend': ('go to, be present at', 'Spanish "atender" means TO PAY ATTENTION or SERVE, not this'),
            'realize': ('become aware of', 'Spanish "realizar" and French "réaliser" mean TO CARRY OUT, not this'),
            'sensible': ('showing good judgement', 'Spanish and French "sensible" mean SENSITIVE, not this'),
            'library': ('a place that lends books', 'Spanish "librería" means BOOKSHOP, not this'),
            'pretend': ('act as if something is true when it is not', 'Spanish "pretender" means TO INTEND, not this'),
            'comprehensive': ('complete, covering everything', 'Spanish "comprensivo" means UNDERSTANDING (of a person), not this'),
            'large': ('big', 'Spanish "largo" means LONG, not this'),
            'introduce': ('present for the first time', 'Spanish "introducir" often means TO INSERT, not this'),
            'record': ('write down and keep', 'Spanish "recordar" means TO REMEMBER, not this'),
            'support': ('help, hold up', 'French "supporter" means TO TOLERATE, not this'),
            'college': ('in US papers this means UNIVERSITY', 'French "collège" means MIDDLE SCHOOL, not this'),
            'estate': ('property or land', 'Spanish "estado" means STATE, not this'),
            'parents': ('mother and father only', 'Spanish "parientes" means RELATIVES in general, not this'),
            'exit': ('the way out', 'Spanish "éxito" means SUCCESS, not this'),
            'ultimately': ('in the end', 'Spanish "últimamente" means RECENTLY, not this'),
        }

        # US institutions and terms that papers assume the reader knows.
        self.cultural_context = {
            'k-12': 'the US school system from age 5 to age 18',
            'grade point average': 'a US average of school marks, usually out of 4.0',
            'gpa': 'grade point average - a US average of school marks, usually out of 4.0',
            'sat': 'a standardised US university entrance exam',
            'act': 'a standardised US university entrance exam (when written in capitals)',
            'irb': 'Institutional Review Board - the ethics committee that approves US studies',
            'medicaid': 'US government health cover for people on low incomes',
            'medicare': 'US government health cover for people over 65',
            'cdc': 'Centers for Disease Control and Prevention - the US public health agency',
            'nih': 'National Institutes of Health - the main US medical research funder',
            'fda': 'Food and Drug Administration - the US agency that approves medicines',
            'socioeconomic status': 'a measure combining income, education and job type',
            'school district': 'the local body that runs public schools in one US area',
            'freshman': 'a first-year student in a US school or university',
            'sophomore': 'a second-year student in a US school or university',
            'title i': 'a US programme funding schools with many low-income students',
            'ivy league': 'a group of eight old, highly selective US universities',
        }

        # Imperial units and how to convert them.
        self.unit_conversions = [
            (r'(\d+(?:\.\d+)?)\s*(?:lbs?\b|pounds?\b)', 0.4536, 'kg', 1),
            (r'(\d+(?:\.\d+)?)\s*(?:°\s*F\b|degrees Fahrenheit\b|°F)', None, '°C', 1),
            (r'(\d+(?:\.\d+)?)\s*(?:miles?\b)', 1.609, 'km', 1),
            (r'(\d+(?:\.\d+)?)\s*(?:feet\b|foot\b)', 0.3048, 'm', 2),
            (r'(\d+(?:\.\d+)?)\s*(?:inches\b|inch\b)', 2.54, 'cm', 1),
            (r'(\d+(?:\.\d+)?)\s*(?:ounces?\b|oz\b)', 28.35, 'g', 0),
            (r'(\d+(?:\.\d+)?)\s*(?:gallons?\b)', 3.785, 'L', 1),
        ]

        # Latin and Greek building blocks. If your language borrowed from
        # Latin, these make long English words predictable.
        #
        # Two-letter prefixes ('co-', 'bi-') are deliberately absent: they
        # match too many words that do not actually contain them.
        self.word_parts = {
            'socio': 'society (Latin)',
            'inter': 'between (Latin)',
            'intra': 'inside (Latin)',
            'trans': 'across (Latin)',
            'sub': 'under (Latin)',
            'super': 'above (Latin)',
            'pre': 'before (Latin)',
            'post': 'after (Latin)',
            'multi': 'many (Latin)',
            'contra': 'against (Latin)',
            'hyper': 'over, too much (Greek)',
            'hypo': 'under, too little (Greek)',
            'meta': 'beyond, about itself (Greek)',
            'micro': 'small (Greek)',
            'macro': 'large (Greek)',
            'poly': 'many (Greek)',
            'psycho': 'mind (Greek)',
            'neuro': 'nerve, brain (Greek)',
            'cardio': 'heart (Greek)',
            'patho': 'disease (Greek)',
            'epi': 'upon, among (Greek)',
            'chrono': 'time (Greek)',
            'demo': 'people (Greek)',
        }

    def get_name(self) -> str:
        return "ESL Support"

    def get_description(self) -> str:
        return "Explains phrasal verbs, warns about false friends, decodes Latin/Greek roots, converts US units and terms"

    def process_text(self, text: str, context: Dict) -> str:
        """Annotate the text with the explanations a second-language reader needs"""

        annotated, phrasals = self.explain_phrasal_verbs(text)
        annotated = self.convert_units(annotated)
        annotated, cultural = self.explain_cultural_terms(annotated)

        friends = self.find_false_friends(text)
        roots = self.find_word_parts(text)

        header = self.create_header(context)
        footer = self.create_notes(phrasals, friends, cultural, roots)

        return f"{header}\n\n{annotated}\n\n{footer}"

    def create_header(self, context: Dict) -> str:
        """Explain what was marked and why"""
        return """
🌍 **ENGLISH LANGUAGE SUPPORT**

This paper has been marked up for readers whose first language is not English.

**What the marks mean:**
• `carry out (= do or perform)` - a phrasal verb. Two words that together
  mean something you cannot guess from either word alone.
• `150 lbs (68 kg)` - US units converted to metric.
• `GPA (= average of school marks)` - a US term the paper assumes you know.

**At the end you will find:**
• False friends - English words that look like a word in your language but
  mean something different. These cause the most misunderstandings.
• Word parts - Latin and Greek pieces that appear in the long words.
  If your language comes from Latin, the long words are often the easy ones.

Vocabulary was explained, not removed. The English is the paper's own.

-----
""".strip()

    def explain_phrasal_verbs(self, text: str) -> Tuple[str, List[str]]:
        """Gloss phrasal verbs inline"""
        found = []
        result = text

        # Longest first: 'take into account' before 'take'.
        for phrase in sorted(self.phrasal_verbs, key=len, reverse=True):
            meaning = self.phrasal_verbs[phrase]
            pattern = r'\b' + r'\s+'.join(re.escape(p) for p in phrase.split()) + r'\b'

            if re.search(pattern, result, re.IGNORECASE):
                found.append(f"**{phrase}** = {meaning}")
                result = re.sub(
                    pattern,
                    lambda m: f"{m.group(0)} (= {meaning})",
                    result,
                    count=1,  # gloss the first use only, to avoid clutter
                    flags=re.IGNORECASE,
                )

        return result, found

    def convert_units(self, text: str) -> str:
        """Add metric equivalents after imperial measurements"""
        result = text

        for pattern, factor, unit, decimals in self.unit_conversions:
            def replace(match: re.Match, factor=factor, unit=unit, decimals=decimals) -> str:
                value = float(match.group(1))
                converted = (value - 32) * 5 / 9 if factor is None else value * factor
                return f"{match.group(0)} ({converted:.{decimals}f} {unit})"

            result = re.sub(pattern, replace, result, flags=re.IGNORECASE)

        return result

    def explain_cultural_terms(self, text: str) -> Tuple[str, List[str]]:
        """Gloss US-specific institutions and terms"""
        found = []
        result = text

        for term in sorted(self.cultural_context, key=len, reverse=True):
            meaning = self.cultural_context[term]
            # Acronyms must match case-sensitively, or 'act' matches the verb.
            case_sensitive = term.isupper() or len(term) <= 3
            flags = 0 if case_sensitive else re.IGNORECASE
            probe = term.upper() if case_sensitive else term

            search_pattern = r'\b' + re.escape(probe) + r'\b'
            if re.search(search_pattern, result, flags):
                found.append(f"**{probe}** - {meaning}")
                result = re.sub(
                    search_pattern,
                    lambda m: f"{m.group(0)} (= {meaning})",
                    result,
                    count=1,
                    flags=flags,
                )

        return result, found

    def find_false_friends(self, text: str) -> List[str]:
        """List false friends present in the text, without altering it"""
        found = []
        lowered = text.lower()

        for word, (meaning, warning) in sorted(self.false_friends.items()):
            if re.search(r'\b' + re.escape(word) + r'\b', lowered):
                found.append(f"**{word}** means \"{meaning}\". {warning}.")

        return found

    def find_word_parts(self, text: str) -> List[str]:
        """Find Latin/Greek prefixes used by long words in the text"""
        long_words = {
            word.lower().strip('.,;:()[]"\'')
            for word in text.split()
            if len(word.strip('.,;:()[]"\'')) >= 8
        }

        found = []
        for prefix in sorted(self.word_parts, key=len, reverse=True):
            examples = sorted(w for w in long_words if w.startswith(prefix))
            if examples:
                meaning = self.word_parts[prefix]
                sample = ", ".join(examples[:3])
                found.append(f"**{prefix}-** = {meaning} — as in {sample}")

        return found[:10]

    def create_notes(self, phrasals: List[str], friends: List[str],
                     cultural: List[str], roots: List[str]) -> str:
        """Build the reference section at the end"""
        parts = ["-----", "", "🌍 **LANGUAGE NOTES**", ""]

        if friends:
            parts.append("⚠️ **FALSE FRIENDS — read these first**")
            parts.append("")
            parts.append("These English words look like words in other languages "
                         "but mean something different:")
            parts.append("")
            parts.extend(f"• {item}" for item in friends)
            parts.append("")

        if phrasals:
            parts.append("🔗 **PHRASAL VERBS IN THIS PAPER**")
            parts.append("")
            parts.extend(f"• {item}" for item in phrasals)
            parts.append("")

        if cultural:
            parts.append("🇺🇸 **US TERMS THIS PAPER ASSUMES YOU KNOW**")
            parts.append("")
            parts.extend(f"• {item}" for item in cultural)
            parts.append("")

        if roots:
            parts.append("🧩 **WORD PARTS**")
            parts.append("")
            parts.append("If your first language comes from Latin (Spanish, French, "
                         "Portuguese, Italian, Romanian), you may already recognise these:")
            parts.append("")
            parts.extend(f"• {item}" for item in roots)
            parts.append("")

        if len(parts) == 4:
            parts.append("No phrasal verbs, false friends, or US-specific terms "
                         "were found in this text.")
            parts.append("")

        return "\n".join(parts)

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide ESL-specific additional elements"""

        visual_elements = [
            "🌍 Inline glosses so you never have to leave the sentence",
            "⚠️ False-friend warnings collected in one place",
            "📏 Metric conversions beside every US measurement",
            "🔗 Phrasal verbs marked where they first appear",
            "🧩 Latin and Greek word parts, with examples from this paper",
            "🔤 Generous spacing for readers scanning word by word",
        ]

        action_items = [
            "📝 Start a personal list of the phrasal verbs you meet most often",
            "⚠️ Check the false-friend list before trusting a word that looks familiar",
            "🗣️ Read one paragraph aloud to connect spelling with sound",
            "📖 Look up only the words that block meaning - skip the rest",
            "🔁 Re-read the abstract last; it is the densest part of any paper",
            "💬 Explain the main finding in your first language, then in English",
        ]

        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.extend([
                "🩺 Learn the body-part roots (cardio, neuro, patho) - they repeat constantly",
                "💊 Check whether drug names differ in your country",
            ])
        elif subject_area == 'education':
            action_items.extend([
                "🎓 Compare the US school stages to your country's before reading results",
                "📚 Note that 'college' means university in US papers",
            ])

        return {
            'visual_elements': visual_elements,
            'action_items': action_items,
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
Researchers carried out a study to rule out alternative explanations. They
pointed out that socioeconomic status accounts for much of the variation, and
the findings led to a revised model.

Participants weighed an average of 150 lbs and walked 3 miles per day. Body
temperature was recorded at 98.6 degrees Fahrenheit. Eventually, the authors
realize that comprehensive follow up is required. The study was approved by
the IRB and funded by the NIH.
"""

    module = ESLModule()
    context = {'subject_area': 'medical', 'reading_level': 'College'}

    print("🌍 ESL MODULE TEST")
    print("=" * 60)
    print(module.process_text(sample_text, context))
