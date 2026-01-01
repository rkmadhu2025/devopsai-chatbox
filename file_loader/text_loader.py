"""
Text Loader - Extract and process text files.
Supports various text formats including plain text, markdown, code, and structured data.
"""
import os
import re
import json
import logging
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

# Try to import optional libraries
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import csv
    CSV_AVAILABLE = True
except ImportError:
    CSV_AVAILABLE = False


class TextLoader:
    """
    Text file processor supporting multiple formats.
    Handles encoding detection, format parsing, and content analysis.
    """

    # Code file extensions and their languages
    CODE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.sql': 'sql',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.ps1': 'powershell',
        '.bat': 'batch',
        '.cmd': 'batch',
    }

    # Config/data file extensions
    CONFIG_EXTENSIONS = {
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.conf': 'config',
        '.cfg': 'config',
        '.env': 'env',
        '.properties': 'properties',
    }

    def __init__(self, default_encoding: str = 'utf-8'):
        """
        Initialize text loader.

        Args:
            default_encoding: Default encoding to try first
        """
        self.default_encoding = default_encoding

    def extract_text(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract text from file content.

        Args:
            file_content: File content as bytes
            filename: Original filename (for format detection)

        Returns:
            Tuple of (text_content, metadata)
        """
        metadata = {
            "encoding": None,
            "format": None,
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "language": None
        }

        try:
            # Detect encoding
            text, encoding = self._decode_content(file_content)
            metadata["encoding"] = encoding

            if text is None:
                return None, {"error": "Could not decode file content"}

            # Determine format from extension
            ext = os.path.splitext(filename.lower())[1]
            format_type = self._get_format_type(ext)
            metadata["format"] = format_type

            # Process based on format
            if format_type == "code":
                metadata["language"] = self.CODE_EXTENSIONS.get(ext, "unknown")
                processed_text = self._process_code(text, metadata["language"])
            elif format_type == "json":
                processed_text, extra_meta = self._process_json(text)
                metadata.update(extra_meta)
            elif format_type == "yaml":
                processed_text, extra_meta = self._process_yaml(text)
                metadata.update(extra_meta)
            elif format_type == "csv":
                processed_text, extra_meta = self._process_csv(text)
                metadata.update(extra_meta)
            elif format_type == "markdown":
                processed_text, extra_meta = self._process_markdown(text)
                metadata.update(extra_meta)
            else:
                processed_text = text

            # Calculate statistics
            metadata["line_count"] = len(processed_text.splitlines())
            metadata["word_count"] = len(processed_text.split())
            metadata["char_count"] = len(processed_text)

            return processed_text, metadata

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return None, {"error": str(e)}

    def _decode_content(self, content: bytes) -> Tuple[Optional[str], str]:
        """
        Decode bytes to string with encoding detection.

        Returns:
            Tuple of (decoded_text, encoding_used)
        """
        # Try default encoding first
        try:
            return content.decode(self.default_encoding), self.default_encoding
        except UnicodeDecodeError:
            pass

        # Use chardet if available
        if CHARDET_AVAILABLE:
            detected = chardet.detect(content)
            if detected and detected.get('encoding'):
                try:
                    encoding = detected['encoding']
                    return content.decode(encoding), encoding
                except (UnicodeDecodeError, LookupError):
                    pass

        # Try common encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii', 'utf-16']
        for encoding in encodings:
            try:
                return content.decode(encoding), encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Last resort: decode with error replacement
        return content.decode('utf-8', errors='replace'), 'utf-8 (with replacements)'

    def _get_format_type(self, extension: str) -> str:
        """Determine format type from extension."""
        if extension in self.CODE_EXTENSIONS:
            return "code"
        elif extension in ['.json']:
            return "json"
        elif extension in ['.yaml', '.yml']:
            return "yaml"
        elif extension in ['.csv']:
            return "csv"
        elif extension in ['.md', '.markdown']:
            return "markdown"
        elif extension in ['.html', '.htm']:
            return "html"
        elif extension in ['.xml']:
            return "xml"
        elif extension in self.CONFIG_EXTENSIONS:
            return "config"
        else:
            return "text"

    def _process_code(self, text: str, language: str) -> str:
        """Process code files with optional analysis."""
        # Add code block markers for context
        lines = text.splitlines()

        # Remove excessive blank lines
        processed_lines = []
        blank_count = 0
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    processed_lines.append(line)
            else:
                blank_count = 0
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def _process_json(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Process JSON files."""
        metadata = {"valid_json": False}
        try:
            data = json.loads(text)
            metadata["valid_json"] = True

            # Analyze structure
            if isinstance(data, dict):
                metadata["json_type"] = "object"
                metadata["json_keys"] = list(data.keys())[:20]  # First 20 keys
            elif isinstance(data, list):
                metadata["json_type"] = "array"
                metadata["json_length"] = len(data)

            # Pretty print for readability
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            return formatted, metadata
        except json.JSONDecodeError as e:
            metadata["json_error"] = str(e)
            return text, metadata

    def _process_yaml(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Process YAML files."""
        metadata = {"valid_yaml": False}
        if not YAML_AVAILABLE:
            return text, metadata

        try:
            data = yaml.safe_load(text)
            metadata["valid_yaml"] = True

            if isinstance(data, dict):
                metadata["yaml_type"] = "mapping"
                metadata["yaml_keys"] = list(data.keys())[:20]
            elif isinstance(data, list):
                metadata["yaml_type"] = "sequence"
                metadata["yaml_length"] = len(data)

            return text, metadata
        except yaml.YAMLError as e:
            metadata["yaml_error"] = str(e)
            return text, metadata

    def _process_csv(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Process CSV files."""
        import io
        metadata = {"valid_csv": False}

        try:
            # Detect delimiter
            sample = text[:4096]
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ','

            # Read CSV
            reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            rows = list(reader)

            if rows:
                metadata["valid_csv"] = True
                metadata["csv_rows"] = len(rows)
                metadata["csv_columns"] = len(rows[0]) if rows else 0
                metadata["csv_headers"] = rows[0] if rows else []
                metadata["csv_delimiter"] = delimiter

            # Return as formatted table
            return text, metadata
        except Exception as e:
            metadata["csv_error"] = str(e)
            return text, metadata

    def _process_markdown(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Process Markdown files."""
        metadata = {"format_type": "markdown"}

        # Extract headings
        headings = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
        if headings:
            metadata["headings"] = [
                {"level": len(h[0]), "text": h[1]}
                for h in headings[:20]
            ]

        # Count code blocks
        code_blocks = re.findall(r'```(\w*)', text)
        if code_blocks:
            metadata["code_blocks"] = len(code_blocks)
            metadata["code_languages"] = list(set(code_blocks))

        # Count links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        metadata["link_count"] = len(links)

        return text, metadata

    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown-formatted text.

        Returns:
            List of {"language": ..., "code": ...} dictionaries
        """
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)

        return [
            {"language": lang or "text", "code": code.strip()}
            for lang, code in matches
        ]

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[str]:
        """
        Split text into overlapping chunks for processing.

        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk
            overlap: Number of characters to overlap

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at paragraph or sentence
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind('. ', start, end),
                        text.rfind('.\n', start, end),
                        text.rfind('! ', start, end),
                        text.rfind('? ', start, end)
                    )
                    if sentence_break > start + chunk_size // 2:
                        end = sentence_break + 2

            chunks.append(text[start:end].strip())
            start = end - overlap

        return chunks

    def clean_text(self, text: str) -> str:
        """Remove excessive whitespace and normalize text."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive blank lines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.splitlines()]

        return '\n'.join(lines)

    def is_binary(self, content: bytes) -> bool:
        """Check if content appears to be binary."""
        # Check for null bytes
        if b'\x00' in content[:8192]:
            return True

        # Check ratio of printable characters
        try:
            text = content[:8192].decode('utf-8', errors='ignore')
            printable = sum(c.isprintable() or c.isspace() for c in text)
            return printable / len(text) < 0.7 if text else True
        except Exception:
            return True
