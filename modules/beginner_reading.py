#!/usr/bin/env python3
"""
Beginner Reading Level Module for Academic Translator

Rewrites academic text for readers who are early in their reading journey,
or reading in a second language, or simply tired:

- Swaps long academic words for short everyday ones, keeping the grammar
  ("utilized" becomes "used", not "use")
- Splits long sentences at natural joins, never mid-clause
- Breaks the text into short paragraphs
- Collects the hard words it kept into a glossary
- Reports the reading level before and after

Written for adults. Short words are not the same thing as childish words:
nothing here adds baby talk, exclamation marks, or praise for reading. The
content stays exactly as difficult as the research really is.
"""

import re
from typing import Dict, List, Tuple

try:
    from academic_translator import AccessibilityModule
    from term_matching import pluralize_word
except ImportError:  # running this file directly
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from academic_translator import AccessibilityModule
    from term_matching import pluralize_word


# Verbs whose forms the regular rules would get wrong.
IRREGULAR_VERBS = {
    'build up': ('builds up', 'built up', 'building up'),
    'find out': ('finds out', 'found out', 'finding out'),
    'make up': ('makes up', 'made up', 'making up'),
    'make sure': ('makes sure', 'made sure', 'making sure'),
    'take part': ('takes part', 'took part', 'taking part'),
    'show': ('shows', 'showed', 'showing'),
    'keep': ('keeps', 'kept', 'keeping'),
    'get': ('gets', 'got', 'getting'),
    'see': ('sees', 'saw', 'seeing'),
    'buy': ('buys', 'bought', 'buying'),
    'send': ('sends', 'sent', 'sending'),
    'shrink': ('shrinks', 'shrank', 'shrinking'),
}


def verb_forms(base: str) -> Tuple[str, str, str]:
    """Return (third person, past, gerund) for a verb or verb phrase.

    Multi-word verbs inflect on their first word: 'carry out' -> 'carried out'.
    """
    if base in IRREGULAR_VERBS:
        return IRREGULAR_VERBS[base]

    head, _, rest = base.partition(' ')
    tail = f" {rest}" if rest else ""

    if head.endswith(('s', 'x', 'z', 'ch', 'sh')):
        third = head + 'es'
    elif head.endswith('y') and len(head) > 1 and head[-2] not in 'aeiou':
        third = head[:-1] + 'ies'
    else:
        third = head + 's'

    if head.endswith('e'):
        past = head + 'd'
    elif head.endswith('y') and len(head) > 1 and head[-2] not in 'aeiou':
        past = head[:-1] + 'ied'
    else:
        past = head + 'ed'

    gerund = head[:-1] + 'ing' if head.endswith('e') and not head.endswith('ee') else head + 'ing'

    return f"{third}{tail}", f"{past}{tail}", f"{gerund}{tail}"


