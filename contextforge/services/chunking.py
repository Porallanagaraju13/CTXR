import re
from typing import List
from contextforge.core.models import ExtractedEntity

class SemanticChunker:
    """
    Semantic Document Chunking Engine.
    Splits GFM Markdown based on heading structures and section transitions,
    preventing mid-sentence breaks and preserving contextual relevance for vector search.
    """

    @staticmethod
    def chunk_markdown(text: str, max_chunk_words: int = 350) -> List[str]:
        """
        Splits Markdown text into highly coherent semantic packages.
        Maintains title headers with children blocks and splits on #/##/### headings.
        Prefixes each chunk with its parent heading breadcrumbs context (e.g. # [Context: A > B]).
        """
        if not text:
            return []

        # Split on markdown headings at the start of a line
        sections = re.split(r"(^#+\s+.*$)", text, flags=re.MULTILINE)
        
        chunks = []
        current_chunk = []
        current_words = 0
        heading_stack = {}
        
        def get_breadcrumb() -> str:
            sorted_levels = sorted(heading_stack.keys())
            path = [heading_stack[lvl] for lvl in sorted_levels if heading_stack[lvl]]
            if path:
                return f"# [Context: {' > '.join(path)}]\n"
            return ""
            
        def add_chunk(content_list: List[str]):
            if not content_list:
                return
            clean_list = [c.strip() for c in content_list if c.strip()]
            if not clean_list:
                return
            content = "\n\n".join(clean_list)
            breadcrumb = get_breadcrumb()
            if breadcrumb and not content.startswith("# [Context:"):
                chunks.append(f"{breadcrumb}{content}")
            else:
                chunks.append(content)

        for section in sections:
            section_strip = section.strip()
            if not section_strip:
                continue
                
            is_heading = bool(re.match(r"^#+\s+", section_strip))
            
            if is_heading:
                # Flush the current chunk before updating heading hierarchy
                if current_chunk:
                    add_chunk(current_chunk)
                    current_chunk = []
                    current_words = 0
                
                # Update heading stack
                hash_count = len(re.match(r"^#+", section_strip).group(0))
                levels_to_clear = [lvl for lvl in heading_stack if lvl >= hash_count]
                for lvl in levels_to_clear:
                    del heading_stack[lvl]
                heading_stack[hash_count] = section_strip.lstrip("#").strip()
                
                current_chunk.append(section_strip)
                current_words = len(section_strip.split())
                continue
                
            word_count = len(section_strip.split())
            
            # If a single section is extremely large, split it by sentence structures
            if word_count > max_chunk_words:
                # Flush the current chunk first
                if current_chunk:
                    add_chunk(current_chunk)
                    current_chunk = []
                    current_words = 0
                
                # Split large section by sentence structures
                sentences = re.split(r"(?<=[.!?])\s+", section_strip)
                sub_chunk = []
                sub_words = 0
                
                for sentence in sentences:
                    sentence_words = len(sentence.split())
                    if sub_words + sentence_words > max_chunk_words and sub_chunk:
                        add_chunk(sub_chunk)
                        sub_chunk = [sentence]
                        sub_words = sentence_words
                    else:
                        sub_chunk.append(sentence)
                        sub_words += sentence_words
                
                if sub_chunk:
                    add_chunk(sub_chunk)
                    
            # Normal size section: Accumulate
            elif current_words + word_count > max_chunk_words and current_chunk:
                add_chunk(current_chunk)
                current_chunk = [section_strip]
                current_words = word_count
            else:
                current_chunk.append(section_strip)
                current_words += word_count
                
        if current_chunk:
            add_chunk(current_chunk)
            
        return chunks

# Date normalization month mapping
MONTH_MAP = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12"
}

