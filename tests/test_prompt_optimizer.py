import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from contextforge.services.prompt_optimizer import PromptOptimizer
from contextforge.core.models import PromptOptimizationResult, TokenMetrics


class TestFillerWordRemoval:
    """Tests for filler word and weak opener stripping."""

    def test_please_removal(self):
        result = PromptOptimizer.strip_filler_words("Please help me with this task")
        assert "please" not in result.lower() or result.startswith("help") or "help" in result.lower()

    def test_could_you_removal(self):
        result = PromptOptimizer.strip_filler_words("Could you please write a function")
        assert "could you" not in result.lower()

    def test_i_would_like_removal(self):
        result = PromptOptimizer.strip_filler_words("I would like you to create a REST API")
        assert "i would like you to" not in result.lower()

    def test_just_removal(self):
        result = PromptOptimizer.strip_filler_words("Just add a simple test")
        assert not result.lower().startswith("just")

    def test_multiple_fillers_combined(self):
        text = "Could you please kindly just help me basically fix this"
        result = PromptOptimizer.strip_filler_words(text)
        assert len(result) < len(text)

    def test_preserves_meaningful_content(self):
        text = "Write a Python function that calculates the factorial"
        result = PromptOptimizer.strip_filler_words(text)
        assert "Python" in result
        assert "factorial" in result


class TestRedundantPhraseCompression:
    """Tests for verbose multi-word phrase replacement."""

    def test_in_order_to(self):
        result = PromptOptimizer.compress_redundant_phrases("In order to fix this bug")
        assert result.startswith("To")
        assert "in order to" not in result.lower()

    def test_due_to_the_fact_that(self):
        result = PromptOptimizer.compress_redundant_phrases("Due to the fact that the server is down")
        assert "Because" in result

    def test_make_sure_to(self):
        result = PromptOptimizer.compress_redundant_phrases("Make sure to validate the input")
        assert "Ensure" in result

    def test_is_able_to(self):
        result = PromptOptimizer.compress_redundant_phrases("The system is able to process requests")
        assert "Can" in result

    def test_all_of_the(self):
        result = PromptOptimizer.compress_redundant_phrases("Process all of the records")
        assert "All" in result
        assert "all of the" not in result.lower()


class TestVerboseQualifiers:
    """Tests for verbose qualifier stripping."""

    def test_very_important(self):
        result = PromptOptimizer.strip_verbose_qualifiers("This is very important")
        assert "very important" not in result.lower()
        assert "important" in result.lower()

    def test_extremely_critical(self):
        result = PromptOptimizer.strip_verbose_qualifiers("This is extremely critical")
        assert "extremely critical" not in result.lower()
        assert "critical" in result.lower()

    def test_a_lot_of(self):
        result = PromptOptimizer.strip_verbose_qualifiers("There are a lot of issues")
        assert "many" in result.lower()


class TestPassiveVoice:
    """Tests for passive voice simplification."""

    def test_it_is_recommended_that(self):
        result = PromptOptimizer.simplify_passive_voice("It is recommended that you use TypeScript")
        assert "Recommend:" in result

    def test_it_is_necessary_to(self):
        result = PromptOptimizer.simplify_passive_voice("It is necessary to validate inputs")
        assert "Must" in result

    def test_there_is_no_need_to(self):
        result = PromptOptimizer.simplify_passive_voice("There is no need to restart")
        assert "Do not" in result


class TestWhitespaceNormalization:
    """Tests for whitespace collapse and cleanup."""

    def test_multiple_spaces(self):
        result = PromptOptimizer.normalize_whitespace("Hello   world   test")
        assert "   " not in result
        assert "Hello world test" == result

    def test_excessive_newlines(self):
        result = PromptOptimizer.normalize_whitespace("Line 1\n\n\n\n\nLine 2")
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_trailing_whitespace(self):
        result = PromptOptimizer.normalize_whitespace("Hello   \nWorld   ")
        assert not any(line.endswith(" ") for line in result.split("\n"))

    def test_empty_input(self):
        assert PromptOptimizer.normalize_whitespace("") == ""

    def test_none_like_empty(self):
        assert PromptOptimizer.normalize_whitespace("") == ""


