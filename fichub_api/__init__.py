from __future__ import annotations

import asyncio
from datetime import datetime
from importlib.metadata import version as im_version
from typing import TYPE_CHECKING, Any, TypedDict
from urllib.parse import urljoin

import aiohttp
import msgspec


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self
else:
    Self = Any


__all__ = ("FICHUB_BASE_URL", "FicHubException", "DownloadUrls", "Author", "Story", "Client")

_DECODER = msgspec.json.Decoder()
FICHUB_BASE_URL = "https://fichub.net/api/v0"


class FicHubException(Exception):
    """The base exception for the FicHub API."""


class ExtendedMetadataFFN(TypedDict, total=False):
    category: str
    chapters: str
    characters: str
    crossover: bool
    fandom_ids: list[str]
    fandom_stubs: list[str]
    favorites: str
    follows: str
    genres: str
    id: str
    language: str
    published: str
    rated: str
    raw_fandom: str
    reviews: str
    updated: str
    words: str


class ExtendedMetadataAO3(TypedDict, total=False):
    category: list[str]
    category_hrefs: list[str]
    character: list[str]
    character_hrefs: list[str]
    fandom: list[str]
    fandom_hrefs: list[str]
    freeform: list[str]
    freeform_hrefs: list[str]
    language: str
    rating: list[str]
    rating_hrefs: list[str]
    relationship: list[str]
    relationship_hrefs: list[str]
    stats: dict[str, str]
    warning: list[str]
    warning_hrefs: list[str]


class StoryMetadata(TypedDict):
    author: str
    authorId: int
    authorLocalId: str
    authorUrl: str
    chapters: int
    created: str
    description: str
    extraMeta: str | None
    id: str
    rawExtendedMeta: ExtendedMetadataAO3 | ExtendedMetadataFFN | None
    source: str
    sourceId: int
    status: str
    title: str
    updated: str
    words: int


class DownloadData(TypedDict):
    epub_url: str
    err: int
    fixits: list[Any]
    hashes: dict[str, str]
    html_url: str
    info: str
    meta: StoryMetadata
    mobi_url: str
    notes: list[str]
    pdf_url: str
    q: str
    slug: str
    urlId: str
    urls: dict[str, str]


class DownloadUrls(msgspec.Struct):
    """A collection of download links for a story retrieved from FicHub.

    Attributes
    ----------
    epub: :class:`str`
        A download link for an epub file.
    html: :class:`str`
        A download link for an html file.
    mobi: :class:`str`
        A download link for a mobi file.
    pdf: :class:`str`
        A download link for a pdf file.

    Notes
    -----
    These links are generated within FicHub's cache and thus expire after some time.
    """

    epub: str
    html: str
    mobi: str
    pdf: str


class Author(msgspec.Struct):
    """The basic metadata of an author.

    Attributes
    ----------
    id: :class:`int`
        An arbitrary FicHub author id.
    local_id: :class:`str`
        The id of the author on a particular website.
    name: :class:`str`
        The name of the author.
    url: :class:`str`
        The url of the author's profile on a particular website.
    """

    id: int
    local_id: str
    name: str
    url: str


