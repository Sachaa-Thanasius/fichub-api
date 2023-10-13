# FicHub API Wrapper
A small asynchronous wrapper for the FicHub API, made to retrieve story data from various fanfiction and original fiction sites. For more information about FicHub, see their [website](https://fichub.net/) and [git repos](https://github.com/FicHub).

## Installing
**fichub-api-wrapper currently requires Python 3.8 or higher.**

To install the library, run one of the following commands:

```shell
# Linux/macOS
python3 -m pip install -U git+https://github.com/Sachaa-Thanasius/fichub-api-wrapper

# Windows
py -3 -m pip install -U git+https://github.com/Sachaa-Thanasius/fichub-api-wrapper
```

## Example
For more examples, see the [examples folder](https://github.com/Sachaa-Thanasius/fichub-api/examples).

```python
import asyncio
import aiohttp
import fichub_api as fichub

async def main():
    async with aiohttp.ClientSession() as session:
        client = fichub.Client(session=session)
        url = "https://www.fanfiction.net/s/13912800/1/Magical-Marvel"
        story_metadata = await client.get_story_metadata(url)
        print(
            f"Story Metadata (link: '{story_metadata.url}')\n",
            f"    {story_metadata.title}\n",
            f"        {story_metadata.description}\n"
        )

asyncio.run(main())
```