def normalize_date_to_iso(date_str: str) -> str:
    """Standardizes date strings (e.g. '12 June 2026') to ISO-8601 'YYYY-MM-DD'."""
    if not date_str:
        return ""
    date_str_clean = date_str.strip().lower()
    
    # If already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str_clean):
        return date_str_clean
        
    # Match: DD Month YYYY or D Month YYYY
    match_words = re.match(r"^(\d{1,2})\s+([a-z]+)\s+(\d{4})$", date_str_clean)
    if match_words:
        day, month_name, year = match_words.groups()
        month = MONTH_MAP.get(month_name)
        if month:
            day_padded = day.zfill(2)
            return f"{year}-{month}-{day_padded}"
            
    return date_str

class EntityExtractor:
    """
    Core Semantic Entity Extractor.
    Resolves core entities (Organizations, People, Dates, Technologies, Emails, Phones, Locations, and Monetary Values)
    to generate semantic metadata tags for advanced RAG indexing.
    """

    # Global regexes for fast entity matching
    ORG_PATTERN = re.compile(
        r"\b([A-Z][a-zA-Z0-9&]+(?:\s+[A-Z][a-zA-Z0-9]+)*\s+(?:Corp|Corporation|Inc|LLC|Ltd|Group|Holdings|Solutions|Systems|Technologies|University|Institute))\b"
    )
    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}-\d{2}-\d{2})\b"
    )
    TECH_PATTERN = re.compile(
        r"\b(Python|FastAPI|Pydantic|Docker|PostgreSQL|Celery|Redis|Qdrant|TypeScript|Next\.js|Gemini|Claude|ChatGPT|LLM|RAG|SQLAlchemy)\b",
        re.IGNORECASE
    )
    EMAIL_PATTERN = re.compile(
        r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"
    )
    PHONE_PATTERN = re.compile(
        r"(?:^|(?<=\s))(\+?\d{1,3}[-.\s]?\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4})\b"
    )
    LOC_PATTERN = re.compile(
        r"\b(New York|San Francisco|London|Tokyo|Paris|Berlin|California|Texas|Washington|Boston|Seattle|India|Germany|Canada|UK|US|USA|United States|United Kingdom)\b",
        re.IGNORECASE
    )
    MONEY_PATTERN = re.compile(
        r"(\$\d+(?:\.\d+)?(?:\s*(?:million|billion|M|B))?|\b\d+(?:\.\d+)?\s*(?:USD|EUR|GBP|dollars)\b)",
        re.IGNORECASE
    )

    @classmethod
    def extract_entities(cls, text: str) -> List[ExtractedEntity]:
        """
        Parses text and extracts key entities along with their exact local sentence context.
        """
        if not text:
            return []

        entities = []
        
        # Helper to find enclosing sentence context
        def get_context(match_start: int, match_end: int) -> str:
            # Look backwards and forwards to find sentence bounds or fallback size
            start = max(0, text.rfind(".", 0, match_start) + 1)
            end = text.find(".", match_end)
            if end == -1:
                end = min(len(text), match_end + 50)
            else:
                end += 1
            return text[start:end].strip().replace("\n", " ")

        # Match Organizations
        for match in cls.ORG_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                category="Organization",
                context=get_context(match.start(), match.end())
            ))

        # Match Dates (with ISO-8601 normalization)
        for match in cls.DATE_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=normalize_date_to_iso(name),
                category="Date",
                context=get_context(match.start(), match.end())
            ))

        # Match Technologies
        for match in cls.TECH_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                category="Technology",
                context=get_context(match.start(), match.end())
            ))

        # Match Emails
        for match in cls.EMAIL_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                category="Email",
                context=get_context(match.start(), match.end())
            ))

        # Match Phone Numbers
        for match in cls.PHONE_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                category="Phone",
                context=get_context(match.start(), match.end())
            ))

        # Match Locations
        for match in cls.LOC_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                category="Location",
                context=get_context(match.start(), match.end())
            ))

        # Match Monetary Values
        for match in cls.MONEY_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                category="Monetary",
                context=get_context(match.start(), match.end())
            ))

        # De-duplicate entities keeping the first occurrence
        unique_entities = {}
        for ent in entities:
            key = (ent.name.lower(), ent.category)
            if key not in unique_entities:
                unique_entities[key] = ent

        return list(unique_entities.values())