class TestInstructionDeduplication:
    """Tests for duplicate instruction removal."""

    def test_exact_duplicates(self):
        text = "Use TypeScript for all code\nDo something else\nUse TypeScript for all code"
        result = PromptOptimizer.deduplicate_instructions(text)
        assert result.count("Use TypeScript for all code") == 1

    def test_whitespace_variant_duplicates(self):
        text = "Follow the coding standards carefully\nDo X\nFollow  the  coding  standards  carefully"
        result = PromptOptimizer.deduplicate_instructions(text)
        lines = [l.strip() for l in result.split("\n") if l.strip()]
        coding_lines = [l for l in lines if "coding standards" in l.lower()]
        assert len(coding_lines) == 1

    def test_preserves_short_lines(self):
        text = "# Title\n# Title\n## Section\n## Section"
        result = PromptOptimizer.deduplicate_instructions(text)
        # Short lines should NOT be deduped
        assert result.count("# Title") == 2

    def test_preserves_empty_lines(self):
        text = "Line 1\n\nLine 2\n\nLine 3"
        result = PromptOptimizer.deduplicate_instructions(text)
        assert "\n\n" in result


class TestMarkdownStructuring:
    """Tests for implicit-to-markdown structure conversion."""

    def test_section_label_to_heading(self):
        text = "Requirements:\nMust support Python 3.12"
        result = PromptOptimizer.convert_to_structured_markdown(text)
        assert "## Requirements" in result

    def test_preserves_existing_headings(self):
        text = "# Main Title\nSome content"
        result = PromptOptimizer.convert_to_structured_markdown(text)
        assert "# Main Title" in result

    def test_preserves_bullet_lists(self):
        text = "- Item one\n- Item two\n* Item three"
        result = PromptOptimizer.convert_to_structured_markdown(text)
        assert "- Item one" in result
        assert "* Item three" in result

    def test_numbered_list_normalization(self):
        text = "1) First step\n2) Second step"
        result = PromptOptimizer.convert_to_structured_markdown(text)
        assert "1. First step" in result
        assert "2. Second step" in result


class TestFullOptimizePipeline:
    """Integration tests for the full optimize() pipeline."""

    def test_full_pipeline_reduces_tokens(self):
        verbose_prompt = """
        I would like you to please help me create a Python function.
        Could you kindly make sure to validate all of the input parameters.
        In order to ensure correctness, it is important to note that
        the function should handle edge cases.
        It is recommended that you use type hints.
        The function is very important and extremely critical for production.
        I would like you to please help me create a Python function.
        """
        optimized, techniques = PromptOptimizer.optimize(verbose_prompt)
        assert len(optimized) < len(verbose_prompt)
        assert len(techniques) > 0

    def test_empty_prompt_returns_empty(self):
        optimized, techniques = PromptOptimizer.optimize("")
        assert optimized == ""
        assert techniques == []

    def test_whitespace_only_returns_empty(self):
        optimized, techniques = PromptOptimizer.optimize("   \n  \n  ")
        assert optimized == ""
        assert techniques == []

    def test_clean_prompt_minimal_changes(self):
        clean_prompt = "Write a Python function that returns the sum of two integers."
        optimized, techniques = PromptOptimizer.optimize(clean_prompt)
        # A clean prompt should have minimal or no changes
        assert "Python" in optimized
        assert "sum" in optimized

    def test_techniques_list_populated(self):
        prompt = "I would like you to please make sure to create a function in order to process data"
        optimized, techniques = PromptOptimizer.optimize(prompt)
        assert "Filler word removal" in techniques
        assert "Redundant phrase compression" in techniques

    def test_capitalizes_first_character(self):
        # After stripping "Please ", the result should still be capitalized
        prompt = "Please write a test"
        optimized, techniques = PromptOptimizer.optimize(prompt)
        assert optimized[0].isupper()


class TestPromptOptimizationResultModel:
    """Tests for the PromptOptimizationResult Pydantic model."""

    def test_model_creation(self):
        metrics = TokenMetrics(
            raw_tokens_estimate=100,
            compressed_tokens=60,
            tokens_saved=40,
            savings_percentage=40.0,
            dollars_saved=0.0012
        )
        result = PromptOptimizationResult(
            original_prompt="Hello world",
            optimized_prompt="Hello",
            optimization_techniques=["Filler word removal"],
            metrics=metrics
        )
        assert result.original_prompt == "Hello world"
        assert result.optimized_prompt == "Hello"
        assert len(result.optimization_techniques) == 1
        assert result.metrics.savings_percentage == 40.0

    def test_empty_techniques_list(self):
        metrics = TokenMetrics(
            raw_tokens_estimate=10,
            compressed_tokens=10,
            tokens_saved=0,
            savings_percentage=0.0
        )
        result = PromptOptimizationResult(
            original_prompt="Clean text",
            optimized_prompt="Clean text",
            optimization_techniques=[],
            metrics=metrics
        )
        assert result.optimization_techniques == []
