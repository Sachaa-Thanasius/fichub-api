from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import aiohttp

from . import __version__
from .models import (
    _meta_converter,
    _download_urls_converter,
    Story,
    DownloadUrls
)

if TYPE_CHECKING:
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

    Parameters
    ----------
    session : :class:`aiohttp.ClientSession`, optional
        The asynchronous HTTP session to make requests with. If not passed in, automatically generated. Closing it is
        not handled automatically by the class if done outside an async context manager.
    headers : dict, optional
        The HTTP headers to send with any requests.
    sema_limit : :class:`int`
        The limit on the number of requests that can be made at once asynchronously. If not between 1 and 3, defaults to 2.
    """

    def __init__(
            self,
            *,
            headers: dict | None = None,
            session: aiohttp.ClientSession | None = None,
            sema_limit: int | None = None
    ) -> None:
        self.headers = headers or {"User-Agent": f"FicHub API wrapper/v{__version__}+@Thanos"}
        self.session = session
        self._semaphore = asyncio.Semaphore(value=(sema_limit if (sema_limit and 1 <= sema_limit <= 3) else 2))
        self._sema_limit = sema_limit

        # Use pre-structured converters to convert json responses to models.
        self._dwnld_urls_conv = _download_urls_converter
        self._meta_conv = _meta_converter

    async def __aenter__(self) -> FicHubClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def sema_limit(self) -> int:
        """:class:`int`: The counter limit for the number of simultaneous requests."""

        return self._sema_limit

    @sema_limit.setter
    def sema_limit(self, value: int) -> None:
        if 1 <= value <= 3:
            self._sema_limit = value
            self._semaphore = asyncio.Semaphore(value)
        else:
            raise ValueError("To prevent hitting the FicHub API too much, this limit has to be between 1 and 3 inclusive.")

    async def start_session(self) -> None:
        """Start an HTTP session attached to this instance if necessary."""

        if (not self.session) or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close the HTTP session attached to this instance if necessary."""

        if self.session and (not self.session.closed):
            await self.session.close()

    async def _get(self, endpoint: str, params: dict | None = None) -> Any:
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
        Any
            The JSON data from the API response.

        Raises
        ------
        FicHubException
            If there's a client response error.
        """

        # TODO: Implement caching mechanism.
        await self.start_session()

        async with self._semaphore:
            try:
                url = urljoin(FICHUB_BASE_URL, endpoint)
                async with self.session.get(url, params=params, headers=self.headers) as response:
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
        metadata : :class:`Story`
            The queried story's metadata.
        """

        query = {"q": url}
        payload: StoryMetadataPayload = await self._get("meta", params=query)
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

        query = {"q": url}
        payload: DownloadDataPayload = await self._get("epub", params=query)
        download_urls = self._dwnld_urls_conv.structure(payload["urls"], DownloadUrls)
        return download_urls
