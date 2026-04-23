"""
SharePoint Graph API Client.

Handles authentication and site/drive discovery.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

import aiohttp

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SharePointClient:
    """
    Client for Microsoft Graph API to access SharePoint.

    Usage:
        client = SharePointClient()
        await client.initialize()
        # Now client.drive_id is available for document queries
    """

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the client.

        Args:
            settings: Configuration settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()

        # Will be set during initialize()
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.site_id: Optional[str] = None
        self.drive_id: Optional[str] = None

        # Session for reuse
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> bool:
        """
        Initialize the client by authenticating and discovering site/drive IDs.

        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            logger.info("Initializing SharePoint client...")

            # Step 1: Get access token
            if not await self._get_access_token():
                logger.error("Failed to get access token")
                return False

            # Step 2: Get site ID
            if not await self._get_site_id():
                logger.error("Failed to get site ID")
                return False

            # Step 3: Get drive ID
            if not await self._get_drive_id():
                logger.error("Failed to get drive ID")
                return False

            logger.info(
                f"SharePoint client initialized: "
                f"site={self.settings.sharepoint_site}, "
                f"drive={self.settings.sharepoint_drive}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize SharePoint client: {e}")
            return False

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def get_auth_headers(self) -> dict:
        """Get authorization headers for Graph API requests."""
        if not self.access_token:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    async def _get_access_token(self) -> bool:
        """
        Get OAuth2 access token using client credentials grant.

        Returns:
            True if token obtained successfully.
        """
        token_url = self.TOKEN_URL_TEMPLATE.format(
            tenant_id=self.settings.sharepoint_tenant_id
        )

        token_data = {
            "client_id": self.settings.sharepoint_client_id,
            "client_secret": self.settings.sharepoint_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        session = await self.get_session()

        async with session.post(token_url, data=token_data) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Token request failed: {response.status} - {error_text}")
                return False

            data = await response.json()
            self.access_token = data["access_token"]

            # Token typically expires in 1 hour, refresh 5 minutes early
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Access token obtained successfully")
            return True

    async def _get_site_id(self) -> bool:
        """
        Get SharePoint site ID from site path.

        Returns:
            True if site ID obtained successfully.
        """
        # Graph API format for subsite: /sites/{hostname}:/{site-path}
        site_url = (
            f"{self.GRAPH_API_BASE}/sites/"
            f"{self.settings.sharepoint_host}:/{self.settings.sharepoint_site}"
        )

        session = await self.get_session()
        headers = self.get_auth_headers()

        async with session.get(site_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Site request failed: {response.status} - {error_text}")
                return False

            data = await response.json()
            self.site_id = data["id"]
            site_name = data.get("displayName", "Unknown")

            logger.info(f"Found site: {site_name} (ID: {self.site_id[:20]}...)")
            return True

    async def _get_drive_id(self) -> bool:
        """
        Get drive ID for the configured document library.

        Returns:
            True if drive ID found successfully.
        """
        drives_url = f"{self.GRAPH_API_BASE}/sites/{self.site_id}/drives"

        session = await self.get_session()
        headers = self.get_auth_headers()

        async with session.get(drives_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Drives request failed: {response.status} - {error_text}")
                return False

            data = await response.json()
            drives = data.get("value", [])

            # Find the configured drive by name
            for drive in drives:
                if drive["name"] == self.settings.sharepoint_drive:
                    self.drive_id = drive["id"]
                    logger.info(f"Found drive: {drive['name']} (ID: {self.drive_id[:20]}...)")
                    return True

            # Drive not found - list available drives for debugging
            available = [d["name"] for d in drives]
            logger.error(
                f"Drive '{self.settings.sharepoint_drive}' not found. "
                f"Available drives: {available}"
            )
            return False

    async def ensure_valid_token(self) -> bool:
        """
        Ensure the access token is still valid, refresh if needed.

        Returns:
            True if token is valid (or was refreshed successfully).
        """
        if not self.access_token or not self.token_expires_at:
            return await self._get_access_token()

        if datetime.now() >= self.token_expires_at:
            logger.info("Access token expired, refreshing...")
            return await self._get_access_token()

        return True

    async def resolve_by_path(
        self, drive_path: str, filename: str
    ) -> Optional[dict]:
        """
        Resolve a file by path+filename to a Graph API DriveItem.

        Useful when the scanner's fuzzy matching can't reach a document
        (e.g. DGGT books in non-standard subfolders) but we know exactly
        where it lives in SharePoint.

        Args:
            drive_path: Path within the drive, e.g. "Bibliothek/E/EAP"
            filename: Exact filename, e.g. "EA-Pfahle, 2. Auflage 2012.pdf"

        Returns:
            Dict with {id, webUrl, size, name} on hit, None on 404 or error.
        """
        from urllib.parse import quote

        await self.ensure_valid_token()

        # Normalize: strip "Bibliothek/" prefix if the drive root already is
        # the Bibliothek folder — the caller often stores the full visible
        # path including the drive name, but Graph expects drive-root-relative.
        # We keep the prefix because the configured drive name is "GGU"
        # (not "Bibliothek"), so "Bibliothek/..." IS drive-root-relative.
        full = f"{drive_path}/{filename}".strip("/")
        encoded = quote(full, safe="/")
        url = f"{self.GRAPH_API_BASE}/drives/{self.drive_id}/root:/{encoded}"

        session = await self.get_session()
        headers = self.get_auth_headers()

        async with session.get(url, headers=headers) as response:
            if response.status == 404:
                logger.info(f"Path not found in SharePoint: {full}")
                return None
            if response.status != 200:
                error_text = await response.text()
                logger.error(
                    f"Path resolution failed for {full}: {response.status} - {error_text}"
                )
                return None

            data = await response.json()
            return {
                "id": data.get("id"),
                "webUrl": data.get("webUrl"),
                "size": data.get("size"),
                "name": data.get("name"),
            }

    async def download_file(self, item_id: str) -> Optional[bytes]:
        """
        Download file content by item ID.

        Args:
            item_id: Graph API item ID.

        Returns:
            File content as bytes, or None if download failed.
        """
        await self.ensure_valid_token()

        download_url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}/items/{item_id}/content"
        )

        session = await self.get_session()
        headers = self.get_auth_headers()

        async with session.get(download_url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Download failed for {item_id}: {response.status} - {error_text}")
                return None

            content = await response.read()
            logger.debug(f"Downloaded {len(content)} bytes for item {item_id}")
            return content
