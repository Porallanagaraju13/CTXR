import re
from typing import List, Tuple


class PromptOptimizer:
    """
    Rule-Based Prompt Compression Engine.
    Reduces token footprint of raw user prompts by applying layered
    text transformations while preserving semantic meaning and intent.
    """

    # ── Filler words and weak openers that add no value ──────────────
    FILLER_PATTERNS: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"\b[Pp]lease\s+", re.IGNORECASE), ""),
        (re.compile(r"\b[Cc]ould you\s+(?:please\s+)?", re.IGNORECASE), ""),
        (re.compile(r"\b[Cc]an you\s+(?:please\s+)?", re.IGNORECASE), ""),
        (re.compile(r"\b[Ww]ould you\s+(?:please\s+)?(?:be able to\s+)?", re.IGNORECASE), ""),
        (re.compile(r"\bI would like you to\s+", re.IGNORECASE), ""),
        (re.compile(r"\bI want you to\s+", re.IGNORECASE), ""),
        (re.compile(r"\bI need you to\s+", re.IGNORECASE), ""),
        (re.compile(r"\bI was wondering if you could\s+", re.IGNORECASE), ""),
        (re.compile(r"\b[Kk]indly\s+", re.IGNORECASE), ""),
        (re.compile(r"\bjust\s+", re.IGNORECASE), ""),
        (re.compile(r"\bbasically\s+", re.IGNORECASE), ""),
        (re.compile(r"\bactually\s+", re.IGNORECASE), ""),
        (re.compile(r"\bliterally\s+", re.IGNORECASE), ""),
        (re.compile(r"\bsimply\s+", re.IGNORECASE), ""),
        (re.compile(r"\bobviously\s+", re.IGNORECASE), ""),
        (re.compile(r"\bof course\s+", re.IGNORECASE), ""),
    ]

    # ── Redundant phrasings → concise replacements ───────────────────
    REDUNDANT_PHRASES: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"\b[Ii]n order to\b"), "To"),
        (re.compile(r"\b[Dd]ue to the fact that\b"), "Because"),
        (re.compile(r"\b[Ff]or the purpose of\b"), "To"),
        (re.compile(r"\b[Ii]n the event that\b"), "If"),
        (re.compile(r"\b[Aa]t this point in time\b"), "Now"),
        (re.compile(r"\b[Aa]t the present time\b"), "Now"),
        (re.compile(r"\b[Ii]n the near future\b"), "Soon"),
        (re.compile(r"\b[Oo]n a daily basis\b"), "Daily"),
        (re.compile(r"\b[Ii]t is important to note that\b"), "Note:"),
        (re.compile(r"\b[Ii]t should be noted that\b"), "Note:"),
        (re.compile(r"\b[Ii]t is worth mentioning that\b"), "Note:"),
        (re.compile(r"\b[Aa]s a matter of fact\b"), "In fact"),
        (re.compile(r"\b[Ff]or the sake of\b"), "For"),
        (re.compile(r"\b[Ww]ith regard to\b"), "Regarding"),
        (re.compile(r"\b[Ww]ith respect to\b"), "Regarding"),
        (re.compile(r"\b[Ii]n regard to\b"), "Regarding"),
        (re.compile(r"\b[Ii]n terms of\b"), "Regarding"),
        (re.compile(r"\b[Aa]s well as\b"), "and"),
        (re.compile(r"\b[Ee]ach and every\b"), "Every"),
        (re.compile(r"\b[Ff]irst and foremost\b"), "First"),
        (re.compile(r"\b[Aa]ll of the\b"), "All"),
        (re.compile(r"\b[Aa] large number of\b"), "Many"),
        (re.compile(r"\b[Aa] majority of\b"), "Most"),
        (re.compile(r"\b[Hh]as the ability to\b"), "Can"),
        (re.compile(r"\b[Ii]s able to\b"), "Can"),
        (re.compile(r"\b[Mm]ake sure that\b"), "Ensure"),
        (re.compile(r"\b[Mm]ake sure to\b"), "Ensure"),
        (re.compile(r"\b[Tt]ake into consideration\b"), "Consider"),
        (re.compile(r"\b[Tt]ake into account\b"), "Consider"),
    ]

    # ── Verbose qualifiers → tighter alternatives ────────────────────
    VERBOSE_QUALIFIERS: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"\bvery\s+important\b", re.IGNORECASE), "important"),
        (re.compile(r"\bextremely\s+important\b", re.IGNORECASE), "critical"),
        (re.compile(r"\bextremely\s+critical\b", re.IGNORECASE), "critical"),
        (re.compile(r"\bvery\s+much\b", re.IGNORECASE), "greatly"),
        (re.compile(r"\bvery\s+good\b", re.IGNORECASE), "excellent"),
        (re.compile(r"\bvery\s+bad\b", re.IGNORECASE), "poor"),
        (re.compile(r"\bvery\s+big\b", re.IGNORECASE), "large"),
        (re.compile(r"\bvery\s+small\b", re.IGNORECASE), "tiny"),
        (re.compile(r"\bvery\s+fast\b", re.IGNORECASE), "rapid"),
        (re.compile(r"\bvery\s+easy\b", re.IGNORECASE), "simple"),
        (re.compile(r"\bvery\s+hard\b", re.IGNORECASE), "difficult"),
        (re.compile(r"\bquite\s+a\s+few\b", re.IGNORECASE), "several"),
        (re.compile(r"\ba\s+lot\s+of\b", re.IGNORECASE), "many"),
        (re.compile(r"\bthe\s+vast\s+majority\s+of\b", re.IGNORECASE), "most"),
    ]

    # ── Passive-voice simplification hints ───────────────────────────
    PASSIVE_PATTERNS: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"\b[Ii]t is recommended that\b"), "Recommend:"),
        (re.compile(r"\b[Ii]t is suggested that\b"), "Suggest:"),
        (re.compile(r"\b[Ii]t is required that\b"), "Require:"),
        (re.compile(r"\b[Ii]t is necessary to\b"), "Must"),
        (re.compile(r"\b[Ii]t is essential to\b"), "Must"),
        (re.compile(r"\b[Ii]t is advisable to\b"), "Should"),
        (re.compile(r"\b[Tt]here is a need to\b"), "Need to"),
        (re.compile(r"\b[Tt]here are several\b"), "Several"),
        (re.compile(r"\b[Tt]here are many\b"), "Many"),
        (re.compile(r"\b[Tt]here is no need to\b"), "Do not"),
    ]

    @classmethod
    def strip_filler_words(cls, text: str) -> str:
        """Removes filler words and weak opener phrases."""
        result = text
        for pattern, replacement in cls.FILLER_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    @classmethod
    def compress_redundant_phrases(cls, text: str) -> str:
        """Replaces verbose multi-word phrases with concise equivalents."""
        result = text
        for pattern, replacement in cls.REDUNDANT_PHRASES:
            result = pattern.sub(replacement, result)
        return result

    @classmethod
    def strip_verbose_qualifiers(cls, text: str) -> str:
        """Compresses verbose qualifiers into single-word alternatives."""
        result = text
        for pattern, replacement in cls.VERBOSE_QUALIFIERS:
            result = pattern.sub(replacement, result)
        return result

    @classmethod
    def simplify_passive_voice(cls, text: str) -> str:
        """Converts common passive constructions to direct phrasing."""
        result = text
        for pattern, replacement in cls.PASSIVE_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapses excessive whitespace and blank lines."""
        if not text:
            return ""
        # Collapse multiple spaces/tabs into single space
        result = re.sub(r"[ \t]+", " ", text)
        # Collapse 3+ consecutive newlines into 2
        result = re.sub(r"\n{3,}", "\n\n", result)
        # Strip trailing whitespace per line
        result = "\n".join(line.rstrip() for line in result.split("\n"))
        return result.strip()

    @staticmethod
    def deduplicate_instructions(text: str) -> str:
        """
        Removes duplicate lines/sentences that appear more than once.
        Preserves the first occurrence and drops subsequent repeats.
        """
        if not text:
            return ""

        lines = text.split("\n")
        seen = set()
        unique_lines = []

        for line in lines:
            stripped = line.strip()
            # Allow empty lines to pass through (structural)
            if not stripped:
                unique_lines.append(line)
                continue

            # Normalize for comparison (lowercase, collapse whitespace)
            normalized = re.sub(r"\s+", " ", stripped).lower()

            # Skip very short lines from dedup (headers, bullets, etc.)
            if len(normalized) < 15:
                unique_lines.append(line)
                continue

            if normalized not in seen:
                seen.add(normalized)
                unique_lines.append(line)

        return "\n".join(unique_lines)

    @staticmethod
    def convert_to_structured_markdown(text: str) -> str:
        """
        Detects implicit structure in flat text and converts it to markdown.
        - Lines ending with ':' followed by content become ## headers
        - Lines starting with '- ', '* ', or numbered patterns stay as lists
        - Code-like blocks get fenced
        """
        if not text:
            return ""

        lines = text.split("\n")
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip already-formatted markdown headings
            if stripped.startswith("#"):
                result_lines.append(line)
                i += 1
                continue

            # Detect section-like labels: "Section Name:" at the start of a line
            # followed by content on the next line(s)
            colon_match = re.match(
                r"^([A-Z][A-Za-z0-9 /&,]{2,50}):\s*$", stripped
            )
            if colon_match:
                heading_text = colon_match.group(1).strip()
                result_lines.append(f"## {heading_text}")
                i += 1
                continue

            # Detect numbered instructions like "1. Do something" or "1) Do something"
            numbered_match = re.match(r"^(\d+)[.)]\s+(.+)$", stripped)
            if numbered_match:
                result_lines.append(f"{numbered_match.group(1)}. {numbered_match.group(2)}")
                i += 1
                continue

            # Detect dash/star bullet points — keep as-is
            if re.match(r"^[-*+]\s+", stripped):
                result_lines.append(line)
                i += 1
                continue

            # Detect inline code-like content (lines starting with common code markers)
            if stripped.startswith("```"):
                result_lines.append(line)
                i += 1
                continue

            # Default: keep the line as-is
            result_lines.append(line)
            i += 1

        return "\n".join(result_lines)

    @classmethod
    def optimize(cls, prompt: str) -> Tuple[str, List[str]]:
        """
        Runs the full rule-based optimization pipeline on the input prompt.
        Returns (optimized_text, list_of_techniques_applied).
        """
        if not prompt or not prompt.strip():
            return ("", [])

        techniques_applied = []
        result = prompt

        # Stage 1: Filler word removal
        after_filler = cls.strip_filler_words(result)
        if after_filler != result:
            techniques_applied.append("Filler word removal")
            result = after_filler

        # Stage 2: Redundant phrase compression
        after_redundant = cls.compress_redundant_phrases(result)
        if after_redundant != result:
            techniques_applied.append("Redundant phrase compression")
            result = after_redundant

        # Stage 3: Verbose qualifier stripping
        after_qualifiers = cls.strip_verbose_qualifiers(result)
        if after_qualifiers != result:
            techniques_applied.append("Verbose qualifier stripping")
            result = after_qualifiers

        # Stage 4: Passive voice simplification
        after_passive = cls.simplify_passive_voice(result)
        if after_passive != result:
            techniques_applied.append("Passive voice simplification")
            result = after_passive

        # Stage 5: Instruction deduplication
        after_dedup = cls.deduplicate_instructions(result)
        if after_dedup != result:
            techniques_applied.append("Instruction deduplication")
            result = after_dedup

        # Stage 6: Markdown structuring
        after_markdown = cls.convert_to_structured_markdown(result)
        if after_markdown != result:
            techniques_applied.append("Markdown structuring")
            result = after_markdown

        # Stage 7: Whitespace normalization (always run last)
        after_whitespace = cls.normalize_whitespace(result)
        if after_whitespace != result:
            techniques_applied.append("Whitespace normalization")
            result = after_whitespace

        # Capitalize the first character of the result if it starts lowercase
        # (can happen after filler stripping removes the opener)
        if result and result[0].islower():
            result = result[0].upper() + result[1:]

        return (result, techniques_applied)
