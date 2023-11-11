# FicHub API Wrapper
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/fichub-api.svg)](https://pypi.python.org/pypi/fichub-api)
[![License: MIT](https://img.shields.io/github/license/Sachaa-Thanasius/fichub-api.svg)](https://opensource.org/licenses/MIT)
[![Checked with pyright](https://img.shields.io/badge/pyright-checked-informational.svg)](https://github.com/microsoft/pyright/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A small asynchronous wrapper for the FicHub API, made to retrieve story data from various fanfiction and original fiction sites. For more information about FicHub, see their [website](https://fichub.net/) and [git repos](https://github.com/FicHub).

## Installing

**fichub-api currently requires Python 3.8 or higher.**

To install the library, run one of the following commands:

```shell
# Linux/macOS
python3 -m pip install -U fichub-api

# Windows
py -3 -m pip install -U fichub-api
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
