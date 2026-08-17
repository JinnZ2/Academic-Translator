#!/usr/bin/env python3
"""
Context-aware term matching for Academic Translator.

The naive approach - substitute every glossary term wherever its exact
characters appear - fails in two opposite directions:

  MISSES    'hypothesis' is in the glossary, so 'hypotheses' sails past
            untranslated. So do 'clinical trials', 'correlated',
            'randomised' (British spelling) and 'n=240' (no space).

  FALSE     'construct', 'power', 'scaffolding' and 'triangulation' are
  POSITIVES technical terms in one context and ordinary English in another.
            Blind substitution turns "we construct a model" into
            "we concept being measured (construct) a model".

This module fixes both without any third-party dependency:

  1. INFLECTION  Each glossary term expands into a family of surface forms
     (plurals, irregular plurals, spelling variants, derived forms). When a
     plural form matches, the plain-English expansion is pluralized to match,
     so the sentence still reads grammatically.

  2. SENSE       Ambiguous terms carry two cue vectors - one profiling the
     academic sense, one profiling the everyday sense. The words surrounding
     an occurrence become a vector too, and the term is only expanded when
     the context sits closer to the academic sense by cosine similarity.
     This is the classic vector space model: shared vocabulary between a
     context window and a sense profile, normalized by vector length.

  3. GRAMMAR     A term declared as a noun is skipped where the local grammar
     says it is being used as a verb ("we construct", "to construct"), which
     cosine similarity alone will not always catch.

Terms with no declared senses are expanded unconditionally, exactly as
before - the gate only constrains words that are genuinely ambiguous.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple

# How much text on each side of a match forms the context window. Roughly
# 20 words each way - wide enough to pick up the topic, narrow enough that
# an unrelated later paragraph does not vote.
CONTEXT_CHARS = 130

_WORD_RE = re.compile(r"[a-z][a-z'’-]*")


def tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens"""
    return _WORD_RE.findall(text.lower())


def count_tokens(text: str) -> Dict[str, int]:
    """Build a term-frequency vector from raw text"""
    counts: Dict[str, int] = {}
    for token in tokenize(text):
        counts[token] = counts.get(token, 0) + 1
    return counts


# ----------------------------------------------------------------------
# Vector space sense profiles
# ----------------------------------------------------------------------

class SenseProfile:
    """A weighted bag of cue words describing one sense of a term.

    Cosine similarity against a context window answers "how much does this
    context look like this sense?" on a 0..1 scale.
    """

    def __init__(self, cues: Iterable[str]):
        if isinstance(cues, Mapping):
            self.weights = {cue.lower(): float(weight) for cue, weight in cues.items()}
        else:
            self.weights = {cue.lower(): 1.0 for cue in cues}

        self._norm = math.sqrt(sum(w * w for w in self.weights.values())) or 1.0

    def __bool__(self) -> bool:
        return bool(self.weights)

    def cosine(self, counts: Mapping[str, int]) -> float:
        """Cosine similarity between this profile and a context vector"""
        if not counts or not self.weights:
            return 0.0

        dot = sum(weight * counts.get(cue, 0) for cue, weight in self.weights.items())
        if dot == 0:
            return 0.0

        window_norm = math.sqrt(sum(c * c for c in counts.values())) or 1.0
        return dot / (self._norm * window_norm)


# Words that mark the following token as a verb rather than a noun.
VERB_CUES = frozenset({
    'to', 'we', 'they', 'i', 'you', 'he', 'she', 'researchers', 'authors',
    'can', 'could', 'will', 'would', 'shall', 'should', 'must', 'may',
    'might', 'cannot', "can't", 'let', 'helps', 'help', 'and', 'or',
})

# Words that mark the following token as a noun.
NOUN_CUES = frozenset({
    'the', 'a', 'an', 'this', 'that', 'these', 'those', 'each', 'every',
    'its', 'their', 'our', 'his', 'her', 'any', 'no', 'one', 'same',
    'such', 'which', 'whose', 'another', 'both',
})


