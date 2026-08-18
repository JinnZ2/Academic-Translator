#!/usr/bin/env python3
"""
Autism Accessibility Module for Academic Translator

Transforms academic text to remove the things that make it needlessly hard
to read literally:

- Replaces idioms and metaphors with their literal meaning
- Makes implicit logical connections explicit
- Flags vague quantities the paper never actually specifies
- Explains academic hedging ("may", "suggests") in plain terms
- Uses the same predictable structure every time, stated up front

Written with identity-first language ("autistic readers"), which is the
majority preference in the autistic community. No puzzle-piece imagery.

The goal is not to simplify the content. It is to say plainly what the text
already means, so nothing has to be inferred from tone or figure of speech.
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


class AutismModule(AccessibilityModule):
    def __init__(self):
        # Figures of speech that academic writing uses constantly, and what
        # each one literally means.
        self.figurative_language = {
            'shed light on': 'help explain',
            'sheds light on': 'helps explain',
            'shedding light on': 'helping to explain',
            'in the wake of': 'after',
            'a growing body of evidence': 'an increasing number of studies',
            'growing body of literature': 'increasing number of published studies',
            'the lion\'s share': 'most',
            'cutting edge': 'most advanced',
            'landmark study': 'very important study',
            'paves the way': 'makes it possible',
            'paving the way': 'making it possible',
            'gold standard': 'best available method',
            'in light of': 'because of',
            'bridge the gap': 'fill in the missing part',
            'double-edged sword': 'something with both good and bad effects',
            'at the end of the day': 'finally',
            'hand in hand': 'together',
            'tip of the iceberg': 'only the small visible part of a bigger thing',
            'level playing field': 'fair conditions for everyone',
            'food for thought': 'something to think about',
            'take with a grain of salt': 'be careful about fully believing',
            'taken with a grain of salt': 'treated with care before believing',
            'in a nutshell': 'stated briefly',
            'by and large': 'generally',
            'rule of thumb': 'general guideline',
            'down the road': 'in the future',
            'ballpark figure': 'rough estimate',
            'cast doubt on': 'give reason to doubt',
            'casts doubt on': 'gives reason to doubt',
            'carries weight': 'is important',
            'came to light': 'became known',
            'in the long run': 'over a long period of time',
            'across the board': 'in every case',
            'a stepping stone': 'one step toward something bigger',
            'draw on': 'use',
            'in the field': 'in this area of research',
            'state of the art': 'the most advanced current method',
        }

        # Connectives whose logical relationship is left implicit.
        self.connectives = {
            'however': 'this contradicts what was just said',
            'nevertheless': 'this is true despite what was just said',
            'nonetheless': 'this is true despite what was just said',
            'conversely': 'this is the opposite of what was just said',
            'therefore': 'this is the result of what was just said',
            'thus': 'this is the result of what was just said',
            'hence': 'this is the result of what was just said',
            'consequently': 'this is the result of what was just said',
            'moreover': 'this adds more information to what was just said',
            'furthermore': 'this adds more information to what was just said',
            'additionally': 'this adds more information to what was just said',
            'in contrast': 'this is different from what was just said',
            'similarly': 'this is like what was just said',
            'notably': 'the author thinks this part is important',
        }

        # Words that describe an amount without giving one.
        self.vague_quantities = [
            'some', 'several', 'a number of', 'many', 'few', 'various',
            'numerous', 'a range of', 'relatively', 'fairly', 'quite',
            'rather', 'considerably', 'substantially', 'markedly',
            'the vast majority', 'a great deal', 'much of', 'often',
            'frequently', 'occasionally', 'sometimes', 'generally',
        ]

        # Hedging words. Academic writing rarely states certainty directly.
        self.hedges = {
            'may': 'it is possible, but not certain',
            'might': 'it is possible, but not certain',
            'could': 'it is possible, but not certain',
            'suggests': 'this is what the evidence points to, but it is not proven',
            'suggest': 'this is what the evidence points to, but it is not proven',
            'indicates': 'this is what the evidence points to',
            'appears to': 'it looks this way, but is not confirmed',
            'seems to': 'it looks this way, but is not confirmed',
            'tends to': 'this usually happens, but not always',
            'likely': 'probably, but not certainly',
            'unlikely': 'probably not, but not impossible',
        }

    def get_name(self) -> str:
        return "Autism-Friendly Format"

    def get_description(self) -> str:
        return "Replaces idioms with literal meanings, makes logical connections explicit, flags vague quantities and hedging"

    def process_text(self, text: str, context: Dict) -> str:
        """Rewrite text so nothing has to be inferred"""

        literal_text, idioms_found = self.make_literal(text)
        connected_text = self.make_connections_explicit(literal_text)
        flagged_text, vague_found = self.flag_vague_quantities(connected_text)
        hedges_found = self.find_hedges(text)

        sections = self.number_sections(flagged_text)

        header = self.create_structure_statement(len(sections), context)
        body = "\n\n".join(sections)
        footer = self.create_summary(idioms_found, vague_found, hedges_found)

        return f"{header}\n\n{body}\n\n{footer}"

    def create_structure_statement(self, section_count: int, context: Dict) -> str:
        """State exactly what this document contains, in order, before it starts"""
        subject_area = context.get('subject_area', 'research')

        return f"""
