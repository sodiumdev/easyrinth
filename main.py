import difflib
import io
import pprint

import orjson

import config
import cache
import aiohttp
import asyncio
import typing as tp

import argparse
import colorama
import zipfile
import easygui

colorama.init()


HEADERS = {
    "User-Agent": f"{config.appName}/0.01a (https://sodiumdev.xyz, Sodium#0001, deep.unstable@gmail.com)",
    "Authorization": config.sensitive.github_token
}

pid: str = config.projectInfo.id
url: str = config.apiEndpoint

badges: dict[str, str] = config.badges.value
possible_badges: list[str] = list(badges.keys())
powered_by: str = config.projectInfo.poweredBy
downloads: str = f"https://img.shields.io/modrinth/dt/{pid}?color=%23000000&style=for-the-badge"
badge: str = badges.get(powered_by)
title: str | None = None


async def warn(message: str) -> bool:
    warning = input(f"{message} Do you want to continue? (y/n) ").lower()

    if warning.startswith("n"):
        return False
    elif not warning.startswith("y"):
        await warn(message)

        return False

    return True


def generate_html(tag: str, attributes: dict[str, str], *, empty: bool = False) -> str:
    if empty:
        return f"<{tag}>"
    quote = "\""
    return f"<{tag} {' '.join([f'{key}={quote}{value}{quote}' for key, value in attributes.items()])} />"


def image_from_link(link: str, size: int = 200, *, alt: str = "?") -> str:
    return generate_html("img", {
        "src": link,
        "width": str(size),
        "alt": alt
    })


async def main(client: aiohttp.ClientSession, *, debug: bool = False, mods: dict[str, str]) -> None:
    while True:
        print("1: Generate Description\n"
              "*More Options Will Be Added Later In Development.*\n")

        option: str = input("Select Option: ")

        try:
            option: int = int(option)
        except ValueError:
            raise ValueError("Hey, that's not a valid option!")

        match option:
            case 1:
                res = await warn("\nThis will reset the current description of the project. \n"
                                 "If no, this will only write the description to `description.md`.")

                body = f"{image_from_link(badge)}\n"
                body += f"{generate_html('br', {}, empty=True)}\n"
                body += f"{image_from_link(downloads)}\n\n"

                body += f"# {title}\n"
                body += "\n".join(config.projectInfo.shortDescription) + "\n"

                body += "<details>\n<summary>Mods Used</summary>\n\n"

                for key, value in mods.items():
                    body += f"- [{key}]({value})\n"

                body += "</details>"

                if not res:
                    with open('description.md', 'w') as w:
                        w.write(body)
                    return

                raise NotImplemented

            case _:
                raise ValueError("Hey, that's not a valid option!")


async def cache_mods(client: aiohttp.ClientSession, r: io.FileIO | tp.IO[bytes]) -> dict | None:
    global title

    mods: dict = {}

    res = orjson.loads(r.read())

    if args.verbose:
        pprint.pprint(res, indent=4)
        print()

    title = res["name"]
    files: list[dict[str, tp.Any]] = res["files"]

    filtered = list(
        filter(lambda x: cache.is_cached(x["downloads"][0].removeprefix("https://").split("/")[2]),
               files))

    if args.verbose:
        print(filtered)

    if len(filtered) > 216:
        print(colorama.Fore.RED + "Mod count can't be more than 216!" + colorama.Fore.RESET)
        return None

    for file in files:
        download: str = file["downloads"][0]
        mod_id: str = download.removeprefix("https://").split("/")[2]

        if cache.is_cached(mod_id):
            mods[cache.get_cache().value[mod_id]] = f"https://modrinth.com/mod/{mod_id}"

            if args.verbose:
                print(f"Mod `{cache.get_cache().value[mod_id]}` was pulled from cache.")
            continue

        async with client.get(f"{url}/project/{mod_id}") as resp:
            res = await resp.json(loads=orjson.loads)

            mods[res["title"]] = f"https://modrinth.com/mod/{mod_id}"

            cache.cache(mod_id, res["title"])

            if args.verbose:
                print(f"Mod `{res['title']}` successfully downloaded.")

        await asyncio.sleep(0)

    return mods


async def wrapper(args: argparse.Namespace) -> None:
    global title

    if badge is None:
        quit(f"Error :: `projectInfo.poweredBy` is invalid. Did you mean "
              f"`{difflib.get_close_matches(powered_by, possible_badges, 1, 0)[0]}` instead of `{powered_by}`?")

    async with aiohttp.ClientSession() as client:
        mods: dict = {}

        if args.packpath.endswith(".zip"):
            with zipfile.ZipFile(args.packpath, 'r') as z:
                with z.open('modrinth.index.json', 'r') as r:
                    mods = await cache_mods(client, r)
                    if mods is None:
                        return
        elif args.packpath.endswith(".json"):
            with open(args.packpath, 'r') as r:
                mods = await cache_mods(client, r)
                if mods is None:
                    return
        elif args.packpath.endswith(".ferium") or args.packpath.endswith(".txt"):
            with open(args.packpath, 'r') as r:
                if r.read().count("Modrinth") != len(r.readlines()):
                    quit(colorama.Fore.RED + "Ferium list is not valid." + colorama.Fore.RESET)

                for line in r.readlines():
                    line = line.split("Modrinth")

                    mods[line[0].strip()] = f"https://modrinth.com/mod/{line[1].strip()})"

        cache.dump()

        return await main(client, debug=args.verbose, mods=mods)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{str(config.appName).title()}"
                                                 f" - A program that helps create descriptions on Modrinth.")

    parser.add_argument("-v", "--verbose", action="store_true", help="Sets verbose mode.")
    parser.add_argument("-pp", "--packpath", type=str, help="Modpack path (.mrpack or .txt containing ferium list).",
                        required=False)

    args = parser.parse_args()

    if args.packpath is None:
        args.packpath = easygui.fileopenbox(title="Select Modpack",
                                            default="\\*Modrinth Modpack Files",
                                            filetypes=[["*.mrpack", "*.json", "*.zip", "Modrinth Modpack Files"]])

        if args.packpath is None:
            quit("Invalid modpack path!")

    if args.verbose:
        print(colorama.Fore.RED + "Verbose mode is on!" + colorama.Fore.RESET)

    asyncio.run(wrapper(args))
