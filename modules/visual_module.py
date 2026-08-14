#!/usr/bin/env python3
"""
Visual Processing Accessibility Module for Academic Translator

Transforms text-heavy academic content into visual formats:

- Creates ASCII diagrams and flowcharts
- Converts data to visual representations
- Identifies concepts that need visual explanation
- Generates infographic-style layouts
- Provides visual metaphors and analogies

Perfect for visual learners who think in pictures.
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


class VisualModule(AccessibilityModule):
    def __init__(self):
        self.visual_indicators = {
            'process': ['method', 'procedure', 'steps', 'process', 'protocol', 'workflow'],
            'comparison': ['versus', 'compared to', 'difference', 'contrast', 'better than'],
            'relationship': ['correlation', 'relationship', 'connected', 'associated', 'linked'],
            'change': ['increased', 'decreased', 'improved', 'reduced', 'changed', 'effect'],
            'structure': ['components', 'parts', 'elements', 'structure', 'framework'],
            'timeline': ['before', 'after', 'during', 'weeks', 'months', 'timeline', 'follow-up']
        }

        self.chart_symbols = {
            'increase': '📈',
            'decrease': '📉',
            'stable': '➡️',
            'comparison': '⚖️',
            'process': '🔄',
            'structure': '🏗️',
            'relationship': '🔗',
            'timeline': '📅'
        }

    def get_name(self) -> str:
        return "Visual Processing Support"

    def get_description(self) -> str:
        return "Converts text to diagrams, flowcharts, and visual representations for visual learners"

    def process_text(self, text: str, context: Dict) -> str:
        """Transform text with visual elements and diagrams"""

        # Identify visual opportunities
        visual_concepts = self.identify_visual_concepts(text)

        # Create visual header
        visual_header = self.create_visual_header(context)

        # Process text with visual indicators
        processed_text = self.add_visual_indicators(text)

        # Create visual diagrams
        diagrams = self.create_diagrams(text, visual_concepts)

        # Add visual metaphors
        visual_metaphors = self.add_visual_metaphors(processed_text, context.get('subject_area', 'general'))

        # Combine everything
        return f"{visual_header}\n\n{visual_metaphors}\n\n{diagrams}\n\n{processed_text}"

    def identify_visual_concepts(self, text: str) -> Dict[str, List[str]]:
        """Identify concepts that would benefit from visual representation"""
        concepts = {}
        text_lower = text.lower()

        for concept_type, indicators in self.visual_indicators.items():
            found_indicators = []
            for indicator in indicators:
                if indicator in text_lower:
                    # Extract context around the indicator
                    pattern = rf'.{{0,50}}\b{re.escape(indicator)}\b.{{0,50}}'
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    found_indicators.extend(matches)

            if found_indicators:
                concepts[concept_type] = found_indicators[:3]  # Limit to 3 examples

        return concepts

    def create_visual_header(self, context: Dict) -> str:
        """Create visual overview of the research"""
        subject_area = context.get('subject_area', 'research')

        # Subject-specific icons
        subject_icons = {
            'medical': '🩺🧬💊',
            'psychology': '🧠💭🤝',
            'education': '📚🎓👩‍🏫',
            'social_science': '🌍📊🏛️',
            'science': '🔬⚗️🧪'
        }

        icons = subject_icons.get(subject_area, '📖🔍💡')

        header = f"""