@dataclass
class TermSense:
    """Disambiguation rules for a term that means different things by context"""

    academic: SenseProfile
    everyday: SenseProfile = field(default_factory=lambda: SenseProfile(()))
    expects: Optional[str] = None       # 'noun' - skip where used as a verb
    strict: bool = False                # with no evidence either way, skip
    min_similarity: float = 0.0         # floor the academic sense must clear

    def decide(self, left: str, right: str) -> Tuple[bool, str]:
        """Should this occurrence be expanded? Returns (verdict, reason)."""
        if self.expects == 'noun':
            preceding = tokenize(left)
            if preceding and preceding[-1] in VERB_CUES and preceding[-1] not in NOUN_CUES:
                return False, f"used as a verb after '{preceding[-1]}'"

        window = count_tokens(left)
        for token, count in count_tokens(right).items():
            window[token] = window.get(token, 0) + count

        academic = self.academic.cosine(window)
        everyday = self.everyday.cosine(window)

        if academic > everyday and academic >= self.min_similarity:
            return True, f"academic sense (similarity {academic:.3f} > {everyday:.3f})"
        if everyday > academic:
            return False, f"everyday sense (similarity {everyday:.3f} > {academic:.3f})"

        # No evidence either way.
        if self.strict:
            return False, "no academic context found"
        return True, "no competing sense found"


def _profile(*cues: str) -> SenseProfile:
    return SenseProfile(cues)


# Terms whose plain meaning collides with their technical meaning. Only these
# are gated; every other glossary term expands unconditionally.
AMBIGUOUS_TERMS: Dict[str, TermSense] = {
    'construct': TermSense(
        academic=_profile('measure', 'measured', 'measurement', 'scale', 'validity',
                          'latent', 'variable', 'variables', 'questionnaire', 'items',
                          'factor', 'theoretical', 'psychological', 'assess', 'assessed',
                          'score', 'scores', 'reliability'),
        everyday=_profile('build', 'building', 'built', 'model', 'framework', 'algorithm',
                          'system', 'pipeline', 'sentence', 'argument', 'dataset',
                          'matrix', 'graph', 'network'),
        expects='noun',
    ),
    'scaffolding': TermSense(
        academic=_profile('learning', 'learner', 'learners', 'student', 'students',
                          'teacher', 'teachers', 'instruction', 'instructional',
                          'support', 'gradually', 'task', 'tasks', 'zone',
                          'development', 'metacognitive', 'classroom'),
        everyday=_profile('construction', 'building', 'site', 'steel', 'workers',
                          'erected', 'pipes', 'scaffold', 'ladder', 'roof', 'bricks'),
    ),
    'differentiation': TermSense(
        academic=_profile('instruction', 'classroom', 'student', 'students', 'teaching',
                          'learners', 'needs', 'curriculum', 'tiered', 'lesson',
                          'teacher', 'ability'),
        everyday=_profile('calculus', 'derivative', 'derivatives', 'equation', 'integral',
                          'cell', 'cells', 'stem', 'tissue', 'embryonic', 'product',
                          'market', 'brand'),
    ),
    'triangulation': TermSense(
        academic=_profile('methods', 'method', 'data', 'sources', 'qualitative',
                          'findings', 'confirm', 'validity', 'interviews', 'observation',
                          'analysis', 'corroborate'),
        everyday=_profile('gps', 'satellite', 'position', 'surveying', 'signal',
                          'coordinates', 'navigation', 'radio', 'antenna', 'towers',
                          'location'),
    ),
    'replication': TermSense(
        academic=_profile('study', 'studies', 'results', 'findings', 'replicate',
                          'independent', 'crisis', 'original', 'sample', 'effect',
                          'preregistered', 'failed', 'science'),
        everyday=_profile('dna', 'rna', 'cell', 'cells', 'virus', 'viral', 'genome',
                          'molecular', 'database', 'server', 'servers', 'bacterial'),
    ),
    'power': TermSense(
        academic=_profile('statistical', 'sample', 'size', 'detect', 'effect', 'analysis',
                          'alpha', 'beta', 'hypothesis', 'test', 'underpowered',
                          'calculation', 'adequate'),
        everyday=_profile('political', 'electricity', 'electrical', 'energy', 'grid',
                          'engine', 'motor', 'plant', 'watts', 'social', 'economic',
                          'institutional', 'purchasing', 'balance'),
        strict=True,
    ),
    'mean': TermSense(
        academic=_profile('standard', 'deviation', 'median', 'average', 'score', 'scores',
                          'sd', 'values', 'sample', 'baseline', 'difference'),
        everyday=_profile('meaning', 'meant', 'means', 'implies', 'suggests', 'says'),
        strict=True,
        expects='noun',
    ),
    'mode': TermSense(
        academic=_profile('median', 'mean', 'frequency', 'distribution', 'values',
                          'common', 'statistic', 'histogram'),
        everyday=_profile('display', 'setting', 'transport', 'travel', 'operation',
                          'default', 'delivery', 'failure', 'switch'),
        strict=True,
    ),
    'range': TermSense(
        academic=_profile('values', 'minimum', 'maximum', 'distribution', 'scores',
                          'variance', 'statistic', 'spread', 'interquartile', 'median'),
        everyday=_profile('mountain', 'shooting', 'driving', 'wide', 'kitchen', 'stove',
                          'products', 'motion', 'free'),
        strict=True,
    ),
    'variance': TermSense(
        academic=_profile('standard', 'deviation', 'mean', 'statistical', 'analysis',
                          'sample', 'explained', 'anova', 'homogeneity', 'residual'),
        everyday=_profile('budget', 'schedule', 'zoning', 'legal', 'permit', 'contract',
                          'planning', 'board'),
        strict=True,
    ),
    'regression': TermSense(
        academic=_profile('linear', 'logistic', 'model', 'coefficient', 'coefficients',
                          'predictor', 'predictors', 'variables', 'analysis', 'multiple',
                          'covariates', 'slope'),
        everyday=_profile('therapy', 'childhood', 'hypnosis', 'tumor', 'disease',
                          'symptom', 'symptoms', 'relapse', 'behaviour'),
        strict=True,
    ),
}


