"""Indexing filter based on configuration."""

import fnmatch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

import yaml


@dataclass
class FilterConfig:
    """Configuration for document filtering."""
    mode: str = "whitelist"  # "whitelist", "patterns", or "registry"
    whitelist: list[str] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=lambda: ["*.md"])
    exclude_patterns: list[str] = field(default_factory=list)
    registry_path: Optional[Path] = None

    @classmethod
    def from_yaml(cls, path: Path) -> "FilterConfig":
        """Load configuration from YAML file."""
        if not path.exists():
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        patterns = data.get('patterns', {})

        # Handle registry mode - load whitelist from norms registry
        mode = data.get('mode', 'whitelist')
        whitelist = data.get('whitelist', [])
        registry_path = None

        if mode == 'registry':
            # Load whitelist from norms-registry.yaml
            registry_path = path.parent / 'norms-registry.yaml'
            if registry_path.exists():
                whitelist = cls._load_registry_whitelist(registry_path)

        return cls(
            mode=mode,
            whitelist=whitelist,
            include_patterns=patterns.get('include', ['*.md']),
            exclude_patterns=patterns.get('exclude', []),
            registry_path=registry_path,
        )

    @staticmethod
    def _load_registry_whitelist(registry_path: Path) -> list[str]:
        """Load whitelist from norms registry."""
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        whitelist = []
        for norm_data in data.get('norms', []):
            status = norm_data.get('status', 'pending')
            if status in ('found', 'withdrawn_only'):
                filename = norm_data.get('sharepoint_file')
                if filename:
                    # Convert PDF filename to MD
                    if filename.lower().endswith('.pdf'):
                        filename = filename[:-4] + '.md'
                    whitelist.append(filename)

        return whitelist


class IndexingFilter:
    """Filter documents based on configuration rules."""

    def __init__(self, config: Optional[FilterConfig] = None, config_path: Optional[Path] = None):
        """
        Initialize filter.

        Args:
            config: FilterConfig instance
            config_path: Path to YAML config file (alternative to config)
        """
        if config:
            self.config = config
        elif config_path:
            self.config = FilterConfig.from_yaml(config_path)
        else:
            self.config = FilterConfig()

    def should_index(self, filename: str) -> bool:
        """
        Check if a file should be indexed.

        Args:
            filename: The filename to check (not full path)

        Returns:
            True if the file should be indexed
        """
        if self.config.mode in ("whitelist", "registry"):
            return self._check_whitelist(filename)
        else:
            return self._check_patterns(filename)

    def _check_whitelist(self, filename: str) -> bool:
        """Check if filename is in whitelist."""
        # Normalize for comparison (handle encoding variations)
        normalized = self._normalize(filename)
        for entry in self.config.whitelist:
            if self._normalize(entry) == normalized:
                return True
        return False

    def _check_patterns(self, filename: str) -> bool:
        """Check if filename matches include patterns and not exclude patterns."""
        # Check excludes first
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return False

        # Check includes
        for pattern in self.config.include_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def _normalize(self, s: str) -> str:
        """Normalize string for comparison."""
        # Handle common encoding variations
        return s.lower().replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss')

    def filter_documents(self, documents: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Filter a list of documents.

        Args:
            documents: List of document dicts with 'filename' key

        Returns:
            Tuple of (included, excluded) document lists
        """
        included = []
        excluded = []

        for doc in documents:
            filename = doc.get('filename', '')
            if self.should_index(filename):
                included.append(doc)
            else:
                excluded.append(doc)

        return included, excluded

    def get_status(self) -> dict:
        """Get filter configuration status."""
        return {
            "mode": self.config.mode,
            "whitelist_count": len(self.config.whitelist) if self.config.mode == "whitelist" else None,
            "include_patterns": self.config.include_patterns if self.config.mode == "patterns" else None,
            "exclude_patterns": self.config.exclude_patterns if self.config.mode == "patterns" else None,
        }
