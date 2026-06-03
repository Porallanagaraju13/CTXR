import re

class TokenCompressor:
    """
    Intelligent Token Compression Engine.
    Processes normalized GFM Markdown to strip boilerplate text, duplicate lines,
    OCR margin artifacts, and layout bloat while retaining headers and semantic structure.
    """

    # Globally compile common boilerplate regex patterns for high-performance scanning
    BOILERPLATE_PATTERN = re.compile(
        r"(page\s+\d+\s+of\s+\d+|confidential|copyright\s+©\s+\d{4}|all\s+rights\s+reserved|\d{1,2}/\d{1,2}/\d{2,4}|\b\d+\s+of\s+\d+\b)",
        re.IGNORECASE
    )

    @classmethod
    def strip_metadata_bloat(cls, markdown_text: str) -> str:
        """
        Strips common headers, footers, boilerplate copyright statements,
        and continuous repetitive layouts.
        Also dynamically detects and prunes recurring page headers/footers across pages.
        """
        if not markdown_text:
            return ""

        # Step 1: Detect dynamic recurring headers/footers across pages
        # Split document into pages by horizontal rules
        pages_raw = re.split(r'\n+---\n+', markdown_text)
        dynamic_boilerplate = set()
        
        if len(pages_raw) >= 3:
            header_candidates = {}
            footer_candidates = {}
            
            for page in pages_raw:
                lines = [l.strip() for l in page.split('\n') if l.strip()]
                # Collect top 2 non-empty lines as potential headers
                for i in range(min(2, len(lines))):
                    line_norm = re.sub(r"\s+", " ", lines[i]).lower()
                    # Skip common formatting elements like markdown headings or tables
                    if line_norm and not line_norm.startswith("#") and not line_norm.startswith("|"):
                        header_candidates[line_norm] = header_candidates.get(line_norm, 0) + 1
                # Collect bottom 2 non-empty lines as potential footers
                for i in range(min(2, len(lines))):
                    idx = len(lines) - 1 - i
                    if idx >= 0:
                        line_norm = re.sub(r"\s+", " ", lines[idx]).lower()
                        if line_norm and not line_norm.startswith("#") and not line_norm.startswith("|"):
                            footer_candidates[line_norm] = footer_candidates.get(line_norm, 0) + 1
            
            threshold = len(pages_raw) * 0.50
            for line_norm, count in header_candidates.items():
                if count >= threshold:
                    dynamic_boilerplate.add(line_norm)
            for line_norm, count in footer_candidates.items():
                if count >= threshold:
                    dynamic_boilerplate.add(line_norm)

        # Step 2: Strip metadata and boilerplate lines
        lines = markdown_text.split("\n")
        seen_paragraphs = set()
        clean_lines = []

        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                clean_lines.append("")
                continue

            # Drop boilerplate lines matching static page headers/footers regex
            if cls.BOILERPLATE_PATTERN.search(line_strip):
                continue
                
            # Drop boilerplate matching dynamic recurring headers/footers
            line_norm = re.sub(r"\s+", " ", line_strip).lower()
            if line_norm in dynamic_boilerplate:
                continue

            # OCR/Parser artifact deduplication: Deduplicate contiguous long paragraphs
            if len(line_strip) > 50:
                # Normalize line for deduplication check to catch slight whitespace differences
                normalized_line = re.sub(r"\s+", "", line_strip).lower()
                if normalized_line in seen_paragraphs:
                    continue
                seen_paragraphs.add(normalized_line)

            clean_lines.append(line)

        # Merge results and standardise double spaces
        result = "\n".join(clean_lines)
        
        # Deduplicate multiple consecutive empty lines (keep max of 2 newlines)
        result = re.sub(r"\n{3,}", "\n\n", result)
        
        return result.strip()

    @staticmethod
    def compress_syntax(markdown_text: str) -> str:
        """
        Reduces token footprint by cleaning up extra tabs, horizontal spacing,
        and redundant layout columns, maintaining formatting constraints.
        """
        if not markdown_text:
            return ""

        lines = markdown_text.split("\n")
        compressed_lines = []
        
        for line in lines:
            # 1. Normalize Headings: e.g., "#  Heading  A" -> "# Heading A"
            match_heading = re.match(r"^(\s*)(#+)(\s+)", line)
            if match_heading:
                hashes = match_heading.group(2)
                content = line[match_heading.end():]
                compressed_content = re.sub(r"[ \t]+", " ", content).strip()
                compressed_lines.append(f"{hashes} {compressed_content}")
                continue

            # 2. Normalize List Items (nested or standard): e.g., "  -  Item  A" -> "  - Item A"
            match_list = re.match(r"^(\s*)([-*+]|[0-9]+\.)(\s+)", line)
            if match_list:
                indent = match_list.group(1)
                bullet = match_list.group(2)
                content = line[match_list.end():]
                compressed_content = re.sub(r"[ \t]+", " ", content).strip()
                compressed_lines.append(f"{indent}{bullet} {compressed_content}")
                continue

            # 3. Standard paragraphs: compress multiple spaces into a single space
            compressed_line = re.sub(r"[ \t]+", " ", line).strip()
            compressed_lines.append(compressed_line)
                
        return "\n".join(compressed_lines).strip()
