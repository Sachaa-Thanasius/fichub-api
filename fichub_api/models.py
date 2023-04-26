from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from attrs import define, Factory
from cattrs import Converter
from cattrs.gen import make_dict_structure_fn, override
from markdownify import markdownify as md


__all__ = ("DownloadUrls", "Author", "Story")


@define
class DownloadUrls:
    """A collection of download links for a story retrieved from FicHub.

    These links are short term and expire after some length of time, due to being in FicHub's cache.

    Attributes
    ----------
    epub : :class:`str`
        A download link for an epub file.
    html : :class:`str`
        A download link for an html file.
    mobi : :class:`str`
        A download link for a mobi file.
    pdf : :class:`str`
        A download link for a pdf file.
    """

    epub: str
    html: str
    mobi: str
    pdf: str


@define
class Author:
    """The basic metadata of an author.

    Attributes
    ----------
    name : :class:`str`
        The name of the author.
    id : :class:`int`
        An arbitrary FicHub author id. Not generally useful.
    local_id : :class:`str`
        The id of the author on a particular website.
    url : :class:`str`
        The url of the author's profile on a particular website.
    """

    name: str
    id: int
    local_id: str
    url: str


@define
class Story:
    """The basic metadata of a work retrieved from FicHub.

    Attributes
    ----------
    author : :class:`Author`
        The author's information. Some of it is website-specific.
    title : :class:`str`
        The story title.
    description : :class:`str`
        The description or summary.
    source : :class:`str`
        The source url.
    chapters : :class:`int`
        The number of chapters.
    created : :class:`datetime`
        The date and time when the story was published.
    updated : :class:`datetime`
        The date and time when the story was last updated.
    status : :class:`str`
        The completion status. Can be either "ongoing" or "complete".
    words : :class:`int`
        The number of words in the story.
    language : :class:`str`
        The language the story is written in.
    fandoms : list[:class:`str`]
        The fandom(s) this story occupies.
    characters : list[:class:`str`]
        The declared cast of characters.
    stats : dict[:class:`str`, :class:`int`]
        The story metrics, such as hits on Ao3 or favorites on FFN. Differs between sites, so they must be retrieved by name manually.
    more_meta : dict[:class:`str`, Any]
        Extra metadata, such as href endpoints from AO3. Must be known by name to be retrieved.
    """

    author: Author
    title: str
    description: str  # Has paragraph tags
    source: str
    chapters: int
    created: datetime
    updated: datetime
    status: str
    words: int
    language: str = "English"
    rating: str = "No Rating"
    fandoms: list[str] = Factory(list)
    characters: list[str] = Factory(list)
    stats: dict[str, int] = Factory(dict)
    more_meta: dict[str, Any] = Factory(dict)


# Cattrs converter instantiation, hooks, and logic.
def _camel_to_snake_case(string: str) -> str:
    """Converts a string from camel case to snake case.

    References
    ----------
    StackOverFlow post: https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#comment133686723_44969381
    """

    return "".join(
        char if not char.isupper() else (
            "" if i and (substr := string[i - 1] + (next_char or "")) == substr.upper() else "_"
        ) + char.lower() for i, (char, next_char) in enumerate(zip(string, [*string[1:], None]))
    ).lstrip("_")


def _fichub_preprocessing(cls: type, c: Converter) -> None:
    """Register a specific structuring hook to process the API response properly."""

    handler = make_dict_structure_fn(cls, c)    # type: ignore

    def preprocessing_hook(val: dict[str, Any], _) -> Any:
        """Beat the dictionary into shape before structuring it."""

        by_suffix = {}

        # Author
        for key in val:
            if "author" in key:
                suffix = (key.split("author"))[1]
                by_suffix.setdefault("author", {})[_camel_to_snake_case(suffix) if suffix else "name"] = val[key]

        # Remove markdown from description.
        by_suffix["description"] = md(val["description"])

        # FicHub only returns the endpoints for Ao3 instead of full links.
        if "archiveofourown.org" in val["source"]:
            by_suffix["author"]["url"] = urljoin("https://www.archiveofourown.org", by_suffix["author"]["url"])

        # Shift metadata to the main Story class.
        more_meta: dict | None = val["rawExtendedMeta"]
        if more_meta:
            by_suffix["language"] = more_meta.pop("language", "English")

            if "fanfiction.net" in val["source"]:
                story_stats = {key: int(more_meta.pop(key, "0").replace(",", "")) for key in ("favorites", "follows", "reviews")}
                rating = more_meta.pop("rated")
                if len(fandoms := more_meta.pop("raw_fandom").split(" + ")) > 1:
                    fandoms[-1] = fandoms[-1].removesuffix(" Crossover")
                characters = [char for char in more_meta.pop("characters").replace("[", ", ").replace("]", ", ").split(", ") if char.strip()]
            elif "archiveofourown.org" in val["source"]:
                story_stats = {key: int(more_meta["stats"].pop(key, "0").replace(",", "")) for key in ("bookmarks", "comments", "hits", "kudos")}
                rating = more_meta.pop("rating")[0]
                fandoms = more_meta.pop("fandom")
                characters = more_meta.pop("character")
            else:
                story_stats = {}
                rating, fandoms, characters = "No Rating", [], []

            by_suffix["rating"] = rating
            by_suffix["fandoms"] = fandoms
            by_suffix["characters"] = characters
            by_suffix["stats"] = story_stats
            by_suffix["more_meta"] = more_meta
        return handler(val | by_suffix, _)

    c.register_structure_hook(cls, preprocessing_hook)


# Urls converter.
_download_urls_converter = Converter()
_download_urls_converter.register_structure_hook(str, lambda v, _: urljoin("https://fichub.net/", v))

# Story/metadata converter.
_meta_converter = Converter()
_meta_converter.register_structure_hook(datetime, lambda dt, _: datetime.fromisoformat(dt))
_meta_converter.register_unstructure_hook(datetime, lambda dt: datetime.isoformat(dt))
_fichub_preprocessing(Story, _meta_converter)
# _meta_converter.register_structure_hook(Story, make_dict_structure_fn(Story, _meta_converter, description=override()))