class Story(msgspec.Struct):
    """The basic metadata of a work retrieved from FicHub.

    Attributes
    ----------
    author: :class:`Author`
        The author's information. Some of it is website-specific.
    title: :class:`str`
        The story title.
    description: :class:`str`
        The description or summary.
    url: :class:`str`
        The source url.
    chapters: :class:`int`
        The number of chapters.
    created: :class:`datetime`
        The date and time when the story was published.
    updated: :class:`datetime`
        The date and time when the story was last updated.
    status: :class:`str`
        The completion status. Can be either "ongoing" or "complete".
    words: :class:`int`
        The number of words in the story.
    language: :class:`str`
        The language the story is written in.
    rating: :class:`str`, default="No Rating"
        The maturity rating of the story.
    fandoms: list[:class:`str`]
        The fandom(s) this story occupies.
    characters: list[:class:`str`]
        The declared cast of characters.
    stats: dict[:class:`str`, :class:`int`]
        The story metrics, such as hits on Ao3 or favorites on FFN. Differs between sites, so they must be accessed by
        name manually.
    more_meta: dict[:class:`str`, Any]
        Extra metadata, such as href endpoints from AO3. must be accessed by name manually.
    """

    author: Author
    title: str
    description: str
    url: str
    chapters: int
    created: datetime
    updated: datetime
    status: str
    words: int
    language: str = "English"
    rating: str = "No Rating"
    fandoms: list[str] = msgspec.field(default_factory=list)
    characters: list[str] = msgspec.field(default_factory=list)
    stats: dict[str, int] = msgspec.field(default_factory=dict)
    more_meta: dict[str, Any] = msgspec.field(default_factory=dict)


class StoryDownload(msgspec.Struct):
    meta: Story | None
    urls: DownloadUrls


def _camel_to_snake_case(string: str) -> str:
    """Converts a string from camel case to snake case.

    References
    ----------
    Source of code: https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#comment133686723_44969381
    """

    return "".join(
        char
        if not char.isupper()
        else ("" if i and (substr := string[i - 1] + (next_char or "")) == substr.upper() else "_") + char.lower()
        for i, (char, next_char) in enumerate(zip(string, [*string[1:], None]))
    ).lstrip("_")


def shape_data(data: dict[str, Any]) -> dict[str, Any]:
    # TODO: See if this can be optimized.
    by_suffix: dict[str, Any] = {}

    # Collect author info.
    for key in data:
        if "author" in key:
            suffix = (key.split("author"))[1]
            by_suffix.setdefault("author", {})[_camel_to_snake_case(suffix) if suffix else "name"] = data[key]

    # Fix Ao3 links for authors.
    if "archiveofourown.org" in data["source"]:
        by_suffix["author"]["url"] = urljoin("https://www.archiveofourown.org", by_suffix["author"]["url"])

    # Adjust other metadata.
    if more_meta := data["rawExtendedMeta"]:
        if "fanfiction.net" in data["source"]:
            story_stats = {
                key: int(more_meta.pop(key, "0").replace(",", "")) for key in ("favorites", "follows", "reviews")
            }
            rating = more_meta.pop("rated")
            if len(fandoms := more_meta.pop("raw_fandom").split(" + ", 1)) > 1:
                fandoms[-1] = fandoms[-1].removesuffix(" Crossover")
            characters = [
                char
                for char in more_meta.pop("characters").replace("[", ", ").replace("]", ", ").split(", ")
                if char.strip()
            ]
        elif "archiveofourown.org" in data["source"]:
            story_stats = {
                key: int(more_meta["stats"].pop(key, "0").replace(",", ""))
                for key in ("bookmarks", "comments", "hits", "kudos")
            }
            rating = more_meta.pop("rating")[0]
            fandoms = more_meta.pop("fandom")
            characters = more_meta.pop("character")
        else:
            story_stats = {}
            rating, fandoms, characters = "No Rating", [], []

        by_suffix.update(
            {
                "language": more_meta.pop("language", "English"),
                "rating": rating,
                "fandoms": fandoms,
                "characters": characters,
                "stats": story_stats,
                "more_meta": more_meta,
            },
        )
    by_suffix.update({"url": data.pop("source")})
    data.update(by_suffix)
    return data


def parse_story(data: bytes | str) -> Story:
    obj = _DECODER.decode(data)
    obj = shape_data(obj)
    return msgspec.convert(obj, type=Story)


