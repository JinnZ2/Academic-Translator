#!/usr/bin/env python3
"""
Scope & Claim Check Module for Academic Translator

Connects four things that usually get read separately:

    the headline  ->  the abstract  ->  the methods  ->  what was found

Most people are not misled by jargon. They are misled by the distance between
"cross-sectional survey of 40 undergraduates" and "SCIENTISTS PROVE X CAUSES
Y". This module measures that distance.

What it checks:

  DESIGN CEILING    Each study design can only support certain kinds of claim.
                    A cross-sectional study cannot show cause, no matter how
                    the abstract is worded.
  POPULATION        Who was actually studied - mice, cells, undergraduates,
                    one clinic - versus who the claim is about.
  SAMPLE SIZE       How many, and what that does to confidence.
  DURATION          An 8-week study cannot support a claim about years.
  EFFECT SIZE       "Statistically significant" is not "large". A tiny effect
                    in a big sample is significant and may not matter.
  SURROGATE         Measuring a blood marker is not measuring the illness.
  HEDGE DROP        The abstract says "may suggest"; the title says "does".

WHAT THIS MODULE DOES NOT DO

It does not judge whether the research is good. It reports mismatches between
what was claimed and what the stated method can support, and it quotes the
text that triggered every flag so you can check the call yourself. A flag is
a question to ask, not a verdict. Study design is a fact about the paper;
research quality is not something a regex can assess.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from academic_translator import AccessibilityModule
except ImportError:  # running this file directly
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from academic_translator import AccessibilityModule


@dataclass
class Finding:
    """One mismatch, with the text that caused it"""

    headline: str            # what to tell the reader
    quoted: str              # the phrase that triggered this
    why: str                 # why the two do not line up
    ask: str = ""            # what to go and check
    source: str = "The paper says"  # where the quote came from

    def render(self) -> str:
        lines = [f"**{self.headline}**",
                 f"  {self.source}: \"{self.quoted}\"",
                 f"  Why this matters: {self.why}"]
        if self.ask:
            lines.append(f"  Worth checking: {self.ask}")
        return "\n".join(lines)


@dataclass
class Design:
    """A study design and the strongest claim it can support"""

    name: str
    ceiling: str           # the strongest claim this design supports
    supports_cause: bool
    generalizes: bool = True
    human: bool = True
    note: str = ""


# Study designs, weakest claim ceiling first. The first match in the text
# that limits the claim is the one that governs.
DESIGNS: Dict[str, Design] = {
    'in vitro': Design('in vitro (cells in a dish)', 'what happens to cells in a dish',
                       supports_cause=False, generalizes=False, human=False,
                       note='Cells in a dish behave differently from cells in a body.'),
    'cell culture': Design('cell culture', 'what happens to cells in a dish',
                           supports_cause=False, generalizes=False, human=False),
    'animal model': Design('animal study', 'what happens in that animal',
                           supports_cause=False, generalizes=False, human=False),
    'mice': Design('mouse study', 'what happens in mice',
                   supports_cause=False, generalizes=False, human=False,
                   note='Most treatments that work in mice do not work in people.'),
    'mouse': Design('mouse study', 'what happens in mice',
                    supports_cause=False, generalizes=False, human=False),
    'rats': Design('rat study', 'what happens in rats',
                   supports_cause=False, generalizes=False, human=False),
    'rodent': Design('rodent study', 'what happens in rodents',
                     supports_cause=False, generalizes=False, human=False),
    'zebrafish': Design('zebrafish study', 'what happens in zebrafish',
                        supports_cause=False, generalizes=False, human=False),
    'case report': Design('case report', 'what happened to one person',
                          supports_cause=False, generalizes=False),
    'case series': Design('case series', 'what happened to a few people',
                          supports_cause=False, generalizes=False),
    'case study': Design('case study', 'what happened in one case',
                         supports_cause=False, generalizes=False),
    'cross-sectional': Design('cross-sectional study',
                              'that two things appear together at one moment',
                              supports_cause=False,
                              note='Everything was measured at one point in time, '
                                   'so there is no way to tell which came first.'),
    'case-control': Design('case-control study',
                           'that a factor is more common in one group',
                           supports_cause=False),
    'survey': Design('survey', 'what people said about themselves',
                     supports_cause=False,
                     note='Self-report measures what people say, not what they do.'),
    'self-report': Design('self-report measure', 'what people said about themselves',
                          supports_cause=False),
    'observational': Design('observational study', 'that two things occur together',
                            supports_cause=False),
    'cohort study': Design('cohort study',
                           'that one thing came before another in time',
                           supports_cause=False,
                           note='Following people over time shows order, but '
                                'something else may still explain both.'),
    'longitudinal': Design('longitudinal study', 'that one thing came before another',
                           supports_cause=False),
    'qualitative': Design('qualitative study', 'how a small number of people describe things',
                          supports_cause=False, generalizes=False,
                          note='Designed for depth, not for how common something is.'),
    'simulation': Design('simulation or model', 'what a model predicts',
                         supports_cause=False, generalizes=False, human=False),
    'pilot': Design('pilot study', 'whether a bigger study is workable',
                    supports_cause=False,
                    note='A pilot is not built to detect whether something works.'),
    'feasibility': Design('feasibility study', 'whether a bigger study is workable',
                          supports_cause=False),
    'meta-analysis': Design('meta-analysis', 'what the studies it pooled showed',
                            supports_cause=False,
                            note='A meta-analysis is only as good as the studies in it.'),
    'randomized controlled trial': Design('randomized controlled trial',
                                          'that the treatment caused the difference, '
                                          'in the people studied',
                                          supports_cause=True),
    'randomised controlled trial': Design('randomised controlled trial',
                                          'that the treatment caused the difference, '
                                          'in the people studied',
                                          supports_cause=True),
}

# Verbs that assert one thing made another happen.
CAUSAL_VERBS = [
    'causes', 'caused', 'cause', 'leads to', 'led to', 'lead to',
    'results in', 'resulted in', 'produces', 'produced', 'triggers',
    'triggered', 'prevents', 'prevented', 'prevent', 'cures', 'cured',
    'improves', 'improved', 'improve', 'reduces', 'reduced', 'reduce',
    'increases', 'increased', 'increase', 'boosts', 'boosted', 'boost',
    'protects against', 'protected against', 'eliminates', 'eliminated',
    'drives', 'driven by', 'enhances', 'enhanced', 'lowers', 'lowered',
    'raises', 'raised', 'makes', 'made', 'stops', 'stopped',
]

# Verbs that only assert the two things travel together.
ASSOCIATION_VERBS = [
    'associated with', 'linked to', 'correlated with', 'related to',
    'accompanied by', 'coincided with', 'predicted', 'predicts',
]

# Words that soften a claim.
HEDGE_WORDS = [
    'may', 'might', 'could', 'suggests', 'suggest', 'appears', 'appear',
    'seems', 'seem', 'possibly', 'potentially', 'preliminary', 'likely',
    'indicates', 'indicate', 'tends', 'tend',
]

# Outcomes that stand in for the thing people actually care about.
# Each is (display name, what it really is).
SURROGATE_MARKERS = {
    'hba1c': ('HbA1c', 'a blood sugar marker, not diabetes complications'),
    'cholesterol': ('cholesterol', 'a blood marker, not heart attacks'),
    'ldl': ('LDL', 'a blood marker, not heart attacks'),
    'blood pressure': ('blood pressure', 'a measurement, not strokes or heart attacks'),
    'bone density': ('bone density', 'a measurement, not fractures'),
    'tumor size': ('tumor size', 'a measurement, not survival'),
    'tumour size': ('tumour size', 'a measurement, not survival'),
    'biomarker': ('a biomarker', 'a stand-in measure, not the illness itself'),
    'antibody titer': ('antibody titer', 'an immune measure, not whether people got sick'),
    'self-reported intention': ('self-reported intention',
                                'what people said they would do, not what they did'),
    'intention to': ('intention', 'what people said they would do, not what they did'),
    'test scores': ('test scores', 'performance on one test, not the underlying ability'),
    'engagement': ('engagement', 'a proxy measure, not learning'),
}

# Claims about the long term.
LONG_TERM_WORDS = ['long-term', 'long term', 'lifelong', 'lasting', 'permanent',
                   'sustained', 'durable', 'for life', 'years to come']


class ScopeModule(AccessibilityModule):
    def __init__(self):
        self.small_sample = 30
        self.very_small_sample = 12
        self.short_study_days = 90

    def get_name(self) -> str:
        return "Scope & Claim Check"

    def get_description(self) -> str:
        return "Connects headline, abstract, methods and findings - flags claims the study design cannot support"

    # ------------------------------------------------------------------
    # Pulling the paper apart
    # ------------------------------------------------------------------

    def extract_title(self, text: str) -> str:
        """The first line, if it looks like a title rather than a sentence"""
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if len(line) > 250:
                return ""
            # A title rarely ends in a full stop and rarely opens a section.
            if re.match(r'^(abstract|introduction|background|methods?)\b', line, re.IGNORECASE):
                return ""
            return line.rstrip('.')
        return ""

    def extract_section(self, text: str, *names: str) -> str:
        """Pull one named section out of the paper"""
        joined = '|'.join(names)
        pattern = (rf'\b(?:{joined})\b\s*[:.\-]?\s*'
                   r'(.*?)(?=\n\s*\n\s*[A-Z][A-Za-z ]{2,30}\s*[:.]|\Z)')

        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def headline_text(self, text: str, context: Dict) -> str:
        """The headline alone - supplied by the reader, or the paper's title"""
        return (context or {}).get('external_headline') or self.extract_title(text)

    def claim_text(self, text: str, context: Dict) -> Tuple[str, str]:
        """The strongest claim available, and where it came from.

        An external headline wins: if a reader arrived here from a news
        story, that is the claim they need checked.
        """
        external = (context or {}).get('external_headline', '')
        if external:
            return external, "the headline you supplied"

        title = self.extract_title(text)
        abstract = self.extract_section(text, 'abstract', 'summary')

        if title and abstract:
            return f"{title}. {abstract}", "the paper's title and abstract"
        if title:
            return title, "the paper's title"
        if abstract:
            return abstract, "the paper's abstract"
        return text[:600], "the opening of the paper"

    # ------------------------------------------------------------------
    # The checks
    # ------------------------------------------------------------------

    def detect_designs(self, text: str) -> List[Tuple[Design, str]]:
        """Every study design named in the text, with the phrase that named it"""
        found = []
        seen = set()

        for marker in sorted(DESIGNS, key=len, reverse=True):
            match = re.search(r'\b' + re.escape(marker) + r'\b', text, re.IGNORECASE)
            if not match:
                continue

            design = DESIGNS[marker]
            if design.name in seen:
                continue

            seen.add(design.name)
            found.append((design, self.quote_around(text, match)))

        return found

    @staticmethod
    def quote_around(text: str, match: re.Match, width: int = 60) -> str:
        """A readable snippet of the text around a match"""
        start = max(0, match.start() - width)
        end = min(len(text), match.end() + width)

        snippet = ' '.join(text[start:end].split())
        prefix = '...' if start > 0 else ''
        suffix = '...' if end < len(text) else ''

        return f"{prefix}{snippet}{suffix}"

    def find_causal_language(self, claim: str) -> List[str]:
        """Causal verbs in the claim, excluding ones inside association phrases"""
        found = []

        for verb in sorted(CAUSAL_VERBS, key=len, reverse=True):
            for match in re.finditer(r'\b' + re.escape(verb) + r'\b', claim, re.IGNORECASE):
                window = claim[max(0, match.start() - 40):match.end() + 20].lower()
                # "was associated with reduced risk" is an association claim.
                if any(assoc in window for assoc in ASSOCIATION_VERBS):
                    continue
                found.append(match.group(0))
                break

        return found

    def check_causal_ceiling(self, claim: str, designs: List[Tuple[Design, str]]) -> List[Finding]:
        """Causal wording against a design that cannot establish cause"""
        if any(design.supports_cause for design, _ in designs):
            return []

        limiting = [(d, q) for d, q in designs if not d.supports_cause]
        if not limiting:
            return []

        causal_words = self.find_causal_language(claim)
        if not causal_words:
            return []

        design, quote = limiting[0]
        note = f" {design.note}" if design.note else ""

        return [Finding(
            headline=f"The claim says \"{causal_words[0]}\" but this is a {design.name}",
            quoted=quote,
            why=(f"A {design.name} can show {design.ceiling}. It cannot show that one "
                 f"thing caused another.{note}"),
            ask="Does the paper itself claim cause, or only the headline about it?",
        )]

    def check_population(self, claim: str, text: str,
                         designs: List[Tuple[Design, str]]) -> List[Finding]:
        """Who was studied, versus who the claim is about"""
        findings = []

        non_human = [(d, q) for d, q in designs if not d.human]
        if non_human:
            design, quote = non_human[0]
            human_words = re.search(
                r'\b(people|patients|adults|children|humans?|men|women|you)\b',
                claim, re.IGNORECASE)
            if human_words:
                findings.append(Finding(
                    headline=f"The claim is about {human_words.group(0).lower()}, "
                             f"but this is a {design.name}",
                    quoted=quote,
                    why=(f"This study can show {design.ceiling}. "
                         f"{design.note or 'Results in one species often do not carry over.'}"),
                    ask="Has this been tested in people yet?",
                ))

        narrow = [
            (r'\bundergraduates?\b|\bcollege students\b|\bpsychology students\b',
             'university students', 'Students are younger, healthier and more educated '
                                    'than the general population.'),
            (r'\bhealthy volunteers?\b', 'healthy volunteers',
             'People who are already well may respond differently from people who are ill.'),
            (r'\bmen only\b|\bmale participants\b|\ball male\b', 'men only',
             'Findings from one sex do not automatically apply to another.'),
            (r'\bwomen only\b|\bfemale participants\b|\ball female\b', 'women only',
             'Findings from one sex do not automatically apply to another.'),
            (r'\ba single (?:site|centre|center|clinic|school|hospital)\b', 'one site only',
             'One place may not resemble others.'),
        ]

        for pattern, label, why in narrow:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                findings.append(Finding(
                    headline=f"The people studied were {label}",
                    quoted=self.quote_around(text, match),
                    why=why,
                    ask="Are you, or the person you care about, like the people studied?",
                ))

        return findings

    @staticmethod
    def find_sample_sizes(text: str) -> List[int]:
        """Every stated participant count, however the paper wrote it"""
        sizes = [int(n) for n in re.findall(r'\bn\s*=\s*(\d+)', text, re.IGNORECASE)]
        sizes += [int(n) for n in re.findall(
            r'\b(\d+)\s+(?:participants?|patients?|subjects?|people|students?)\b',
            text, re.IGNORECASE)]
        return sizes

    def check_sample_size(self, text: str) -> List[Finding]:
        """How many were studied"""
        sizes = self.find_sample_sizes(text)

        if not sizes:
            return [Finding(
                headline="The number of people studied is not stated in plain sight",
                quoted="(no sample size found)",
                why="Without knowing how many were studied, the result cannot be weighed.",
                ask="Search the paper for 'n =' or 'participants'.",
            )]

        total = max(sizes)
        if total >= self.small_sample:
            return []

        match = re.search(rf'\b(?:n\s*=\s*)?{total}\b', text)
        quote = self.quote_around(text, match) if match else f"n = {total}"

        severity = ("very small" if total <= self.very_small_sample else "small")

        return [Finding(
            headline=f"This is a {severity} study: {total} participants",
            quoted=quote,
            why=("With few participants, a result can appear by chance, and unusual "
                 "individuals pull the average a long way."),
            ask="Has a larger study found the same thing?",
        )]

    def check_duration(self, claim: str, text: str) -> List[Finding]:
        """Study length against claims about the long term"""
        long_term = [w for w in LONG_TERM_WORDS if w in claim.lower()]
        if not long_term:
            return []

        match = re.search(r'\b(\d+)[\s-]*(day|week|month|year)s?\b', text, re.IGNORECASE)
        if not match:
            return []

        amount, unit = int(match.group(1)), match.group(2).lower()
        days = amount * {'day': 1, 'week': 7, 'month': 30, 'year': 365}[unit]

        if days > self.short_study_days:
            return []

        return [Finding(
            headline=f"The claim says \"{long_term[0]}\" but the study ran {amount} {unit}s",
            quoted=self.quote_around(text, match),
            why=f"{amount} {unit}s cannot show what happens over years.",
            ask="Did anyone follow these participants up later?",
        )]

    def check_effect_size(self, text: str) -> List[Finding]:
        """Statistical significance is not the same as a difference that matters"""
        findings = []

        has_p_value = re.search(r'\bp\s*[<>=]\s*\.?\d', text, re.IGNORECASE)
        significant = re.search(r'\bstatistically significant\b|\bsignificant(?:ly)?\b',
                                text, re.IGNORECASE)

        # A confidence interval quantifies the effect just as an effect size
        # does, so either one counts as the magnitude having been reported.
        effect_size = re.search(
            r"\b(?:cohen'?s\s*d|effect size|odds ratio|\bOR\b|hazard ratio|"
            r"risk ratio|\bCI\b|confidence interval|\br\s*=)\s*[:=]?\s*"
            r"[^.\n]{0,20}(-?\d*\.?\d+)",
            text, re.IGNORECASE)

        if (has_p_value or significant) and not effect_size:
            match = significant or has_p_value
            findings.append(Finding(
                headline="The paper reports significance but no effect size",
                quoted=self.quote_around(text, match),
                why=("\"Significant\" means the result is probably not chance. It says "
                     "nothing about how big the difference is. A tiny difference in a "
                     "large study is significant and may not matter to anyone."),
                ask="How big was the difference, in units you care about?",
            ))

        # A small effect that is nonetheless being described as significant.
        cohens_d = re.search(r"\bcohen'?s\s*d\s*[:=]\s*(-?\d*\.?\d+)", text, re.IGNORECASE)
        if cohens_d:
            value = abs(float(cohens_d.group(1)))
            if value < 0.2:
                findings.append(Finding(
                    headline=f"The effect is small (Cohen's d = {value})",
                    quoted=self.quote_around(text, cohens_d),
                    why=("Cohen's d below 0.2 is generally considered a small effect - "
                         "real, but not something most people would notice."),
                    ask="Is a difference this size worth acting on?",
                ))

        return findings

    def check_surrogate_outcomes(self, headline: str, text: str) -> List[Finding]:
        """A stand-in measurement being reported as the thing itself.

        Checked against the headline alone, not the abstract: an abstract
        naturally names the marker when describing its methods. A paper
        titled "Exercise lowers HbA1c" is being precise about what it
        measured, so there is nothing to flag. The mismatch exists when the
        headline promises the illness and the study measured the marker.
        """
        findings = []

        for marker, (display, meaning) in SURROGATE_MARKERS.items():
            pattern = r'\b' + re.escape(marker) + r'\b'

            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue

            if headline and re.search(pattern, headline, re.IGNORECASE):
                continue  # the headline says what was measured - nothing to flag

            findings.append(Finding(
                headline=f"What was measured was {display}",
                quoted=self.quote_around(text, match),
                why=f"That is {meaning}. The claim is about something broader.",
                ask="Did the study measure what you actually care about, "
                    "or something that stands in for it?",
            ))
            break  # one is enough to make the point

        return findings

    def check_hedge_drop(self, text: str, context: Dict) -> List[Finding]:
        """The body hedges; the title or headline does not"""
        title = self.headline_text(text, context)

        if not title:
            return []

        body = self.extract_section(text, 'conclusion', 'conclusions', 'discussion') \
            or self.extract_section(text, 'abstract', 'summary')
        if not body:
            return []

        title_hedged = any(re.search(r'\b' + h + r'\b', title, re.IGNORECASE)
                           for h in HEDGE_WORDS)
        body_hedges = [h for h in HEDGE_WORDS
                       if re.search(r'\b' + h + r'\b', body, re.IGNORECASE)]

        if title_hedged or not body_hedges:
            return []

        if not self.find_causal_language(title):
            return []

        external = bool((context or {}).get('external_headline'))

        return [Finding(
            headline="The headline is more certain than the paper",
            quoted=title,
            why=(f"The paper's own wording hedges - it uses \"{body_hedges[0]}\" - "
                 "but the headline states it flatly."),
            ask="Which wording does the paper's conclusion actually use?",
            source="The headline says" if external else "The title says",
        )]

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def analyze(self, text: str, context: Dict = None) -> Dict:
        """Run every check and return the findings plus what they were based on.

        Analysis runs on the paper's own words where they are available. By
        the time process_text is called the text has been jargon-expanded,
        and a module that quotes the paper should quote what it really said.
        """
        context = context or {}
        text = context.get('original_text') or text
        claim, claim_source = self.claim_text(text, context)
        headline = self.headline_text(text, context)
        designs = self.detect_designs(text)

        findings: List[Finding] = []
        findings += self.check_causal_ceiling(claim, designs)
        findings += self.check_population(claim, text, designs)
        findings += self.check_sample_size(text)
        findings += self.check_duration(claim, text)
        findings += self.check_effect_size(text)
        findings += self.check_surrogate_outcomes(headline, text)
        findings += self.check_hedge_drop(text, context)

        return {
            'claim': claim,
            'claim_source': claim_source,
            'designs': designs,
            'findings': findings,
        }

    def supportable_headline(self, text: str, analysis: Dict) -> str:
        """State what an accurate headline would have to include.

        This deliberately does not invent a headline. It lists the facts any
        honest headline about this study has to carry, because guessing the
        outcome wording is exactly the error this module exists to catch.
        """
        parts = []
        designs = analysis['designs']

        sizes = self.find_sample_sizes(text)
        if sizes:
            parts.append(f"the number studied ({max(sizes)})")

        non_human = [d for d, _ in designs if not d.human]
        if non_human:
            parts.append(f"that this was a {non_human[0].name}")

        limiting = [d for d, _ in designs if not d.supports_cause]
        if limiting:
            parts.append(f"that a {limiting[0].name} shows {limiting[0].ceiling}")
            parts.append("association wording, not cause wording "
                         "(\"was linked to\", not \"reduces\")")
        elif designs:
            parts.append(f"that the finding applies to the people studied, "
                         f"not everyone")

        match = re.search(r'\b(\d+)[\s-]*(day|week|month|year)s?\b', text, re.IGNORECASE)
        if match:
            parts.append(f"how long it ran ({match.group(1)} {match.group(2)}s)")

        if not parts:
            return ("Not enough detail was found in the text to say what an "
                    "accurate headline would need.")

        lines = ["An accurate headline about this study would have to include:", ""]
        lines.extend(f"• {part}" for part in parts)

        return "\n".join(lines)

    def process_text(self, text: str, context: Dict) -> str:
        """Prepend the scope check, then the paper"""
        analysis = self.analyze(text, context)
        source = (context or {}).get('original_text') or text
        report = self.build_report(source, analysis)

        return f"{report}\n\n{text}"

    def build_report(self, text: str, analysis: Dict) -> str:
        """The scope check itself"""
        findings = analysis['findings']
        designs = analysis['designs']

        lines = ["🔬 **SCOPE CHECK**", ""]
        lines.append(f"Claim checked, from {analysis['claim_source']}:")
        lines.append(f"> {self.shorten(analysis['claim'], 300)}")
        lines.append("")

        if designs:
            lines.append("**What kind of study this is**")
            lines.append("")
            for design, _quote in designs[:3]:
                lines.append(f"• {design.name} — can show {design.ceiling}")
            lines.append("")

        if findings:
            lines.append(f"**{len(findings)} thing(s) to check before believing the claim**")
            lines.append("")
            for index, finding in enumerate(findings, start=1):
                lines.append(f"{index}. {finding.render()}")
                lines.append("")
        else:
            lines.append("**No mismatches found** between the claim and the stated "
                         "method. That is not the same as the research being correct - "
                         "only that the claim does not exceed the design.")
            lines.append("")

        lines.append("-----")
        lines.append("")
        lines.append(self.supportable_headline(text, analysis))
        lines.append("")
        lines.append("-----")
        lines.append("")
        lines.append("_This check compares wording against stated method. It does not "
                     "assess whether the research is good. Every flag above quotes the "
                     "text that triggered it, so you can judge the call yourself._")
        lines.append("")
        lines.append("-----")

        return "\n".join(lines)

    @staticmethod
    def shorten(text: str, limit: int) -> str:
        """Trim a quote to a readable length"""
        flat = ' '.join(text.split())
        return flat if len(flat) <= limit else flat[:limit].rstrip() + '...'

    def get_additional_elements(self, text: str, context: Dict) -> Dict[str, List[str]]:
        """Provide scope-specific additional elements"""
        analysis = self.analyze(text, context)
        count = len(analysis['findings'])

        visual_elements = [
            "🔬 Claim-to-method comparison at the top of the report",
            f"⚠️ {count} scope flag(s), each quoting the text that raised it",
            "📐 Study design shown with the strongest claim it can support",
            "📋 Checklist of what an accurate headline must include",
            "🔗 Headline, abstract, method and findings shown side by side",
        ]

        action_items = [
            "🔍 Read the methods section before the abstract - it sets the ceiling",
            "📰 Compare the headline that brought you here to the paper's own conclusion",
            "❓ For each flag, find the paper's own wording and judge the call yourself",
            "📊 Look for the effect size, not just whether it was significant",
            "👥 Check whether you resemble the people who were actually studied",
        ]

        subject_area = (context or {}).get('subject_area', 'general')

        if subject_area == 'medical':
            action_items.extend([
                "🩺 Ask your doctor whether this study applies to your situation",
                "💊 Ask whether the outcome measured is the one that matters to you",
            ])
        elif subject_area == 'education':
            action_items.append(
                "🎓 Check whether the students studied resemble the ones you teach")

        return {
            'visual_elements': visual_elements,
            'action_items': action_items,
        }


# Example usage and testing
if __name__ == "__main__":
    sample_text = """
Daily Coffee Consumption Reduces Risk of Cognitive Decline

Abstract: This cross-sectional study examined the relationship between coffee
consumption and cognitive performance in older adults. We surveyed 24
participants at a single clinic. Results showed that higher self-reported
coffee intake was significantly associated with better test scores
(p < 0.03). These findings suggest that coffee may protect against long-term
cognitive decline.

Methods: A cross-sectional survey was administered to 24 healthy volunteers
aged 65-80 over a 4 week period. Coffee intake was measured by self-report.

Conclusion: Coffee consumption may be beneficial for cognitive health.
"""

    module = ScopeModule()
    context = {'subject_area': 'medical', 'reading_level': 'College'}

    print("🔬 SCOPE MODULE TEST")
    print("=" * 70)
    print(module.build_report(sample_text, module.analyze(sample_text, context)))
