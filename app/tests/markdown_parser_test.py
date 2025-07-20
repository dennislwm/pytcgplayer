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