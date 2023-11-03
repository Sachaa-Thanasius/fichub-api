from __future__ import annotations

import asyncio
import datetime
from importlib.metadata import version as im_version
from typing import TYPE_CHECKING, Any, Union
from urllib.parse import urljoin

import aiohttp
import msgspec


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self
else:
    TracebackType = Self = object


__all__ = ("FICHUB_BASE_URL", "FicHubException", "Story", "StoryDownload", "Client")

_DECODER = msgspec.json.Decoder()
FICHUB_BASE_URL = "https://fichub.net/api/v0"


class FicHubException(Exception):
    """The base exception for the FicHub API."""


class AO3Stats(msgspec.Struct, frozen=True):
    """The basic statistics for a story from AO3.

    Attributes
    ----------
    bookmarks: :class:`int`, default=0
        The number of bookmarks this story has.
    comments: :class:`int`, default=0
        The number of comments this story has.
    hits: :class:`int`, default=0
        The number of hits this story has.
    kudos: :class:`int`, default=0
        The number of kudos this story has. Defaults to 0.
    """

    bookmarks: int = 0
    comments: int = 0
    hits: int = 0
    kudos: int = 0


class FFNStats(msgspec.Struct, frozen=True):
    """The basic statistics for a story from FFN.

    Attributes
    ----------
    favorites: :class:`int`, default=0
        The number of favorites this story has.
    follows: :class:`int`, default=0
        The number of follows this story has.
    reviews: :class:`int`, default=0
        The number of reviews this story has.
    """

    favorites: int = 0
    follows: int = 0
    reviews: int = 0


class NoStats(msgspec.Struct, frozen=True):
    """The statistics for a story where those fields are inaccessible through Fichub."""


class Author(msgspec.Struct, frozen=True):
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


class Tags(msgspec.Struct, frozen=True):
    """The AO3-specific tags attached to a story.

    Attributes
    ----------
    category: tuple[:class:`str`, ...]
        The category-type tags for this story. Defaults to an empty tuple.
    freeform: tuple[:class:`str`, ...]
        The freeform-type tags for this story. Defaults to an empty tuple.
    relationship: tuple[:class:`str`, ...]
        The relationship-type tags for this story. Defaults to an empty tuple.
    warning: tuple[:class:`str`, ...]
        The warning-type tags for this story. Defaults to an empty tuple.
    """

    category: tuple[str, ...] = msgspec.field(default_factory=tuple)
    freeform: tuple[str, ...] = msgspec.field(default_factory=tuple)
    relationship: tuple[str, ...] = msgspec.field(default_factory=tuple)
    warning: tuple[str, ...] = msgspec.field(default_factory=tuple)


class BaseStory(msgspec.Struct, frozen=True):
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
    created: :class:`datetime.datetime`
        The date and time when the story was published.
    updated: :class:`datetime.datetime`
        The date and time when the story was last updated.
    status: :class:`str`
        The completion status. Can be either "ongoing" or "complete".
    words: :class:`int`
        The number of words in the story.
    language: :class:`str`, default="English"
        The language the story is written in.
    rating: :class:`str`, default="No Rating"
        The maturity rating of the story.
    fandoms: tuple[:class:`str`, ...]
        The fandom(s) this story occupies.
    characters: tuple[:class:`str`, ...]
        The declared cast of characters.
    """

    author: Author
    title: str
    description: str
    url: str
    chapters: int
    created: datetime.datetime
    updated: datetime.datetime
    status: str
    words: int
    language: str = "English"
    rating: str = "No Rating"
    fandoms: tuple[str, ...] = msgspec.field(default_factory=tuple)
    characters: tuple[str, ...] = msgspec.field(default_factory=tuple)


class AO3Story(BaseStory, frozen=True, tag="ao3"):
    """Slightly specialized story metadata retrieved from Fichub for an AO3 work.

    Attributes
    ----------
    is_crossover: :class:`bool`, default=False
        Whether this story is a crossover. Defaults to False.
    tags: :class:`Tags`
        The other AO3-specific tags attached to this story. Defaults to a collection of empty tuples.
    stats: :class:`AO3Stats`
        The story metrics specific to this site. Defaults to a collection of zeros.
    """

    is_crossover: bool = False
    tags: Tags = msgspec.field(default_factory=Tags)
    stats: AO3Stats = msgspec.field(default_factory=AO3Stats)


class FFNStory(BaseStory, frozen=True, tag="ffn"):
    """Slightly specialized story metadata retrieved from Fichub for an FFN work.

    Attributes
    ----------
    is_crossover: :class:`bool`, default=False
        Whether this story is a crossover. Defaults to False.
    genres: :class:`str`
        The FFN-specific genres of the work. Must be parsed manually.
    stats: :class:`FFNStats`
        The story metrics specific to this site. Defaults to a collection of zeros.
    """

    is_crossover: bool = False
    genres: str = ""
    stats: FFNStats = msgspec.field(default_factory=FFNStats)


class OtherStory(BaseStory, frozen=True, tag="other"):
    """General story metadata retrieved from Fichub.

    Attributes
    ----------
    stats: :class:`NoStats`
        An empty story metrics class.
    """

    stats: NoStats = msgspec.field(default_factory=NoStats)


Story = Union[AO3Story, FFNStory, OtherStory]


class DownloadUrls(msgspec.Struct, frozen=True):
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


class StoryDownload(msgspec.Struct, frozen=True):
    """The story's download links and metadata."""

    urls: DownloadUrls
    meta: Story | None = None


