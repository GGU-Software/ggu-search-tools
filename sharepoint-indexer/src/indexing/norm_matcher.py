"""
Norm Matcher - Match SharePoint documents to norm registry.

Scans SharePoint and finds documents matching the norms in the registry.
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class NormEntry:
    """A norm entry from the registry."""
    id: str
    description: str
    category: str
    priority: str
    status: str = "pending"
    sharepoint_file: Optional[str] = None
    sharepoint_path: Optional[str] = None
    validated: bool = False
    is_withdrawn: bool = False
    version_date: Optional[str] = None
    search_terms: list[str] = field(default_factory=list)


@dataclass
class SharePointMatch:
    """A potential match from SharePoint."""
    filename: str
    path: str
    item_id: str  # Graph API item ID for downloading
    web_url: str  # SharePoint web URL for direct access
    norm_id: str
    norm_key: str  # Normalized key that matched in registry
    version_date: Optional[str]
    is_withdrawn: bool
    score: int  # Higher = better match


@dataclass
class ScanResult:
    """Result of scanning SharePoint for norms."""
    total_norms: int = 0
    found: int = 0
    not_found: int = 0
    withdrawn_only: int = 0
    matches: dict = field(default_factory=dict)  # norm_key -> SharePointMatch


class NormMatcher:
    """Match SharePoint documents to norm registry."""

    # Pattern to extract norm ID from filename
    # Matches: DIN 4017, DIN EN ISO 17892-1, EN 1997-1, ISO 14688-1,
    #          VDI 4640, OENORM B 4417, OENORM EN 1997-1, ASTM D2487
    # Requires:
    #   - Prefix (DIN, EN, ISO, VDI, OENORM, ASTM, or combinations)
    #   - Optional letter-number prefix for OENORM (B, EN) or ASTM (D, E)
    #   - Main number (at least 3 digits to avoid false matches)
    #   - Optional part numbers (-1, -2, etc.)
    #   - Followed by non-digit (to prevent 22476-1 matching 22476-14)
    NORM_PATTERN = re.compile(
        r'(DIN\s+EN\s+ISO|DIN\s+EN|DIN|EN\s+ISO|EN|ISO|VDI|OENORM\s+EN|OENORM\s+B|OENORM|ASTM)\s+'
        r'([A-Z]?\s*\d{3,5})(?:-(\d{1,3}))?(?:-(\d{1,2}))?'
        r'(?=[_\s\.\(\)]|$)',  # Must be followed by separator, not another digit
        re.IGNORECASE
    )

    # Pattern to extract version date (e.g., 2006-02, 2017-08)
    # Must be 4-digit year (19xx or 20xx) followed by 2-digit month
    DATE_PATTERN = re.compile(r'[_\s](\d{4})[-_](\d{2})(?=[_\s\.\(\)]|$)')

    # Pattern to detect withdrawn status
    WITHDRAWN_PATTERNS = [
        re.compile(r'zur[uü]ckgezogen', re.IGNORECASE),
        re.compile(r'withdrawn', re.IGNORECASE),
        re.compile(r'ersetzt\s+durch', re.IGNORECASE),
    ]

    def __init__(self, registry_path: Path):
        """
        Initialize matcher with registry.

        Args:
            registry_path: Path to norms-registry.yaml
        """
        self.registry_path = registry_path
        self.norms: dict[str, NormEntry] = {}
        self.settings: dict = {}
        self._load_registry()

    def _load_registry(self):
        """Load norms from registry file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self.settings = data.get('settings', {})

        for norm_data in data.get('norms', []):
            norm = NormEntry(
                id=norm_data['id'],
                description=norm_data.get('description', ''),
                category=norm_data.get('category', 'other'),
                priority=norm_data.get('priority', 'medium'),
                status=norm_data.get('status', 'pending'),
                sharepoint_file=norm_data.get('sharepoint_file'),
                validated=norm_data.get('validated', False),
                search_terms=norm_data.get('search_terms', []),
            )
            # Normalize ID for matching
            norm_key = self._normalize_norm_id(norm.id)
            self.norms[norm_key] = norm

        logger.info(f"Loaded {len(self.norms)} norms from registry")

    def _normalize_norm_id(self, norm_id: str) -> str:
        """Normalize norm ID for comparison."""
        # Standardize spacing and convert to uppercase
        result = re.sub(r'\s+', ' ', norm_id.upper().strip())
        # Ensure consistent format: "DIN EN ISO" not "DIN  EN  ISO"
        result = result.replace('DIN EN ISO', 'DIN EN ISO')
        result = result.replace('DIN EN', 'DIN EN')
        result = result.replace('EN ISO', 'EN ISO')
        return result

    def _extract_norm_id(self, filename: str) -> Optional[tuple[str, str]]:
        """
        Extract norm ID from filename.

        Returns:
            Tuple of (full_norm_id, base_norm_id) or None
            e.g., ("DIN EN ISO 17892-1", "DIN EN ISO 17892")
        """
        match = self.NORM_PATTERN.search(filename)
        if not match:
            return None

        prefix = match.group(1).upper()
        # Normalize prefix spacing
        prefix = re.sub(r'\s+', ' ', prefix)

        main_number = match.group(2)
        part1 = match.group(3)  # First part number (e.g., -1)
        part2 = match.group(4)  # Second part number (e.g., -1-1)

        # Build full ID
        full_id = f"{prefix} {main_number}"
        base_id = full_id  # Base without part numbers

        if part1:
            full_id += f"-{part1}"
        if part2:
            full_id += f"-{part2}"

        return (full_id, base_id)

    def _extract_version_date(self, filename: str) -> Optional[str]:
        """
        Extract version date from filename (e.g., 2006-02).

        Only matches dates that look like publication dates (year 1990-2030).
        """
        match = self.DATE_PATTERN.search(filename)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            # Validate year is reasonable (1990-2030) and month is valid
            if 1990 <= year <= 2030 and 1 <= month <= 12:
                return f"{match.group(1)}-{match.group(2)}"
        return None

    def _is_withdrawn(self, filename: str) -> bool:
        """Check if document is marked as withdrawn."""
        for pattern in self.WITHDRAWN_PATTERNS:
            if pattern.search(filename):
                return True
        return False

    def _calculate_match_score(self, match: SharePointMatch, is_exact: bool) -> int:
        """
        Calculate match quality score.

        Higher score = better match:
        - +100: Base score
        - +50: Exact norm ID match (not just base)
        - +30: Has version date (more specific)
        - -50: Is withdrawn
        - +20: Is PDF
        """
        score = 100  # Base score for matching

        if is_exact:
            score += 50  # Exact match bonus

        if match.version_date:
            score += 30

        if match.is_withdrawn:
            score -= 50

        if match.filename.lower().endswith('.pdf'):
            score += 20

        return score

    def _find_matching_registry_key(self, full_id: str, base_id: str) -> Optional[tuple[str, bool]]:
        """
        Find which registry key matches the extracted norm ID.

        Returns:
            Tuple of (registry_key, is_exact_match) or None
        """
        full_key = self._normalize_norm_id(full_id)
        base_key = self._normalize_norm_id(base_id)

        # Priority 1: Exact match on full ID (e.g., "DIN 4017-1" matches "DIN 4017-1")
        if full_key in self.norms:
            return (full_key, True)

        # Priority 2: Exact match on base ID (e.g., "DIN 4017-1" matches registry "DIN 4017")
        if base_key in self.norms:
            return (base_key, False)

        # Priority 3: Full ID is a more specific version of registry entry
        # e.g., Document "DIN 18137-1" can match registry "DIN 18137"
        for registry_key in self.norms.keys():
            # Check if full_key starts with registry_key and next char is "-"
            if full_key.startswith(registry_key):
                remainder = full_key[len(registry_key):]
                if remainder == '' or remainder.startswith('-'):
                    return (registry_key, remainder == '')

        return None

    def _match_by_search_terms(self, filename: str) -> Optional[tuple[str, bool]]:
        """
        Try to match a filename using search_terms from registry entries.

        This handles non-standard norms (EAB, EBGEO, EA-Pfähle, etc.)
        that don't follow the DIN/EN/ISO naming pattern.

        Returns:
            Tuple of (registry_key, is_exact_match) or None
        """
        filename_upper = filename.upper()
        for norm_key, norm in self.norms.items():
            if not norm.search_terms:
                continue
            # Require ALL search terms to match (case-insensitive)
            all_match = all(
                term.upper() in filename_upper
                for term in norm.search_terms[:2]  # Use first 2 terms (most specific)
            )
            if all_match:
                return (norm_key, True)
        return None

    def match_document(self, filename: str, path: str, item_id: str = "", web_url: str = "") -> Optional[SharePointMatch]:
        """
        Try to match a document to a norm in the registry.

        Args:
            filename: Document filename
            path: Full SharePoint path
            item_id: Graph API item ID for downloading
            web_url: SharePoint web URL for direct access

        Returns:
            SharePointMatch if document matches a norm, None otherwise
        """
        extracted = self._extract_norm_id(filename)
        match_result = None
        norm_id_for_match = filename  # Fallback display name

        if extracted:
            full_id, base_id = extracted
            norm_id_for_match = full_id
            match_result = self._find_matching_registry_key(full_id, base_id)

        # Fallback: try search_terms for non-standard norms (EAB, EBGEO, etc.)
        if not match_result:
            match_result = self._match_by_search_terms(filename)
            if match_result:
                registry_key, _ = match_result
                norm_id_for_match = self.norms[registry_key].id

        if not match_result:
            return None

        registry_key, is_exact = match_result

        match = SharePointMatch(
            filename=filename,
            path=path,
            item_id=item_id,
            web_url=web_url,
            norm_id=norm_id_for_match,
            norm_key=registry_key,
            version_date=self._extract_version_date(filename),
            is_withdrawn=self._is_withdrawn(filename),
            score=0,
        )
        match.score = self._calculate_match_score(match, is_exact)

        return match

    def process_matches(self, matches: list[SharePointMatch]) -> ScanResult:
        """
        Process all matches and select best document for each norm.

        Args:
            matches: List of all SharePoint matches

        Returns:
            ScanResult with statistics and best matches
        """
        result = ScanResult(total_norms=len(self.norms))

        # Group matches by registry key
        matches_by_norm: dict[str, list[SharePointMatch]] = {}
        for match in matches:
            key = match.norm_key
            if key not in matches_by_norm:
                matches_by_norm[key] = []
            matches_by_norm[key].append(match)

        # Select best match for each norm
        prefer_latest = self.settings.get('prefer_latest', True)
        allow_withdrawn = self.settings.get('allow_withdrawn_fallback', True)

        for norm_key, norm in self.norms.items():
            candidates = matches_by_norm.get(norm_key, [])

            if not candidates:
                result.not_found += 1
                continue

            # Separate active and withdrawn
            active = [m for m in candidates if not m.is_withdrawn]
            withdrawn = [m for m in candidates if m.is_withdrawn]

            # Prefer active documents
            if active:
                # Sort by: score (highest first), then version date (latest first)
                if prefer_latest:
                    active.sort(key=lambda m: (m.score, m.version_date or '0000-00'), reverse=True)
                else:
                    active.sort(key=lambda m: m.score, reverse=True)
                best = active[0]
                result.found += 1
            elif withdrawn and allow_withdrawn:
                # Use withdrawn as fallback
                withdrawn.sort(key=lambda m: (m.score, m.version_date or '0000-00'), reverse=True)
                best = withdrawn[0]
                result.withdrawn_only += 1
            else:
                result.not_found += 1
                continue

            result.matches[norm_key] = best

        return result

    def update_registry(self, result: ScanResult) -> None:
        """
        Update registry file with scan results.

        Args:
            result: ScanResult from process_matches
        """
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Update each norm entry
        for norm_data in data.get('norms', []):
            norm_key = self._normalize_norm_id(norm_data['id'])

            if norm_key in result.matches:
                match = result.matches[norm_key]
                norm_data['status'] = 'withdrawn_only' if match.is_withdrawn else 'found'
                norm_data['sharepoint_file'] = match.filename
                norm_data['sharepoint_path'] = match.path
                norm_data['item_id'] = match.item_id
                norm_data['web_url'] = match.web_url
                norm_data['version_date'] = match.version_date
                norm_data['is_withdrawn'] = match.is_withdrawn
            else:
                norm_data['status'] = 'not_found'
                norm_data['sharepoint_file'] = None
                norm_data['sharepoint_path'] = None
                norm_data['item_id'] = None
                norm_data['web_url'] = None
                norm_data['version_date'] = None
                norm_data['is_withdrawn'] = False

        # Add scan summary
        data['scan_summary'] = {
            'scan_date': datetime.now().isoformat(),
            'total_norms': result.total_norms,
            'found': result.found,
            'withdrawn_only': result.withdrawn_only,
            'not_found': result.not_found,
        }

        with open(self.registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        logger.info(f"Updated registry: {result.found} found, {result.withdrawn_only} withdrawn, {result.not_found} not found")

    def generate_whitelist(self) -> list[str]:
        """
        Generate whitelist of files to index based on registry.

        Returns:
            List of filenames (markdown) to include in indexing
        """
        whitelist = []

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

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
