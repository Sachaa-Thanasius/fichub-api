from __future__ import annotations

import asyncio
from urllib.parse import urljoin

import aiohttp

from .models import (
    _meta_converter,
    _download_urls_converter,
    Story,
    DownloadUrls
)
from .types import (
    DownloadData as DownloadDataPayload,
    StoryMetadata as StoryMetadataPayload,
)


__all__ = ("FICHUB_BASE_URL", "FicHubException", "FicHubClient")


FICHUB_BASE_URL = "https://fichub.net/api/v0/"


class FicHubException(Exception):
    """The base exception for the FicHub API."""

    pass


class FicHubClient:
    """A small async wrapper for accessing FicHub's fanfiction API.

    TODO: Implement cache. Reference: https://realpython.com/lru-cache-python/

    Parameters
    ----------
    session : :class:`aiohttp.ClientSession`, optional
        The asynchronous HTTP session to make requests with. If not passed in, automatically generated. Closing it is
        not handled automatically by the class.
    headers : dict, optional
        The HTTP headers to send with any requests.
    sema_limit : :class:`int`, default=5
        The limit on the number of requests that can be made at once asynchronously. Defaults to 5.
    """

    def __init__(
            self,
            *,
            headers: dict | None = None,
            session: aiohttp.ClientSession | None = None,
            sema_limit: int | None = None
    ) -> None:
        self._headers = headers or {"User-Agent": f"FicHub API wrapper/v0.0.1+@Thanos"}
        self._session = session
        self._semaphore = asyncio.Semaphore(value=(sema_limit if (sema_limit is not None and sema_limit >= 1) else 5))

        # Use pre-structured converters to convert json responses to models.
        self._dwnld_urls_conv = _download_urls_converter
        self._meta_conv = _meta_converter

    async def __aenter__(self) -> FicHubClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start_session(self) -> None:
        """Start an HTTP session attached to this instance if necessary."""

        if (not self._session) or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close the HTTP session attached to this instance if necessary."""

        if self._session and (not self._session.closed):
            await self._session.close()

        self._session = None

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Gets fanfiction data from the FicHub API.

        This restricts the number of simultaneous requests.

        Parameters
        ----------
        endpoint : :class:`str`
            The path parameters for the endpoint.
        params : dict, optional
            The query parameters to request from the endpoint.

        Returns
        -------
        :class:`StoryMetadata`
            The JSON data from the API response.

        Raises
        ------
        FicHubException
            If there's a client response error.
        """

        await self.start_session()

        async with self._semaphore:
            try:
                url = urljoin(FICHUB_BASE_URL, endpoint)
                async with self._session.get(url, params=params, headers=self._headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data

            except aiohttp.ClientResponseError as exc:
                raise FicHubException(f"HTTP {exc.status}: {exc.message}")

    async def get_story_metadata(self, url: str) -> Story:
        """Gets a specific story's metadata.

        Parameters
        ----------
        url : :class:`str`
            The story URL to look up.

        Returns
        -------
        metadata : :class:`FFNMetadata`
            The metadata of the queried fanfic.
        """

        payload: StoryMetadataPayload = await self._get("meta", params={"q": url})
        metadata = self._meta_conv.structure(payload, Story)
        return metadata

    async def get_download_urls(self, url: str) -> DownloadUrls:
        """Gets all the download urls for a fanfic in various formats, including epub, html, mobi, and pdf.

        Parameters
        ----------
        url : :class:`str`
            The fanfiction url being queried.

        Returns
        -------
        download_urls : :class:`DownloadUrls`
            An object containing all download urls returned by the API.
        """

        payload: DownloadDataPayload = await self._get("epub", params={"q": url})
        download_urls = self._dwnld_urls_conv.structure(payload["urls"], DownloadUrls)
        return download_urls
