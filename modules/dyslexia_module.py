#!/usr/bin/env python3
"""
Dyslexia-Friendly Accessibility Module for Academic Translator

Transforms academic text to support dyslexic readers:

- Simplifies sentence structure (max 15 words)
- Provides phonetic pronunciation guides
- Uses dyslexia-friendly formatting
- Breaks up dense text blocks
- Highlights key words and concepts
- Adds visual word spacing and line breaks

Created with input from the dyslexia community.
"""

import re
from typing import Dict, List

try:
    from academic_translator import AccessibilityModule
except ImportError:  # running this file directly, e.g. python modules/adhd_module.py
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from academic_translator import AccessibilityModule


class DyslexiaModule(AccessibilityModule):
    def __init__(self):
        self.max_sentence_length = 15  # words
        self.max_paragraph_length = 3  # sentences

        # Common academic words that need pronunciation help
        self.pronunciation_guide = {
            'methodology': 'meth-od-OL-o-gy',
            'statistical': 'sta-TIS-ti-cal',
            'significant': 'sig-NIF-i-cant',
            'hypothesis': 'hy-POTH-e-sis',
            'participants': 'par-TIC-i-pants',
            'intervention': 'in-ter-VEN-tion',
            'correlation': 'cor-re-LA-tion',
            'analyze': 'AN-a-lyze',
            'procedure': 'pro-CE-dure',
            'variable': 'VAIR-ee-a-bul',
            'cognitive': 'COG-ni-tive',
            'psychological': 'sy-ko-LOJ-i-cal',
            'neurological': 'nur-o-LOJ-i-cal',
            'pharmaceutical': 'far-ma-SU-ti-cal',
            'physiological': 'fiz-ee-o-LOJ-i-cal'
        }

        # Words that commonly cause reading difficulties
        self.difficult_words = {
            'demonstrate': 'show',
            'utilize': 'use',
            'facilitate': 'help',
            'subsequently': 'then',
            'approximately': 'about',
            'nevertheless': 'however',
            'furthermore': 'also',
            'consequently': 'so',
            'therefore': 'so',
            'specifically': 'exactly'
        }

    def get_name(self) -> str:
        return "Dyslexia-Friendly Format"

    def get_description(self) -> str:
        return "Simplifies sentences, adds phonetic guides, optimizes spacing and formatting for dyslexic readers"

    def process_text(self, text: str, context: Dict) -> str:
        """Transform text to be dyslexia-friendly"""

        # Add dyslexia-friendly header
        header = self.create_dyslexia_header()

        # Simplify difficult words
        simplified_text = self.simplify_vocabulary(text)

        # Break into shorter sentences
        short_sentences = self.create_short_sentences(simplified_text)

        # Add pronunciation guides
        pronounced_text = self.add_pronunciation_guides(short_sentences)

        # Format for dyslexia-friendly reading
        formatted_text = self.apply_dyslexia_formatting(pronounced_text)

        # Add reading tips
        footer = self.create_reading_tips()

        return f"{header}\n\n{formatted_text}\n\n{footer}"

    def create_dyslexia_header(self) -> str:
        """Create header with dyslexia-friendly formatting info"""
        return """
📖 **DYSLEXIA-FRIENDLY FORMAT**

This text has been formatted to be easier to read:
• Short sentences (15 words or less)
• Simple vocabulary
• Pronunciation guides for hard words
• Extra spacing between lines
• Clear paragraph breaks

💡 **Reading tip:** Take your time and read at your own pace!

-----
""".strip()

    def simplify_vocabulary(self, text: str) -> str:
        """Replace difficult words with simpler alternatives"""
        simplified = text

        for difficult, simple in self.difficult_words.items():
            pattern = r'\b' + re.escape(difficult) + r'\b'
            simplified = re.sub(pattern, simple, simplified, flags=re.IGNORECASE)

        return simplified

    def create_short_sentences(self, text: str) -> str:
        """Break long sentences into shorter ones"""
        sentences = re.split(r'[.!?]+', text)
        processed_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()

            if len(words) <= self.max_sentence_length:
                processed_sentences.append(sentence + '.')
            else:
                # Break long sentence at logical points
                broken_sentences = self.break_long_sentence(words)
                processed_sentences.extend(broken_sentences)

        return ' '.join(processed_sentences)

    def break_long_sentence(self, words: List[str]) -> List[str]:
        """Break a long sentence at logical breaking points"""
        breaking_points = ['and', 'but', 'because', 'when', 'while', 'although', 'however', 'therefore']

        sentences = []
        current_sentence = []

        for i, word in enumerate(words):
            current_sentence.append(word)

            # Break at conjunctions if we're getting long
            if (len(current_sentence) >= 12
                    and word.lower() in breaking_points
                    and i < len(words) - 3):  # Don't break too close to end

                sentences.append(' '.join(current_sentence) + '.')
                current_sentence = []

            # Force break if sentence gets too long
            elif len(current_sentence) >= self.max_sentence_length:
                sentences.append(' '.join(current_sentence) + '.')
                current_sentence = []

        # Add remaining words
        if current_sentence:
            sentences.append(' '.join(current_sentence) + '.')

        return sentences

    def add_pronunciation_guides(self, text: str) -> str:
        """Add pronunciation guides for difficult words"""
        pronounced = text

        for word, pronunciation in self.pronunciation_guide.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            replacement = f"{word} ({pronunciation})"
            pronounced = re.sub(pattern, replacement, pronounced, flags=re.IGNORECASE)

        return pronounced

    def apply_dyslexia_formatting(self, text: str) -> str:
        """Apply dyslexia-friendly formatting"""
        sentences = re.split(r'[.!?]+', text)
        formatted_sentences = []

        sentence_count = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_count += 1

            # Add extra spacing every sentence
            formatted_sentence = sentence + '.\n'

            # Add paragraph break every 3 sentences
            if sentence_count % self.max_paragraph_length == 0:
                formatted_sentence += '\n'

            formatted_sentences.append(formatted_sentence)

        # Join with proper spacing
        formatted_text = ''.join(formatted_sentences)

        # Highlight key terms
        formatted_text = self.highlight_key_terms(formatted_text)

        return formatted_text

    def highlight_key_terms(self, text: str) -> str:
        """Highlight important terms for easier scanning"""
        key_terms = [
            'results', 'found', 'showed', 'increased', 'decreased',
            'better', 'worse', 'significant', 'important'
        ]

        highlighted = text
        for term in key_terms:
            pattern = r'\b' + re.escape(term) + r'\b'
            replacement = f"**{term.upper()}**"
            highlighted = re.sub(pattern, replacement, highlighted, flags=re.IGNORECASE)

        return highlighted

    def create_reading_tips(self) -> str:
        """Provide dyslexia-specific reading tips"""
        return """
-----

💡 **DYSLEXIA READING TIPS**

✅ **If words look jumbled:**
• Try covering text below the line you're reading
• Use a ruler or piece of paper as a guide

✅ **If you lose your place:**
• Take breaks between paragraphs
• Re-read the last sentence before continuing

✅ **If pronunciation is hard:**
• Sound out the syllables shown in parentheses
• Say difficult words out loud

✅ **Remember:**
• Your brain processes information differently - that's a strength!
• Take as much time as you need
• Understanding is more important than speed

🌟 **You've got this! Dyslexic minds often see patterns others miss.**
""".strip()

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide dyslexia-specific additional elements"""

        visual_elements = [
            "📏 Line spacing optimization (1.5x normal spacing)",
            "🔤 Dyslexia-friendly font recommendations (OpenDyslexic, Arial)",
            "📱 High contrast color scheme options",
            "👁️ Reading ruler overlay for line tracking",
            "🔍 Text zoom controls for comfortable reading",
            "📖 Word syllable break indicators",
            "🎨 Customizable background colors (cream, light blue)"
        ]

        action_items = [
            "📝 Create a word list of new vocabulary you learned",
            "🗣️ Practice saying difficult words out loud",
            "📚 Make your own simple summary in 5 sentences or less",
            "🎯 Pick the 3 most important facts from this research",
            "🖍️ Highlight or underline key points as you read",
            "⏸️ Take reading breaks every 10 minutes",
            "💭 Explain what you learned using your own words"
        ]

        # Add subject-specific elements
        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.extend([
                "📋 Write medical terms and their simple meanings",
                "🩺 Practice explaining health info to someone else",
                "❓ List questions about words you didn't understand"
            ])
        elif subject_area == 'education':
            action_items.extend([
                "📚 Connect this research to your own learning experiences",
                "👩‍🏫 Think about how teachers could use this information",
                "🎓 Identify study strategies mentioned in the research"
            ])

        return {
            'visual_elements': visual_elements,
            'action_items': action_items
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
The longitudinal investigation demonstrated that participants who received
the comprehensive intervention subsequently exhibited statistically significant
improvements in cognitive performance measures. Furthermore, the data analysis
revealed that approximately seventy-five percent of individuals who utilized
the methodology showed enhanced working memory capabilities compared to the
control group. Nevertheless, researchers acknowledge that additional studies
are necessary to facilitate broader implementation of these findings.
"""

    module = DyslexiaModule()
    context = {'subject_area': 'psychology', 'reading_level': 'Graduate'}

    print("🔤 DYSLEXIA MODULE TEST")
    print("=" * 60)
    print(module.process_text(sample_text, context))
    print("\n" + "=" * 60)

    additional = module.get_additional_elements(sample_text, context)
    print("📋 DYSLEXIA-FRIENDLY FEATURES:")
    for element in additional['visual_elements'][:3]:
        print(f"  • {element}")