# ----------------------------------------------------------------------
# Morphology
# ----------------------------------------------------------------------

IRREGULAR_PLURALS = {
    'analysis': 'analyses',
    'hypothesis': 'hypotheses',
    'thesis': 'theses',
    'basis': 'bases',
    'criterion': 'criteria',
    'phenomenon': 'phenomena',
    'index': 'indices',
    'matrix': 'matrices',
    'datum': 'data',
}

# Already-plural words that must never be pluralized again.
UNCOUNTABLE_OR_PLURAL = frozenset({
    'people', 'data', 'research', 'evidence', 'information', 'criteria',
    'phenomena', 'analyses', 'men', 'women', 'children', 'things',
})

# Alternate spellings of the same word in the same word class. These are
# substituted like the term itself: "expansion (matched)".
TERM_VARIANTS: Dict[str, Tuple[str, ...]] = {
    'randomized': ('randomised',),
    'randomized controlled trial': ('randomised controlled trial', 'rct'),
    'peer review': ('peer reviewed', 'peer-reviewed'),
    'double-blind': ('double blind',),
    'p-value': ('p value',),
    'meta-analysis': ('meta analysis',),
    'adverse events': ('adverse effects',),
}

# Derived forms in a DIFFERENT word class from the expansion. A glossary
# expansion is a noun phrase, so dropping it in place of a verb or adjective
# breaks the sentence: "Scores things that tend to happen together with
# outcomes". These are annotated instead - "matched (expansion)" - which
# reads correctly wherever the word appears.
TERM_DERIVED: Dict[str, Tuple[str, ...]] = {
    'randomized': ('randomization', 'randomisation'),
    'correlation': ('correlated', 'correlates', 'correlational'),
    'causation': ('causal', 'causally'),
    'replication': ('replicated', 'replicate', 'replicates'),
    'placebo': ('placebo-controlled',),
    'efficacy': ('efficacious',),
    'metacognition': ('metacognitive',),
    'pedagogical': ('pedagogy',),
    'ethnography': ('ethnographic',),
    'scaffolding': ('scaffolded',),
    'operational definition': ('operationalized', 'operationalised'),
    'statistical significance': ('statistically significant',),
    'qualitative research': ('qualitatively',),
    'quantitative research': ('quantitatively',),
}

# Terms whose regular plural would collide with an unrelated common word.
# 'mean' -> 'means' is the motivating case.
NO_AUTO_PLURAL = frozenset({'mean', 'power', 'mode', 'range', 'causation'})


def pluralize_word(word: str) -> str:
    """Pluralize a single English word with the usual spelling rules"""
    lower = word.lower()

    if lower in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[lower]
    if lower in UNCOUNTABLE_OR_PLURAL:
        return lower
    if lower.endswith('is'):
        return lower[:-2] + 'es'
    if lower.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return lower + 'es'
    if len(lower) > 1 and lower.endswith('y') and lower[-2] not in 'aeiou':
        return lower[:-1] + 'ies'
    return lower + 's'