class BeginnerModule(AccessibilityModule):
    def __init__(self):
        self.max_sentence_words = 14
        self.max_paragraph_sentences = 3

        # Multi-word phrases, replaced before single words so that
        # 'a considerable majority of' never becomes 'a large most of'.
        self.simpler_phrases = {
            'due to the fact that': 'because',
            'in spite of the fact that': 'even though',
            'a considerable majority of': 'most',
            'the vast majority of': 'almost all',
            'a majority of': 'most',
            'the majority of': 'most',
            'a number of': 'some',
            'with regard to': 'about',
            'in addition to': 'as well as',
            'in order to': 'to',
            'prior to': 'before',
            'as a consequence': 'so',
            'it is possible that': 'maybe',
        }

        # Long academic verbs -> short everyday ones. All four forms of each
        # are generated, so tense and number survive the swap.
        self.simpler_verbs = {
            'accumulate': 'build up',
            'alleviate': 'ease',
            'anticipate': 'expect',
            'ascertain': 'find out',
            'assist': 'help',
            'attempt': 'try',
            'commence': 'start',
            'comprise': 'make up',
            'conclude': 'decide',
            'constitute': 'form',
            'demonstrate': 'show',
            'determine': 'find out',
            'diminish': 'shrink',
            'eliminate': 'remove',
            'employ': 'use',
            'endeavor': 'try',
            'enhance': 'improve',
            'ensure': 'make sure',
            'examine': 'look at',
            'exhibit': 'show',
            'facilitate': 'help',
            'implement': 'carry out',
            'indicate': 'show',
            'initiate': 'start',
            'maintain': 'keep',
            'modify': 'change',
            'monitor': 'watch',
            'obtain': 'get',
            'observe': 'see',
            'participate': 'take part',
            'perceive': 'see',
            'purchase': 'buy',
            'require': 'need',
            'retain': 'keep',
            'reveal': 'show',
            'terminate': 'end',
            'transmit': 'send',
            'utilize': 'use',
            'validate': 'confirm',
        }

        # Nouns. Singular and plural are both generated.
        self.simpler_nouns = {
            'component': 'part',
            'discrepancy': 'difference',
            'magnitude': 'size',
            'residence': 'home',
            'variation': 'difference',
            # Noun forms of the verbs above, which the verb rules do not reach.
            'enhancement': 'improvement',
            'utilization': 'use',
            'modification': 'change',
            'elimination': 'removal',
            'examination': 'check',
            'requirement': 'need',
            'objective': 'goal',
        }

        # Words with no inflection to worry about.
        self.simpler_fixed = {
            'additional': 'more',
            'adequate': 'enough',
            'approximately': 'about',
            'considerable': 'large',
            'consequently': 'so',
            'evident': 'clear',
            'fundamental': 'basic',
            'furthermore': 'also',
            'initial': 'first',
            'minimal': 'very small',
            'nevertheless': 'even so',
            'numerous': 'many',
            'previous': 'earlier',
            'primary': 'main',
            'regarding': 'about',
            'significant': 'important',
            'significantly': 'clearly',
            'subsequently': 'later',
            'sufficient': 'enough',
            'therefore': 'so',
            'whereas': 'but',
        }

        self.replacements = self.build_replacements()

        # Words worth keeping even though they are long, because they are the
        # actual subject. These go in the glossary instead of being replaced.
        self.keep_but_explain = {
            'average': 'the usual or middle amount',
            'benefit': 'a good result',
            'diagnosis': 'naming the illness someone has',
            'effect': 'a change caused by something',
            'evidence': 'facts that support an idea',
            'participant': 'a person who took part in the study',
            'percent': 'how many out of every hundred',
            'research': 'careful study to find out something new',
            'researcher': 'a person who does research',
            'risk': 'the chance that something bad happens',
            'study': 'a piece of research',
            'symptom': 'a sign that something is wrong with your body',
            'therapy': 'treatment to help a health or mental problem',
            'treatment': 'something done to help a health problem',
        }

        # Where a long sentence may be cut. Coordinating conjunctions are
        # dropped at the cut; subordinating ones are kept, since removing
        # them would lose the relationship between the two halves.
        self.coordinating = {'and', 'but', 'so'}
        self.subordinating = {'because', 'although', 'though', 'while', 'however'}

        # A cut is only safe if what follows can stand as its own sentence.
        # "Researchers used X and subsequently determined Y" must not become
        # "Determined Y." - that clause shares the earlier subject.
        self.subject_starters = {
            'the', 'a', 'an', 'this', 'that', 'these', 'those', 'they', 'we',
            'it', 'he', 'she', 'there', 'their', 'his', 'her', 'its', 'our',
            'some', 'many', 'most', 'both', 'each', 'every', 'no', 'one',
            'two', 'three', 'participants', 'researchers', 'patients',
            'students', 'children', 'adults', 'scientists', 'authors',
            'results', 'findings', 'scores', 'people',
        }

    def build_replacements(self) -> Dict[str, str]:
        """Every surface form we can swap, mapped to the matching short form"""
        table: Dict[str, str] = {}

        table.update(self.simpler_phrases)
        table.update(self.simpler_fixed)

        for long_verb, short_verb in self.simpler_verbs.items():
            table[long_verb] = short_verb
            for long_form, short_form in zip(verb_forms(long_verb), verb_forms(short_verb)):
                table[long_form] = short_form

        for long_noun, short_noun in self.simpler_nouns.items():
            table[long_noun] = short_noun
            table[pluralize_word(long_noun)] = pluralize_word(short_noun)

        return table

    def get_name(self) -> str:
        return "Beginner Reading Level"

    def get_description(self) -> str:
        return "Swaps long words for short ones keeping tense and number, shortens sentences, and builds a glossary"

    def process_text(self, text: str, context: Dict) -> str:
        """Rewrite for an early reading level"""

        before_level = self.estimate_grade_level(text)

        simple_text, swapped = self.use_shorter_words(text)
        short_text = self.shorten_sentences(simple_text)
        formatted = self.make_short_paragraphs(short_text)

        after_level = self.estimate_grade_level(formatted)
        glossary = self.build_glossary(text)

        header = self.create_header(before_level, after_level, swapped)
        footer = self.create_glossary_section(glossary)

        return f"{header}\n\n{formatted}\n\n{footer}"

    def create_header(self, before: float, after: float, swapped: int) -> str:
        """State plainly what was done to the text"""
        return f"""
📗 **EASY READING VERSION**

This paper was rewritten with shorter words and shorter sentences.

• Reading level before: grade {before:.0f}
• Reading level now: grade {after:.0f}
• Long words replaced: {swapped}

The facts and numbers were not changed. Only the words were.
Hard words that had to stay are explained in the word list at the end.

-----
""".strip()

    @staticmethod
    def match_case(original: str, replacement: str) -> str:
        """Keep the original capitalization"""
        if original[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    def use_shorter_words(self, text: str) -> Tuple[str, int]:
        """Replace long words with everyday ones, in one pass.

        One pass matters: replacing term by term would let an earlier
        replacement be re-matched by a later rule.
        """
        if not self.replacements:
            return text, 0

        # Longest first, so phrases beat the single words inside them.
        pattern = '|'.join(
            r'\b' + r'\s+'.join(re.escape(part) for part in surface.split()) + r'\b'
            for surface in sorted(self.replacements, key=len, reverse=True)
        )

        count = 0

        def substitute(match: re.Match) -> str:
            nonlocal count
            matched = match.group(0)
            replacement = self.replacements.get(' '.join(matched.lower().split()))
            if replacement is None:
                return matched
            count += 1
            return self.match_case(matched, replacement)

        return re.sub(pattern, substitute, text, flags=re.IGNORECASE), count

    def shorten_sentences(self, text: str) -> str:
        """Split any sentence longer than the limit, at natural joins only"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        output = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()
            if len(words) <= self.max_sentence_words:
                output.append(sentence)
            else:
                output.extend(self.split_sentence(words))

        return ' '.join(output)

    def split_sentence(self, words: List[str]) -> List[str]:
        """Cut a long sentence at joining words.

        If there is no natural place to cut, the sentence is left long. A
        long sentence is readable; a sentence cut mid-clause is not.
        """
        pieces = []
        current: List[str] = []
        capitalize_next = False

        for index, word in enumerate(words):
            bare = word.lower().strip(',;:()')
            remaining = len(words) - index - 1

            at_join = bare in self.coordinating or bare in self.subordinating
            long_enough = len(current) >= self.max_sentence_words // 2
            enough_left = remaining >= 4

            next_word = words[index + 1].lower().strip(',;:()') if remaining else ''
            stands_alone = next_word in self.subject_starters

            if at_join and long_enough and enough_left and stands_alone:
                pieces.append(self.finish(current))
                if bare in self.subordinating:
                    # "Because X" still needs its "because".
                    current = [word.capitalize()]
                    capitalize_next = False
                else:
                    # The conjunction is dropped, so the next word starts
                    # the new sentence and has to be capitalized.
                    current = []
                    capitalize_next = True
                continue

            if capitalize_next:
                word = word[:1].upper() + word[1:]
                capitalize_next = False

            current.append(word)

        if current:
            pieces.append(self.finish(current))

        return [piece for piece in pieces if piece.strip(' .')]

    @staticmethod
    def finish(words: List[str]) -> str:
        """Join words into a sentence ending in exactly one full stop"""
        sentence = ' '.join(words).strip().rstrip(',;:')
        if not sentence.endswith(('.', '!', '?')):
            sentence += '.'
        return sentence

    def make_short_paragraphs(self, text: str) -> str:
        """Group sentences into short paragraphs"""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        paragraphs = [
            ' '.join(sentences[index:index + self.max_paragraph_sentences])
            for index in range(0, len(sentences), self.max_paragraph_sentences)
        ]

        return '\n\n'.join(paragraphs)

    def build_glossary(self, text: str) -> List[Tuple[str, str]]:
        """List the hard words that stayed, with plain meanings"""
        lowered = text.lower()

        return [
            (word, meaning)
            for word, meaning in sorted(self.keep_but_explain.items())
            if re.search(r'\b' + re.escape(word), lowered)
        ]

    def create_glossary_section(self, glossary: List[Tuple[str, str]]) -> str:
        """Format the word list"""
        if not glossary:
            return "-----\n\n📕 **WORD LIST**\n\nNo hard words were left in this text."

        lines = ["-----", "", "📕 **WORD LIST**", "",
                 "These words stayed in the text. Here is what they mean:", ""]
        lines.extend(f"• **{word}** - {meaning}" for word, meaning in glossary)

        return "\n".join(lines)

    def estimate_grade_level(self, text: str) -> float:
        """Rough US grade level, from sentence and word length.

        This is the Automated Readability Index, which needs only characters,
        words and sentences - no syllable counting, no word lists.
        """
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        characters = sum(len(word.strip('.,;:()[]"\'')) for word in words)

        if not sentences or not words:
            return 0.0

        score = (4.71 * (characters / len(words))
                 + 0.5 * (len(words) / len(sentences))
                 - 21.43)

        return max(1.0, min(20.0, score))

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide beginner-specific additional elements"""

        visual_elements = [
            "🔠 Large text size with generous line spacing",
            "📗 Short paragraphs - three sentences at most",
            "📕 Word list at the end for the hard words that stayed",
            "📊 Reading level shown before and after",
            "🖍️ One idea per sentence, so nothing has to be held in mind",
            "📖 Plain layout with no columns to track across",
        ]

        action_items = [
            "📝 Say the main finding out loud in your own words",
            "🎯 Pick out the one number that matters most",
            "📕 Check the word list for any word you were unsure about",
            "⏸️ Read one paragraph, then look away and recall it",
            "🗣️ Tell someone else what the study found",
        ]

        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.extend([
                "🩺 Write down what you want to ask your doctor",
                "💊 Check whether this is about a treatment you use",
            ])
        elif subject_area == 'education':
            action_items.extend([
                "🎓 Think about whether this matches what you have seen in school",
                "👩‍🏫 Ask a teacher what part applies to your situation",
            ])

        return {
            'visual_elements': visual_elements,
            'action_items': action_items,
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
Researchers utilized a comprehensive methodology to ascertain whether the
intervention would facilitate improvements in participant outcomes, and
subsequently determined that a considerable majority of participants
demonstrated significant enhancement across numerous measures.

Nevertheless, the investigators indicate that additional research is required
prior to implementing these findings in clinical practice.
"""

    module = BeginnerModule()
    context = {'subject_area': 'medical', 'reading_level': 'Graduate'}

    print("📗 BEGINNER MODULE TEST")
    print("=" * 60)
    print(module.process_text(sample_text, context))
    print("\n" + "=" * 60)

    additional = module.get_additional_elements(sample_text, context)
    print("📋 ADDITIONAL ELEMENTS:")
    for element in additional['visual_elements'][:3]:
        print(f"  • {element}")
