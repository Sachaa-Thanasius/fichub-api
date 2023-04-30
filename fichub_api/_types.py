from typing import TypedDict


class ExtendedMetadataFFN(TypedDict, total=False):
    category: str
    chapters: str
    characters: str
    crossover: bool
    fandom_ids: list
    fandom_stubs: list
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
    category: list
    category_hrefs: list
    character: list
    character_hrefs: list
    fandom: list
    fandom_hrefs: list
    freeform: list
    freeform_hrefs: list
    language: str
    rating: list
    rating_hrefs: list
    relationship: list
    relationship_hrefs: list
    stats: dict
    warning: list
    warning_hrefs: list


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
    fixits: list
    hashes: dict
    html_url: str
    info: str
    meta: StoryMetadata
    mobi_url: str
    notes: list
    pdf_url: str
    q: str
    slug: str
    urlId: str
    urls: dict