def pluralize_term(term: str) -> str:
    """Pluralize the head word of a possibly multi-word term"""
    words = term.split()
    if not words:
        return term

    words[-1] = pluralize_word(words[-1])
    return ' '.join(words)


def singularize_word(word: str) -> str:
    """Best-effort singular of an English plural"""
    lower = word.lower()

    for singular, plural in IRREGULAR_PLURALS.items():
        if lower == plural:
            return singular

    if lower in UNCOUNTABLE_OR_PLURAL or not lower.endswith('s'):
        return lower
    if lower.endswith(('ss', 'is', 'us')):
        return lower
    if lower.endswith('ies') and len(lower) > 4:
        return lower[:-3] + 'y'
    if lower.endswith(('ches', 'shes', 'xes', 'zes')):
        return lower[:-2]
    return lower[:-1]


# Tokens that end the leading noun phrase of a plain-English expansion.
_EXPANSION_BREAKS = frozenset({
    'about', 'of', 'with', 'that', 'where', 'who', 'whom', 'which', 'in',
    'on', 'for', 'from', 'to', 'by', 'between', 'among', 'when', 'while',
    'because', 'and', 'or', 'is', 'are', 'was', 'were', 'not', 'the', 'a',
    'an', 'this', 'these', 'no',
})

# Expansions opening with one of these are not simple noun phrases, so
# pluralizing them would produce nonsense ("one thing actually causes
# another" must not become "one thing actually causes anothers").
_EXPANSION_SKIP_OPENERS = frozenset({
    'how', 'why', 'what', 'whether', 'when', 'where', 'one', 'a', 'an',
    'the', 'neither', 'not', 'other', 'both', 'each', 'every', 'no',
    'repeating', 'following', 'comparing', 'having', 'studying', 'thinking',
    'providing', 'adapting', 'developing', 'checking', 'using', 'doing',
})


# Pluralizing a head noun leaves any verb in its relative clause disagreeing:
# "study that combines" -> "studies that combines". These put it right.
_VERB_PLURALS = {
    "doesn't": "don't",
    "isn't": "aren't",
    "wasn't": "weren't",
    "hasn't": "haven't",
    'is': 'are',
    'was': 'were',
    'has': 'have',
    'does': 'do',
    'goes': 'go',
}

_RELATIVE_PRONOUNS = frozenset({'that', 'which', 'who'})

# When the relative clause carries its own subject the head noun's number is
# irrelevant: "assumption that there's no real effect" stays as it is.
_CLAUSE_SUBJECTS = frozenset({
    'there', "there's", 'it', "it's", 'they', 'we', 'you', 'i', 'he', 'she',
    'people', 'researchers', 'one', 'this', 'these', 'those',
})


def pluralize_verb(verb: str) -> str:
    """Turn a third-person-singular verb into its plural agreement form"""
    lower = verb.lower()

    if lower in _VERB_PLURALS:
        return _VERB_PLURALS[lower]
    if not lower.endswith('s') or lower.endswith(('ss', 'us')):
        return verb
    if lower.endswith('ies') and len(lower) > 4:
        return lower[:-3] + 'y'
    if lower.endswith(('ches', 'shes', 'xes', 'zes', 'sses')):
        return lower[:-2]
    return lower[:-1]


def pluralize_expansion(expansion: str) -> str:
    """Pluralize the head noun of an expansion, conservatively.

    "educated guess about what would happen" -> "educated guesses about ..."
    "study that combines results"            -> "studies that combine results"

    Anything that does not look like a plain leading noun phrase is returned
    untouched. A slightly stiff phrase is always better than a broken one.
    """
    words = expansion.split()
    if not words:
        return expansion

    first = words[0].strip('(,.').lower()
    if first in _EXPANSION_SKIP_OPENERS or first.endswith('ing'):
        return expansion

    head_index = None
    for index, word in enumerate(words):
        clean = word.strip('(),.').lower()
        if clean in _EXPANSION_BREAKS or clean.endswith('ing'):
            break
        head_index = index

    if head_index is None or head_index > 2:
        return expansion

    head = words[head_index]
    clean_head = head.strip('(),.').lower()

    # Already plural, or a word we must not touch.
    if clean_head in UNCOUNTABLE_OR_PLURAL:
        return expansion
    if clean_head.endswith('s') and not clean_head.endswith(('ss', 'is', 'us')):
        return expansion

    words[head_index] = head.replace(clean_head, pluralize_word(clean_head), 1)

    # Keep the verb of any relative clause in agreement with the new plural.
    verb_index = head_index + 2
    if (verb_index < len(words)
            and words[head_index + 1].lower() in _RELATIVE_PRONOUNS
            and words[verb_index].lower().strip('(),.') not in _CLAUSE_SUBJECTS):
        words[verb_index] = pluralize_verb(words[verb_index])

    return ' '.join(words)


