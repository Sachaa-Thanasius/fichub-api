from __future__ import annotations

import asyncio
from time import perf_counter

import aiohttp
import msgspec

import fichub_api


urls = [
    "https://archiveofourown.org/works/45753478/",
    "https://archiveofourown.org/works/35453491/",
    "https://www.fanfiction.net/s/13766768/1/Harry-Potter-and-the-Conjoining-of-Paragons/",
    "https://www.fanfiction.net/s/13274956/1/Harry-Potter-Squatter/",
    "https://forums.spacebattles.com/threads/nemesis-worm-au.747148",
    "https://forums.sufficientvelocity.com/threads/there-is-nothing-to-fear-harry-potter-au-gryffindor-voldemort.49249/",
    "https://archiveofourown.org/works/45753478/",
    "https://archiveofourown.org/works/35453491/",
    "https://www.fanfiction.net/s/13766768/1/Harry-Potter-and-the-Conjoining-of-Paragons/",
    "https://www.fanfiction.net/s/13274956/1/Harry-Potter-Squatter/",
    "https://forums.spacebattles.com/threads/nemesis-worm-au.747148",
    "https://forums.sufficientvelocity.com/threads/there-is-nothing-to-fear-harry-potter-au-gryffindor-voldemort.49249/",
]


async def do_work(client: fichub_api.Client, url: str) -> list[str]:
    story_metadata = await client.get_story_metadata(url)
    return [f"{name:>15}  |  {value}" for name, value in msgspec.structs.asdict(story_metadata).items()]


async def test() -> None:
    """Get metadata from a collection of fiction links."""

    # Create a ClientSession in order to close it gracefully. Not strictly necessary, since the fichub client can create
    # its own session if it's used as an async context manager (i.e. async with).
    async with aiohttp.ClientSession() as session:
        client = fichub_api.Client(session=session)

        # Get the metadata for multiple works multiple times.
        start_time = perf_counter()
        coros = [do_work(client, url) for url in urls]
        results = await asyncio.gather(*coros)
        end_time = perf_counter()
        print("\n\n-------------------------------\n".join("\n".join(data) for data in results))
        print(f"Time taken: {end_time - start_time:.5f}")

    print("Exiting now...")
    await asyncio.sleep(0.25)


if __name__ == "__main__":
    asyncio.run(test())
