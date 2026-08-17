#!/usr/bin/env python3
"""
ADHD Accessibility Module for Academic Translator

Transforms dense academic text into ADHD-friendly formats:

- Chunks text into digestible pieces
- Adds progress indicators and visual breaks
- Highlights key information
- Provides TL;DR summaries
- Includes fidget breaks and pacing suggestions

Created by and for the ADHD community.
"""

import re
from typing import Dict, List
from academic_translator import AccessibilityModule

class ADHDModule(AccessibilityModule):
    def __init__(self):
        self.chunk_size = 150  # words per chunk
        self.key_indicators = [
        'important', 'significant', 'found', 'discovered', 'results show',
        'concluded', 'evidence', 'data suggests', 'study reveals'
        ]
        self.break_indicators = [
        '🧠 Brain break suggestion: Take 30 seconds to look away',
        '💭 Pause point: What did you just learn?',
        '🎯 Focus check: Are you still with us?',
        '⚡ Energy boost: Stand up and stretch!',
        '🔄 Reset moment: Deep breath, you\'re doing great!'
        ]

    def get_name(self) -> str:
        return "ADHD-Friendly Format"

    def get_description(self) -> str:
        return "Breaks text into chunks, highlights key points, adds progress tracking and brain breaks"

    def process_text(self, text: str, context: Dict) -> str:
        """Transform text for ADHD-friendly reading"""

        # Split into manageable chunks
        chunks = self.create_text_chunks(text)

        # Process each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Add progress indicator
            progress = f"📍 **Section {i+1} of {len(chunks)}** ({int((i+1)/len(chunks)*100)}% complete)\n\n"

            # Highlight key information
            highlighted_chunk = self.highlight_key_info(chunk)

            # Add TL;DR for longer chunks
            tldr = self.create_chunk_tldr(highlighted_chunk)

            # Add brain break suggestion every few chunks
            brain_break = ""
            if i > 0 and i % 3 == 0:
                brain_break = f"\n\n🧠 **{self.break_indicators[i % len(self.break_indicators)]}**\n\n"

            processed_chunk = f"{progress}{tldr}{highlighted_chunk}{brain_break}"
            processed_chunks.append(processed_chunk)

        # Add overall structure overview at the beginning
        structure_overview = self.create_structure_overview(len(chunks))

        # Add completion celebration at the end
        completion = self.create_completion_message(context.get('subject_area', 'research'))

        return f"{structure_overview}\n\n" + "\n\n---\n\n".join(processed_chunks) + f"\n\n{completion}"

    def create_text_chunks(self, text: str) -> List[str]:
        """Break text into ADHD-friendly chunks"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = []
        word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_words = len(sentence.split())

            # If adding this sentence would exceed chunk size, start new chunk
            if word_count + sentence_words > self.chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                word_count = sentence_words
            else:
                current_chunk.append(sentence)
                word_count += sentence_words

        # Add final chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')

        return chunks

    def highlight_key_info(self, text: str) -> str:
        """Highlight important information for ADHD readers"""
        highlighted = text

        # Highlight key indicator phrases
        for indicator in self.key_indicators:
            pattern = r'\b' + re.escape(indicator) + r'\b'
            replacement = f"**🎯 {indicator.upper()}**"
            highlighted = re.sub(pattern, replacement, highlighted, flags=re.IGNORECASE)

        # Highlight numbers and statistics
        highlighted = re.sub(r'\b(\d+\.?\d*%?)\b', r'**\1**', highlighted)

        # Highlight research outcomes
        highlighted = re.sub(r'\b(increased|decreased|improved|reduced|better|worse)\b',
                           r'**🔺\1**', highlighted, flags=re.IGNORECASE)

        return highlighted

    def create_chunk_tldr(self, chunk: str) -> str:
        """Create TL;DR summary for chunks over 100 words"""
        words = chunk.split()
        if len(words) < 100:
            return ""

        # Extract the most important sentence (heuristic: contains key indicators)
        sentences = re.split(r'[.!?]+', chunk)
        important_sentences = []

        for sentence in sentences:
            for indicator in self.key_indicators:
                if indicator.lower() in sentence.lower():
                    important_sentences.append(sentence.strip())
                    break

        if important_sentences:
            tldr = important_sentences[0][:200] + "..." if len(important_sentences[0]) > 200 else important_sentences[0]
            return f"⚡ **TL;DR:** {tldr}\n\n"

        return ""

    def create_structure_overview(self, num_chunks: int) -> str:
        """Create overview of document structure for ADHD readers"""
        overview = f"""

        🗺️ **NAVIGATION MAP**
        📖 This research paper has been broken into {num_chunks} bite-sized sections
        ⏱️ Estimated reading time: {num_chunks * 2} minutes
        🎯 Look for highlighted **KEY POINTS** and 🔺**IMPORTANT CHANGES**
        🧠 Brain breaks are built in every 3 sections
        📍 Progress indicators show how far you've come

        💡 **ADHD Reading Tips:**
        • Read at your own pace - no rush!
        • Use the TL;DR summaries if you need quick overviews
        • Take the brain breaks - they help retention
        • Come back to sections if your mind wanders
        • You've got this! 💪
    """
        return overview.strip()

    def create_completion_message(self, subject_area: str) -> str:
        """Celebrate completion with ADHD-friendly encouragement"""
        celebrations = [
            "🎉 **YOU DID IT!** You just understood academic research - that's seriously impressive!",
            "💪 **AMAZING!** Your ADHD brain just processed complex research like a boss!",
            "🏆 **VICTORY!** You stuck with it and now you know something new!",
            "⭐ **SUPERSTAR!** You just turned academic jargon into useful knowledge!",
            "🚀 **FANTASTIC!** Your curiosity and persistence paid off!"
        ]

        import random
        celebration = random.choice(celebrations)

        return f"""

        {celebration}

        🧠 **What your ADHD brain just accomplished:**
        ✅ Processed {subject_area} research
        ✅ Translated academic jargon
        ✅ Identified key findings
        ✅ Connected research to real life
        ✅ Stayed focused through multiple sections

        🎯 **Next steps for your ADHD brain:**
        • Take a victory break - you earned it!
        • Think about how this applies to your life
        • Share what you learned (teaching helps retention)
        • Remember: you can understand complex research!

        **Keep being curious - the world needs your unique perspective!** 🌟
    """

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide ADHD-specific additional elements"""

        visual_elements = [
            "📊 Progress bars showing completion status",
            "🎯 Color-coded key findings highlights",
            "🧠 Visual brain break reminders",
            "📍 Section navigation breadcrumbs",
            "⚡ TL;DR summary boxes for quick scanning"
        ]

        action_items = [
            "📝 Create a one-sentence summary of each section",
            "🗣️ Explain one key finding to someone else",
            "🎯 Identify the most interesting discovery",
            "💭 Think of one way this research applies to your life",
            "⭐ Celebrate understanding complex research with your ADHD brain!"
        ]

        # Add subject-specific ADHD action items
        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.extend([
                "🩺 Write down questions to ask your doctor",
                "📋 Research if there are clinical trials you could join",
                "💊 Check if this research affects your current treatments"
            ])
        elif subject_area == 'psychology':
            action_items.extend([
                "🧠 Reflect on how these findings relate to your experiences",
                "📚 Consider how this knowledge could help your relationships",
                "💭 Think about whether you want to discuss this with a therapist"
            ])
        elif subject_area == 'education':
            action_items.extend([
                "🎓 Consider how this could improve learning strategies",
                "👨‍🏫 Share relevant findings with teachers or tutors",
                "📖 Apply these insights to your own study habits"
            ])

        return {
            'visual_elements': visual_elements,
            'action_items': action_items
        }

        # Example usage and testing