def singularize_expansion(expansion: str) -> str:
    """Singularize the head noun of an expansion stored in the plural.

    "bad side effects" -> "bad side effect", so a singular match does not
    read as "one bad side effects was serious".
    """
    words = expansion.split()
    if not words:
        return expansion

    first = words[0].strip('(,.').lower()
    if first in _EXPANSION_SKIP_OPENERS or first.endswith('ing'):
        return expansion

    head_index = None
    for index, word in enumerate(words):
        clean = word.strip('(),.').lower()
        if clean in _EXPANSION_BREAKS or clean.endswith('ing'):
            break
        head_index = index

    if head_index is None or head_index > 2:
        return expansion

    head = words[head_index]
    clean_head = head.strip('(),.').lower()

    singular = singularize_word(clean_head)
    if singular == clean_head:
        return expansion

    words[head_index] = head.replace(clean_head, singular, 1)
    return ' '.join(words)


def flatten_parentheses(text: str) -> str:
    """Turn 'a (b)' into 'a - b' so a gloss never nests brackets"""
    return re.sub(r'\s*\(([^)]*)\)', r' - \1', text).strip()


# ----------------------------------------------------------------------
# The matcher
# ----------------------------------------------------------------------

@dataclass
class SurfaceForm:
    """One way a glossary term can appear in real text"""

    term: str               # canonical glossary key
    expansion: str          # plain English
    plural: bool = False    # matched form is plural: pluralize the expansion
    annotate: bool = False  # different word class: gloss it, don't replace it
    singular: bool = False  # matched form is singular, expansion is plural

    def render(self, matched: str) -> str:
        """Rewrite one occurrence of this term"""
        if self.annotate:
            # 'correlated (things that tend to happen together)' - the
            # sentence's own grammar is left intact.
            return f"{matched} ({flatten_parentheses(self.expansion)})"

        expansion = self.expansion
        if self.plural:
            expansion = pluralize_expansion(expansion)
        elif self.singular:
            expansion = singularize_expansion(expansion)

        return f"{expansion} ({matched})"