def _camel_to_snake_case(string: str) -> str:
    """Converts a string from camel case to snake case.

    Source of code: https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#comment133686723_44969381
    """

    return "".join(
        char
        if not char.isupper()
        else ("" if i and (substr := string[i - 1] + (next_char or "")) == substr.upper() else "_") + char.lower()
        for i, (char, next_char) in enumerate(zip(string, [*string[1:], None]))
    ).lstrip("_")


def shape_data(data: dict[str, Any]) -> dict[str, Any]:
    # TODO: Find a way to optimize this.
    shaped: dict[str, Any] = {}

    # Identify site origin.
    if "fanfiction.net" in data["source"]:
        type_ = "ffn"
    elif "archiveofourown.org" in data["source"]:
        type_ = "ao3"
    else:
        type_ = "other"

    # Collect author info.
    for key in data:
        if "author" in key:
            suffix = (key.split("author"))[1]
            shaped.setdefault("author", {})[_camel_to_snake_case(suffix) if suffix else "name"] = data[key]

    # Fix Ao3 links for authors.
    if type_ == "ao3":
        shaped["author"]["url"] = urljoin("https://www.archiveofourown.org", shaped["author"]["url"])

    # Adjust other metadata.
    if more_meta := data["rawExtendedMeta"]:
        if type_ == "ffn":
            story_stats: dict[str, Any] = {
                key: int(more_meta.get(key, "0").replace(",", "")) for key in ("favorites", "follows", "reviews")
            }
            rating = more_meta["rated"]
            if len(fandoms := more_meta["raw_fandom"].split(" + ", 1)) > 1:
                fandoms[-1] = fandoms[-1].removesuffix(" Crossover")
            characters = [
                char
                for char in more_meta["characters"].replace("[", ", ").replace("]", ", ").split(", ")
                if char.strip()
            ]
            crossover = more_meta.get("crossover")
            shaped.update({"genres": more_meta.get("genres", "")})
        elif type_ == "ao3":
            story_stats = {
                key: int(more_meta["stats"].get(key, "0").replace(",", ""))
                for key in ("bookmarks", "comments", "hits", "kudos")
            }
            rating = more_meta.get("rating")[0]
            fandoms = more_meta.pop("fandom")
            characters = more_meta.pop("character")
            crossover = len(fandoms) > 1
            shaped.update({"tags": more_meta})
        else:
            story_stats = {}
            rating, fandoms, characters = "No Rating", (), ()
            crossover = False

        try:
            more_meta.pop("stats")
        except KeyError:
            pass

        shaped.update(
            {
                "language": more_meta.pop("language", "English"),
                "rating": rating,
                "fandoms": fandoms,
                "characters": characters,
                "stats": story_stats,
                "is_crossover": crossover,
            },
        )
    shaped.update({"url": data.pop("source"), "type": type_})
    data.update(shaped)
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

    async def get_story_downloads(self, url: str) -> StoryDownload:
        """Gets all the download urls for a fanfic in various formats, including epub, html, mobi, and pdf.

        This may also include the story metadata.

        Parameters
        ----------
        url: :class:`str`
            The fanfiction url being queried.

        Returns
        -------
        :class:`StoryDownload`
            An object containing all the available metadata and download urls returned by the API.
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
            return StoryDownload(urls, meta)