📋 **WHAT THIS DOCUMENT CONTAINS**

This is a {subject_area} research paper, rewritten to be read literally.

The document has exactly these parts, in this order:
1. This explanation (you are reading it now)
2. The paper itself, split into {section_count} numbered sections
3. A list of unclear words the paper used, at the very end

**What was changed in the text:**
• Figures of speech were replaced with their literal meaning.
  The original wording is kept in square brackets afterwards.
• Connecting words like "however" are followed by an explanation of what
  they connect.
• Words that describe an amount without giving a number are marked [VAGUE].
• Nothing was added to or removed from the paper's actual findings.

**What was not changed:**
• The order of the paper's own argument.
• Any number, statistic, or result.

-----
""".strip()

    @staticmethod
    def match_case(original: str, replacement: str) -> str:
        """Keep the original's capitalization, so sentences still start capitalized"""
        if original[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    def make_literal(self, text: str) -> Tuple[str, List[str]]:
        """Replace figures of speech with their literal meaning"""
        result = text
        found = []

        # Longest phrases first, so 'sheds light on' is not half-matched.
        for phrase in sorted(self.figurative_language, key=len, reverse=True):
            meaning = self.figurative_language[phrase]
            pattern = r'\b' + re.escape(phrase) + r'\b'

            if re.search(pattern, result, re.IGNORECASE):
                found.append(f'"{phrase}" means "{meaning}"')
                result = re.sub(
                    pattern,
                    lambda m: f'{self.match_case(m.group(0), meaning)} '
                              f'[the paper says: "{m.group(0)}"]',
                    result,
                    flags=re.IGNORECASE,
                )

        return result, found

    def make_connections_explicit(self, text: str) -> str:
        """Spell out what each connecting word is connecting"""
        result = text

        for connective, explanation in self.connectives.items():
            # Only at the start of a sentence or clause, where the word is
            # doing connective work rather than appearing mid-phrase.
            pattern = r'(^|(?<=[.!?]\s)|(?<=\n))(' + re.escape(connective) + r')\b'
            result = re.sub(
                pattern,
                lambda m: f"{m.group(2)} [meaning: {explanation}]",
                result,
                flags=re.IGNORECASE | re.MULTILINE,
            )

        return result

    def flag_vague_quantities(self, text: str) -> Tuple[str, List[str]]:
        """Mark words that describe an amount without giving one"""
        result = text
        found = []

        for phrase in sorted(self.vague_quantities, key=len, reverse=True):
            pattern = r'\b' + re.escape(phrase) + r'\b'

            if re.search(pattern, result, re.IGNORECASE):
                found.append(phrase)
                result = re.sub(
                    pattern,
                    lambda m: f"{m.group(0)} [VAGUE]",
                    result,
                    flags=re.IGNORECASE,
                )

        return result, found

    def find_hedges(self, text: str) -> List[str]:
        """List the hedging words the paper used, without altering the text"""
        found = []

        for hedge, explanation in self.hedges.items():
            if re.search(r'\b' + re.escape(hedge) + r'\b', text, re.IGNORECASE):
                found.append(f'"{hedge}" means: {explanation}')

        return found

    def number_sections(self, text: str) -> List[str]:
        """Split into numbered sections with a fixed, predictable heading"""
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

        if not paragraphs:
            return []

        return [
            f"**SECTION {index} OF {len(paragraphs)}**\n\n{paragraph}"
            for index, paragraph in enumerate(paragraphs, start=1)
        ]

    def create_summary(self, idioms: List[str], vague: List[str],
                       hedges: List[str]) -> str:
        """Close with a fixed-format list of what was unclear in the original"""
        parts = ["-----", "", "📖 **UNCLEAR WORDS THE PAPER USED**", ""]

        if idioms:
            parts.append("**Figures of speech** (these do not mean what they literally say):")
            parts.extend(f"• {item}" for item in idioms)
            parts.append("")

        if vague:
            unique = sorted(set(vague))
            parts.append("**Amounts the paper never gave a number for:**")
            parts.append("• " + ", ".join(unique))
            parts.append("")
            parts.append("If you need the actual number, it is not in the text. "
                         "That is a limitation of the paper, not a mistake you made.")
            parts.append("")

        if hedges:
            parts.append("**Uncertainty words** (the paper is not claiming certainty):")
            parts.extend(f"• {item}" for item in hedges)
            parts.append("")

        if not (idioms or vague or hedges):
            parts.append("This paper used no figures of speech, vague amounts, "
                         "or uncertainty words that needed explaining.")
            parts.append("")

        parts.append("-----")
        parts.append("")
        parts.append("**END OF DOCUMENT.** There is nothing after this line.")

        return "\n".join(parts)

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide autism-specific additional elements"""

        visual_elements = [
            "📋 Fixed section order, stated before the document begins",
            "🔢 Numbered sections so position in the document is always clear",
            "📐 Consistent formatting - no surprise layout changes",
            "🚫 No flashing, animation, or auto-playing content",
            "📖 Plain background with no decorative images behind text",
            "🔍 Literal-meaning notes kept inline, not hidden in tooltips",
            "⬜ Generous whitespace between sections",
        ]

        action_items = [
            "📝 Write down any sentence that still has more than one possible meaning",
            "🔍 Check the unclear-words list at the end before re-reading",
            "❓ Note which claims the paper hedged - those are not settled facts",
            "📊 Look for the actual numbers behind any [VAGUE] marker",
            "⏸️ Read one numbered section at a time; the order will not change",
        ]

        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.extend([
                "🩺 Write your questions down before an appointment, in order",
                "📋 Ask for written instructions rather than spoken ones",
                "❓ Ask directly: 'Is this certain, or is it likely?'",
            ])
        elif subject_area == 'education':
            action_items.extend([
                "🎓 Check whether the study included autistic participants",
                "📚 Note whether conclusions are stated as facts or as possibilities",
            ])

        return {
            'visual_elements': visual_elements,
            'action_items': action_items,
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
This landmark study sheds light on the relationship between sleep and memory.
A growing body of evidence suggests that sleep may play a role in consolidating
new information.

We recruited several participants and tested them across a range of conditions.
However, the effect was relatively small. Therefore, these findings should be
taken with a grain of salt until larger studies are completed.
"""

    module = AutismModule()
    context = {'subject_area': 'psychology', 'reading_level': 'College'}

    print("📋 AUTISM MODULE TEST")
    print("=" * 60)
    print(module.process_text(sample_text, context))
    print("\n" + "=" * 60)

    additional = module.get_additional_elements(sample_text, context)
    print("📋 ADDITIONAL ELEMENTS:")
    for element in additional['visual_elements'][:3]:
        print(f"  • {element}")
