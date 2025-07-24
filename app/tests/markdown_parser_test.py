import pytest

from common.markdown_parser import MarkdownParser
from common.logger import AppLogger


class TestMarkdownParser:

    @classmethod
    def setup_class(cls):
        """Setup logging for all tests in this class."""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
        cls.logger.info("Starting MarkdownParser tests")

    def test_init(self, markdown_parser):
        assert markdown_parser is not None
        assert hasattr(markdown_parser, 'logger')

    def test_parse_empty_string(self, markdown_parser):
        result = markdown_parser.parse("")
        assert result == ""

    def test_parse_whitespace_only(self, markdown_parser):
        result = markdown_parser.parse("   \n\t  \n  ")
        assert result == ""

    def test_parse_plain_text(self, markdown_parser):
        content = "This is plain text without any markdown."
        result = markdown_parser.parse(content)
        assert result == content

    def test_parse_headers(self, markdown_parser):
        content = """# Header 1
## Header 2
### Header 3
#### Header 4
##### Header 5
###### Header 6"""

        result = markdown_parser.parse(content)
        expected = """Header 1
Header 2
Header 3
Header 4
Header 5
Header 6"""
        assert result == expected

    def test_parse_bold_text(self, markdown_parser):
        content = "This is **bold** text and this is also **very bold**."
        result = markdown_parser.parse(content)
        assert result == "This is bold text and this is also very bold."

    def test_parse_italic_text(self, markdown_parser):
        content = "This is _italic_ text and this is also _very italic_."
        result = markdown_parser.parse(content)
        assert result == "This is italic text and this is also very italic."

    def test_parse_bold_italic_mixed(self, markdown_parser):
        content = "Text with **bold** and _italic_ and **_both_**."
        result = markdown_parser.parse(content)
        assert result == "Text with bold and italic and both."

    def test_parse_links(self, markdown_parser):
        content = "Visit [Google](https://google.com) or [GitHub](https://github.com)."
        result = markdown_parser.parse(content)
        assert result == "Visit Google or GitHub."

    def test_parse_inline_code(self, markdown_parser):
        content = "Use `print()` function or `len()` to get length."
        result = markdown_parser.parse(content)
        assert result == "Use  function or  to get length."

    def test_parse_code_blocks(self, markdown_parser):
        content = """Some text before.

```python
def hello():
    print("Hello World")
    return True
```

Some text after."""

        result = markdown_parser.parse(content)
        expected = """Some text before.

Some text after."""
        assert result == expected

    def test_parse_complex_markdown(self, markdown_parser, sample_markdown_content):
        result = markdown_parser.parse(sample_markdown_content)

        # Should not contain markdown syntax
        assert "#" not in result
        assert "**" not in result
        assert "_" not in result
        assert "`" not in result
        assert "```" not in result
        assert "[" not in result
        assert "]" not in result
        assert "(" not in result
        assert ")" not in result

        # Should contain the actual text content
        assert "Test Document" in result
        assert "test document" in result
        assert "italic text" in result
        assert "Features" in result
        assert "Feature 1" in result
        assert "Link to example" in result
        assert "regular text" in result

    def test_parse_whitespace_cleanup(self, markdown_parser):
        content = """# Header


Multiple blank lines should be reduced.



Another paragraph."""

        result = markdown_parser.parse(content)

        # Should not have excessive newlines
        assert "\n\n\n" not in result
        lines = result.split('\n')
        assert len([line for line in lines if line.strip()]) == 3  # 3 non-empty lines

    def test_parse_mixed_formatting(self, markdown_parser):
        content = """## **Bold Header**

This has _italic_ and **bold** and `code`.

[Link text](https://example.com) here.

```
code block
multiple lines
```

Final paragraph."""

        result = markdown_parser.parse(content)

        assert "Bold Header" in result
        assert "italic" in result
        assert "bold" in result
        assert "Link text" in result
        assert "Final paragraph" in result

        # Should not contain markdown syntax
        assert "##" not in result
        assert "**" not in result
        assert "_" not in result
        assert "`" not in result
        assert "[" not in result
        assert "```" not in result

    def test_extract_price_history_table_empty_content(self, markdown_parser):
        result = markdown_parser.extract_price_history_table("")
        assert result is None

    def test_extract_price_history_table_no_table(self, markdown_parser):
        content = "This content has no price history table."
        result = markdown_parser.extract_price_history_table(content)
        assert result is None

    def test_extract_price_history_table_valid_table(self, markdown_parser):
        content = """
Some other content here.

| Date | Holofoil |
| --- | --- |
| 4/20 to 4/22 | $1,451.66 | $0.00 |
| 4/23 to 4/25 | $1,451.66 | $0.00 |
| 4/26 to 4/28 | $1,451.66 | $0.00 |

More content after table.
"""
        result = markdown_parser.extract_price_history_table(content)
        assert result is not None
        assert "| Date | Holofoil |" in result
        assert "| 4/20 to 4/22 | $1,451.66 | $0.00 |" in result
        assert "| 4/23 to 4/25 | $1,451.66 | $0.00 |" in result
        assert "| 4/26 to 4/28 | $1,451.66 | $0.00 |" in result
        assert "Some other content" not in result
        assert "More content after" not in result

    def test_extract_price_history_table_case_insensitive(self, markdown_parser):
        content = """
| date | holofoil |
| --- | --- |
| 4/20 to 4/22 | $1,451.66 | $0.00 |
"""
        result = markdown_parser.extract_price_history_table(content)
        assert result is not None
        assert "date" in result.lower()
        assert "holofoil" in result.lower()

    def test_extract_price_history_table_with_extra_spaces(self, markdown_parser):
        content = """
|   Date   |   Holofoil   |
|   ---    |    ---       |
|  4/20 to 4/22  |  $1,451.66  |  $0.00  |
"""
        result = markdown_parser.extract_price_history_table(content)
        assert result is not None
        assert "Date" in result
        assert "Holofoil" in result
        assert "4/20 to 4/22" in result

    def test_extract_price_history_table_too_small(self, markdown_parser):
        content = """
| Date | Holofoil |
| --- | --- |
"""
        result = markdown_parser.extract_price_history_table(content)
        assert result is None  # Too small - no data rows

    def test_parse_price_history_data_empty_content(self, markdown_parser):
        result = markdown_parser.parse_price_history_data("")
        assert result == []

    def test_parse_price_history_data_no_table(self, markdown_parser):
        content = "No table here"
        result = markdown_parser.parse_price_history_data(content)
        assert result == []

    def test_parse_price_history_data_valid_table(self, markdown_parser, default_timestamp):
        content = """
| Date | Holofoil |
| --- | --- |
| 4/20 to 4/22 | $1,451.66 | $0.00 |
| 4/23 to 4/25 | $1,451.66 | $0.00 |
| 4/26 to 4/28 | $1,451.66 | $0.00 |
"""
        result = markdown_parser.parse_price_history_data(content)
        assert len(result) == 3

        # Check first row (v2.0 format)
        assert result[0]['period_start_date'] == '2025-04-20'
        assert result[0]['period_end_date'] == '2025-04-22'
        assert result[0]['holofoil_price'] == 1451.66
        assert result[0]['volume'] == 0
        assert 'timestamp' in result[0]

        # Check second row (v2.0 format)
        assert result[1]['period_start_date'] == '2025-04-23'
        assert result[1]['period_end_date'] == '2025-04-25'
        assert result[1]['holofoil_price'] == 1451.66
        assert result[1]['volume'] == 0

        # Check third row (v2.0 format)
        assert result[2]['period_start_date'] == '2025-04-26'
        assert result[2]['period_end_date'] == '2025-04-28'
        assert result[2]['holofoil_price'] == 1451.66
        assert result[2]['volume'] == 0

    def test_parse_price_history_data_with_missing_cells(self, markdown_parser, default_timestamp):
        content = """
| Date | Holofoil |
| --- | --- |
| 4/20 to 4/22 | $1,451.66 |
| 4/23 to 4/25 |  |
"""
        result = markdown_parser.parse_price_history_data(content)
        assert len(result) == 2

        # First row with missing price (v2.0 format)
        assert result[0]['period_start_date'] == '2025-04-20'
        assert result[0]['period_end_date'] == '2025-04-22'
        assert result[0]['holofoil_price'] == 1451.66
        assert result[0]['volume'] == 0

        # Second row with missing holofoil (v2.0 format)
        assert result[1]['period_start_date'] == '2025-04-23'
        assert result[1]['period_end_date'] == '2025-04-25'
        assert result[1]['holofoil_price'] == 0.0
        assert result[1]['volume'] == 0