┌─────────────────────────────────────────────────────────┐
│  🎨 VISUAL RESEARCH OVERVIEW                            │
│                                                         │
│  📊 Subject: {subject_area.title()} {icons}
│  🎯 Visual Format: Diagrams + Charts + Metaphors        │
│  👁️ Optimized for: Visual learners & processors         │
│                                                         │
│  📖 Look for: 📈Charts 🔄Flowcharts 🏗️Structures        │
└─────────────────────────────────────────────────────────┘
"""
        return header.strip()

    def add_visual_indicators(self, text: str) -> str:
        """Add visual symbols to highlight different types of information"""
        processed = text

        # Add icons for different types of content
        replacements = [
            (r'\b(results?|findings?|discovered?)\b', r'🔍 \1'),
            (r'\b(method|procedure|protocol)\b', r'⚙️ \1'),
            (r'\b(increased?|improved?|better)\b', r'📈 \1'),
            (r'\b(decreased?|reduced?|lower)\b', r'📉 \1'),
            (r'\b(compared? to|versus)\b', r'⚖️ \1'),
            (r'\b(correlation|relationship|connected)\b', r'🔗 \1'),
            (r'\b(participants?|subjects?)\b', r'👥 \1'),
            (r'\b(significant|important)\b', r'⭐ \1'),
        ]

        for pattern, replacement in replacements:
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        return processed

    def create_diagrams(self, text: str, visual_concepts: Dict[str, List[str]]) -> str:
        """Create ASCII diagrams based on identified concepts"""
        diagrams = []

        # Create process diagrams
        if 'process' in visual_concepts:
            process_diagram = self.create_process_diagram(text)
            if process_diagram:
                diagrams.append(process_diagram)

        # Create comparison charts
        if 'comparison' in visual_concepts:
            comparison_chart = self.create_comparison_chart(text)
            if comparison_chart:
                diagrams.append(comparison_chart)

        # Create relationship diagrams
        if 'relationship' in visual_concepts:
            relationship_diagram = self.create_relationship_diagram(text)
            if relationship_diagram:
                diagrams.append(relationship_diagram)

        # Create timeline if temporal elements found
        if 'timeline' in visual_concepts:
            timeline = self.create_timeline_diagram(text)
            if timeline:
                diagrams.append(timeline)

        return "\n\n".join(diagrams) if diagrams else ""

    def create_process_diagram(self, text: str) -> str:
        """Create a process flowchart from methodology"""
        # Look for step-like language
        steps = re.findall(r'(first|second|third|then|next|finally|step \d+)[^.]*', text, re.IGNORECASE)

        if len(steps) < 2:
            return ""

        return """
🔄 **RESEARCH PROCESS FLOWCHART**

    START
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Step 1    │───▶│   Step 2    │───▶│   Step 3    │
│ Participants│    │ Intervention│    │  Measure    │
│  Selected   │    │  Applied    │    │  Results    │
└─────────────┘    └─────────────┘    └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
 Select people     Apply treatment      Check if it
 for the study      or intervention       worked
""".strip()

    def create_comparison_chart(self, text: str) -> str:
        """Create a before/after or group comparison chart"""
        # Look for numerical comparisons
        numbers = re.findall(r'(\d+\.?\d*)\s*(?:%|percent|points?)', text)

        if len(numbers) >= 2:
            return f"""
⚖️ **COMPARISON VISUALIZATION**

BEFORE vs AFTER (or Group A vs Group B)

Before/Control Group    │    After/Treatment Group
                        │
    😐 Baseline         │        😊 Improved
     {numbers[0]}%                │         {numbers[1]}%
                        │
    ████████░░          │        ███████████
    (Lower scores)      │        (Higher scores)
                        │
Results show significant improvement! 📈
""".strip()

        return """
⚖️ **GROUP COMPARISON**

   Control Group          Treatment Group
        │                        │
   😐 No change           😊 Improvement seen
        │                        │
   ████████░░░           ████████████
   (Stayed same)         (Got better)

The treatment group showed better results! ⭐
""".strip()

    def create_relationship_diagram(self, text: str) -> str:
        """Create a diagram showing relationships between variables"""
        return """
🔗 **RELATIONSHIP MAP**

    Factor A                 Factor B
       │                       │
       │    📈 Positive        │
       │   Relationship        │
       │                       │
       └───────────────────────┘
              ↕️
    When A increases,
    B also increases

    💡 Remember: Correlation ≠ Causation
    (Things can be related without one causing the other)
""".strip()

    def create_timeline_diagram(self, text: str) -> str:
        """Create a timeline of the research or intervention"""
        return """
📅 **RESEARCH TIMELINE**

Week 1         Week 6         Week 12        Follow-up
  │              │               │              │
  ▼              ▼               ▼              ▼
┌─────┐       ┌────────┐     ┌─────┐       ┌─────┐
│Start│──────▶│Check   │────▶│ End │──────▶│Check│
│Study│       │Progress│     │Study│       │Later│
└─────┘       └────────┘     └─────┘       └─────┘
   📝             📊            📈            🔄