class TermMatcher:
    """Compiled matcher for one glossary (plus statistical shorthand).

    Every occurrence is decided in a single pass over the source text, so an
    expansion can never be re-translated by a later term.
    """

    def __init__(self, glossary: Mapping[str, str],
                 shorthand: Optional[Mapping[str, str]] = None,
                 senses: Optional[Mapping[str, TermSense]] = None,
                 variants: Optional[Mapping[str, Tuple[str, ...]]] = None,
                 derived: Optional[Mapping[str, Tuple[str, ...]]] = None,
                 context_chars: int = CONTEXT_CHARS):
        self.senses = dict(AMBIGUOUS_TERMS if senses is None else senses)
        self.variants = dict(TERM_VARIANTS if variants is None else variants)
        self.derived = dict(TERM_DERIVED if derived is None else derived)
        self.context_chars = context_chars

        self.forms: Dict[str, SurfaceForm] = {}
        self.shorthand: Dict[str, str] = {}

        for term, expansion in glossary.items():
            for surface, is_plural, annotate, is_singular in self._surface_forms(term):
                # Longer glossary terms win: never let 'trial' shadow
                # 'clinical trial' by overwriting an existing entry.
                self.forms.setdefault(
                    surface,
                    SurfaceForm(term, expansion, is_plural, annotate, is_singular),
                )

        for phrase, expansion in (shorthand or {}).items():
            self.shorthand[phrase.lower()] = expansion

        self.pattern = self._compile()

    # -- construction --------------------------------------------------

    def _surface_forms(self, term: str) -> List[SurfaceForm]:
        """Every way this term may be written, with how to render each"""
        key = term.lower()
        forms: List[Tuple[str, bool, bool, bool]] = []

        def add_inflections(base: str, annotate: bool) -> None:
            forms.append((base, False, annotate, False))

            if base in NO_AUTO_PLURAL:
                return

            plural = pluralize_term(base)
            if plural != base:
                forms.append((plural, True, annotate, False))

            # Terms stored in the plural also need their singular.
            singular = self._singularize_term(base)
            if singular and singular != base:
                forms.append((singular, False, annotate, True))

        add_inflections(key, False)

        for variant in self.variants.get(key, ()):
            add_inflections(variant.lower(), False)

        # Derived forms are glossed in place, so they are never inflected -
        # the surrounding sentence already supplies the grammar.
        for derived in self.derived.get(key, ()):
            forms.append((derived.lower(), False, True, False))

        seen: Set[str] = set()
        unique = []
        for surface, is_plural, annotate, is_singular in forms:
            if surface not in seen:
                seen.add(surface)
                unique.append((surface, is_plural, annotate, is_singular))

        return unique

    @staticmethod
    def _singularize_term(term: str) -> Optional[str]:
        words = term.split()
        if not words:
            return None

        head = words[-1]
        if head in UNCOUNTABLE_OR_PLURAL or not head.endswith('s'):
            return None
        if head.endswith(('ss', 'is', 'us')):
            return None

        if head.endswith('ies') and len(head) > 4:
            words[-1] = head[:-3] + 'y'
        elif head.endswith(('ses', 'xes', 'zes', 'ches', 'shes')):
            words[-1] = head[:-2]
        else:
            words[-1] = head[:-1]

        return ' '.join(words)

    def _compile(self) -> Optional[re.Pattern]:
        alternatives: List[Tuple[int, str]] = []

        for surface in self.forms:
            # Spaces in a term may appear as any whitespace, including a
            # line break where a PDF wrapped the phrase.
            body = r'\s+'.join(re.escape(part) for part in surface.split())
            alternatives.append((len(surface), rf'\b{body}\b'))

        for phrase in self.shorthand:
            # 'n =' must also catch 'n=240' and 'n  =  240'.
            body = r'\s*'.join(re.escape(part) for part in phrase.split())
            prefix = r'\b' if phrase[:1].isalnum() else ''
            alternatives.append((len(phrase), rf'{prefix}{body}'))

        if not alternatives:
            return None

        # Longest first, so the most specific term claims the span.
        alternatives.sort(key=lambda item: item[0], reverse=True)
        return re.compile('|'.join(source for _, source in alternatives), re.IGNORECASE)

    # -- matching ------------------------------------------------------

    def lookup(self, matched: str) -> Optional[SurfaceForm]:
        """Find the surface form for matched text, normalizing whitespace"""
        return self.forms.get(' '.join(matched.lower().split()))

    def decide(self, term: str, left: str, right: str) -> Tuple[bool, str]:
        """Whether an occurrence of term in this context should be expanded"""
        sense = self.senses.get(term.lower())
        if sense is None:
            return True, "term is unambiguous"
        return sense.decide(left, right)

    def translate(self, text: str) -> str:
        """Expand every glossary term in text, once, in a single pass"""
        if not self.pattern:
            return text

        def substitute(match) -> str:
            matched = match.group(0)
            normalized = ' '.join(matched.lower().split())

            shorthand = self.shorthand.get(re.sub(r'\s+', ' ', normalized))
            if shorthand is None:
                shorthand = self.shorthand.get(re.sub(r'\s*', '', normalized))
            if shorthand is None:
                # 'n=240' normalizes to 'n=' but the key is 'n ='.
                collapsed = re.sub(r'\s+', '', normalized)
                for phrase, expansion in self.shorthand.items():
                    if re.sub(r'\s+', '', phrase) == collapsed:
                        shorthand = expansion
                        break
            if shorthand is not None:
                return shorthand

            form = self.lookup(matched)
            if form is None:
                return matched

            left = text[max(0, match.start() - self.context_chars):match.start()]
            right = text[match.end():match.end() + self.context_chars]

            expand, _reason = self.decide(form.term, left, right)
            if not expand:
                return matched

            return form.render(matched)

        return self.pattern.sub(substitute, text)
