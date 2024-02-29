# TODO: Switch to tests that don't ping the API.
from __future__ import annotations

import msgspec
import pytest

import fichub_api


@pytest.mark.parametrize(
    "test_url",
    [
        "https://archiveofourown.org/works/45753478/",
        "https://archiveofourown.org/works/35453491/",
        "https://archiveofourown.org/works/51331387",
        "https://www.fanfiction.net/s/13766768/1/Harry-Potter-and-the-Conjoining-of-Paragons/",
        "https://www.fanfiction.net/s/13274956/1/Harry-Potter-Squatter/",
        "https://www.fanfiction.net/s/14295079/1/The-Crow-Rebooted",
        "https://forums.spacebattles.com/threads/nemesis-worm-au.747148",
        "https://forums.sufficientvelocity.com/threads/there-is-nothing-to-fear-harry-potter-au-gryffindor-voldemort.49249/",
    ],
)
@pytest.mark.asyncio
async def test_get_story_metadata(test_url):
    async with fichub_api.Client() as client:
        story = await client.get_story_metadata(test_url)

    assert story
    assert hash(story)


@pytest.mark.parametrize(
    "test_url",
    [
        "https://archiveofourown.org/works/45753478/",
        "https://archiveofourown.org/works/35453491/",
        "https://archiveofourown.org/works/51331387",
        "https://www.fanfiction.net/s/13766768/1/Harry-Potter-and-the-Conjoining-of-Paragons/",
        "https://www.fanfiction.net/s/13274956/1/Harry-Potter-Squatter/",
        "https://www.fanfiction.net/s/14295079/1/The-Crow-Rebooted",
        "https://forums.spacebattles.com/threads/nemesis-worm-au.747148",
        "https://forums.sufficientvelocity.com/threads/there-is-nothing-to-fear-harry-potter-au-gryffindor-voldemort.49249/",
    ],
)
@pytest.mark.asyncio
async def test_get_story_downloads(test_url):
    async with fichub_api.Client() as client:
        story = await client.get_story_downloads(test_url)

    assert story
    assert hash(story)

    display = [f"{name:>15}  |  {value}" for name, value in msgspec.structs.asdict(story.meta).items()]
    print("\n".join(display))
    print("\n\n-------------------------------\n")