if __name__ == "__main__":
    # Test the ADHD module with sample academic text
    sample_text = """
    The present study investigated the efficacy of cognitive behavioral therapy (CBT)
    interventions for adults with attention deficit hyperactivity disorder (ADHD).
    A randomized controlled trial was conducted with 127 participants diagnosed with
    ADHD. Participants were randomly assigned to either the CBT intervention group
    (n=64) or the waitlist control group (n=63). The CBT intervention consisted of
    12 weekly sessions focused on executive functioning skills, time management,
    and organization strategies. Results indicated statistically significant
    improvements in ADHD symptoms as measured by the Adult ADHD Self-Report Scale
    (ASRS-v1.1) for the intervention group compared to controls (p<0.001, Cohen's d=0.82).
    Additionally, participants in the CBT group demonstrated significant improvements
    in executive functioning as assessed by the Behavior Rating Inventory of Executive
    Function-Adult version (BRIEF-A). These findings suggest that CBT interventions
    can be highly effective for managing ADHD symptoms in adults. The study provides
    evidence for the implementation of structured CBT programs in clinical settings
    for adult ADHD treatment.
    """

    module = ADHDModule()
    context = {'subject_area': 'psychology', 'reading_level': 'Graduate'}

    print("🧠 ADHD MODULE TEST")
    print("=" * 50)
    print(module.process_text(sample_text, context))
    print("\n" + "=" * 50)

    additional = module.get_additional_elements(sample_text, context)
    print("📋 ADDITIONAL ELEMENTS:")
    print(f"Visual: {additional['visual_elements'][:2]}")
    print(f"Actions: {additional['action_items'][:3]}")