Baseline      Mid-point      Final         Long-term
measures      assessment     results       effects
""".strip()

    def add_visual_metaphors(self, text: str, subject_area: str) -> str:
        """Add visual metaphors to explain complex concepts"""
        metaphors = {
            'medical': {
                'statistical significance': "🎯 Like hitting a bullseye - the result is so clear it's almost impossible it happened by chance",
                'placebo effect': '🍭 Like thinking candy medicine will help - your mind can sometimes create real effects from fake treatments',
                'double-blind study': '👓🕶️ Like both patient and doctor wearing blindfolds - nobody knows who gets real treatment until the end'
            },
            'psychology': {
                'cognitive load': "🧠💾 Like your brain's RAM - too much information at once and it starts slowing down",
                'correlation': "🌧️☂️ Like rain and umbrellas - they appear together but rain doesn't cause umbrellas",
                'sample size': '🫐 Like judging all blueberries by tasting just a few - bigger sample = better guess about all blueberries'
            },
            'education': {
                'scaffolding': "🏗️ Like construction scaffolding - temporary support that's removed once the building (learning) is strong",
                'zone of proximal development': '🎯 Like the "just right" level in video games - not too easy, not too hard',
                'metacognition': '🪞 Like having a mirror for your thinking - being aware of how you learn and think'
            }
        }

        subject_metaphors = metaphors.get(subject_area, {})
        enhanced_text = text

        for concept, metaphor in subject_metaphors.items():
            if concept.lower() in text.lower():
                enhanced_text = enhanced_text.replace(
                    concept,
                    f"{concept} ({metaphor})"
                )

        return enhanced_text

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide visual-specific additional elements"""

        visual_elements = [
            "📊 Interactive bar charts showing before/after comparisons",
            "🔄 Animated flowcharts of research methodology",
            "🎯 Infographic summaries of key findings",
            "🗺️ Concept maps linking related ideas",
            "📈 Line graphs showing changes over time",
            "🏗️ Structural diagrams of frameworks or models",
            "🔗 Network diagrams showing relationships",
            "📱 Mobile-friendly visual summaries"
        ]

        action_items = [
            "🎨 Sketch your own diagram of the key concepts",
            "📊 Create a simple chart of the main findings",
            "🗺️ Map out how this research connects to what you already know",
            "📸 Take mental pictures of the visual diagrams",
            "🖼️ Imagine explaining this using only pictures",
            "🎭 Create visual metaphors for complex concepts",
            "📝 Draw a timeline of the research process"
        ]

        # Add subject-specific visual elements
        subject_area = context.get('subject_area', 'general')

        if subject_area == 'medical':
            visual_elements.extend([
                "🫀 Body system diagrams showing treatment effects",
                "💊 Drug pathway visualizations",
                "📊 Patient outcome comparison charts"
            ])
            action_items.extend([
                "🏥 Visualize how this applies to your health situation",
                "📋 Create a visual summary to show your doctor"
            ])

        elif subject_area == 'psychology':
            visual_elements.extend([
                "🧠 Brain process flowcharts",
                "🤝 Social interaction diagrams",
                "📈 Behavioral change visualizations"
            ])
            action_items.extend([
                "💭 Map your own thought patterns related to this research",
                "🎭 Visualize how these findings apply to your relationships"
            ])

        return {
            'visual_elements': visual_elements,
            'action_items': action_items
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
This randomized controlled trial examined the effectiveness of mindfulness-based
stress reduction (MBSR) compared to a control group. Participants were randomly
assigned to either the 8-week MBSR intervention (n=45) or waitlist control (n=47).
The MBSR group showed statistically significant reductions in anxiety scores
(p<0.001) and increased mindfulness ratings compared to controls. Correlation
analysis revealed a strong negative relationship between mindfulness practice
frequency and reported stress levels (r=-0.72). These findings suggest that
regular mindfulness practice can effectively reduce anxiety and stress.
"""

    module = VisualModule()
    context = {'subject_area': 'psychology', 'reading_level': 'College'}

    print("🎨 VISUAL MODULE TEST")
    print("=" * 70)
    print(module.process_text(sample_text, context))
    print("\n" + "=" * 70)

    additional = module.get_additional_elements(sample_text, context)
    print("📋 ADDITIONAL VISUAL ELEMENTS:")
    for element in additional['visual_elements'][:3]:
        print(f"  • {element}")