class Client:
    """A client for the Fichub API.

    Parameters
    ----------
    session: :class:`aiohttp.ClientSession`, optional
        The asynchronous HTTP session to make requests with. If not passed in, automatically generated. Closing it is
        not handled automatically by the class if done outside an async context manager.
    headers: dict[:class:`str`, Any], optional
        The HTTP headers to send with any requests.
    sema_limit: :class:`int`
        The limit on the number of requests that can be made at once asynchronously. If not between 1 and 3, defaults
        to 2.
    """

    def __init__(
        self,
        *,
        headers: dict[str, Any] | None = None,
        session: aiohttp.ClientSession | None = None,
        sema_limit: int | None = None,
    ) -> None:
        self.headers = headers or {"User-Agent": f"FicHub API wrapper/v{im_version('fichub_api')}+@Thanos"}
        self.session = session
        self._sema_limit = sema_limit if (sema_limit and 1 <= sema_limit <= 3) else 2
        self._semaphore = asyncio.Semaphore(value=self._sema_limit)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    @property
    def sema_limit(self) -> int:
        """:class:`int`: The counter limit for the number of simultaneous requests.

        Limited to between 1 and 3 inclusive.
        """

        return self._sema_limit

    @sema_limit.setter
    def sema_limit(self, value: int) -> None:
        if 1 <= value <= 3:
            self._sema_limit = value
            self._semaphore = asyncio.Semaphore(value)
        else:
            msg = "To prevent hitting the FicHub API too much, this limit has to be between 1 and 3 inclusive."
            raise ValueError(msg)

    async def start_session(self) -> None:
        """Start an HTTP session attached to this instance if necessary."""

        if (not self.session) or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close the HTTP session attached to this instance if necessary."""

        if self.session and (not self.session.closed):
            await self.session.close()

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> bytes:
        """Gets fanfiction data from the FicHub API.

        This restricts the number of simultaneous requests.

        Parameters
        ----------
        endpoint: :class:`str`
            The path parameters for the endpoint.
        params: dict[:class:`str`, Any] | None, optional
            The query parameters to request from the endpoint.

        Returns
        -------
        :class:`bytes`
            The JSON data from the API response.

        Raises
        ------
        FicHubException
            If there's a client response error.
        """

        # TODO: Implement caching mechanism.
        await self.start_session()
        assert self.session

        async with self._semaphore:
            try:
                url = FICHUB_BASE_URL + endpoint
                async with self.session.get(url, params=params, headers=self.headers) as response:
                    response.raise_for_status()
                    return await response.read()
            except aiohttp.ClientResponseError as exc:
                msg = f"HTTP {exc.status}: {exc.message}"
                raise FicHubException(msg) from None

    async def get_story_metadata(self, url: str) -> Story:
        """Gets a specific story's metadata.

        Parameters
        ----------
        url: :class:`str`
            The story URL to look up.

        Returns
        -------
        :class:`Story`
            The queried story's metadata.
        """

        query = {"q": url}
        try:
            return parse_story(await self._get("/meta", params=query))
        except (msgspec.MsgspecError, KeyError) as err:
            msg = f"Unable to load story metadata from url: {url}"
            raise FicHubException(msg) from err

    async def get_download_urls(self, url: str) -> StoryDownload:
        """Gets all the download urls for a fanfic in various formats, including epub, html, mobi, and pdf.

        This may also include the story metadata.

        Parameters
        ----------
        url: :class:`str`
            The fanfiction url being queried.

        Returns
        -------
        :class:`DownloadUrls`
            An object containing all download urls returned by the API.
        """

        query = {"q": url}
        data = _DECODER.decode(await self._get("/epub", params=query))

        try:
            meta = msgspec.convert(shape_data(data["meta"]), type=Story)
        except (msgspec.MsgspecError, KeyError):
            meta = None

        try:
            urls = msgspec.convert(
                data["urls"],
                type=DownloadUrls,
                dec_hook=lambda _, v: urljoin("https://fichub.net/", v),
            )
        except (msgspec.MsgspecError, KeyError) as err:
            msg = f"Unable to load story download urls from url: {url}"
            raise FicHubException(msg) from err
        else:
            return StoryDownload(meta, urls)
