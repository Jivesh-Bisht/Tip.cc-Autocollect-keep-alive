from asyncio import TimeoutError, sleep
from logging import (CRITICAL, DEBUG, ERROR, INFO, WARNING, Formatter,
                     StreamHandler, getLogger)
from math import acosh, asinh, atanh, ceil, cos, cosh, e, erf, exp
from math import fabs as abs
from math import factorial, floor
from math import fmod as mod
from math import (gamma, gcd, hypot, log, log1p, log2, log10, pi, pow, sin,
                  sinh, sqrt, tan, tau)
from random import randint
from re import compile
from time import time
from urllib.parse import quote, unquote

from aiohttp import ClientSession
from art import tprint
from discord import Client, HTTPException, LoginFailure, Message, NotFound, Status
from discord.ext import tasks
from questionary import checkbox, select, text

import os 
import threading
from flask import Flask


TOKEN = os.environ["TOKEN"]
PORT = os.environ["PORT"]
ID = os.environ["id"]


app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

class ColourFormatter(
    Formatter
):  # Taken from discord.py-self and modified to my liking.

    LEVEL_COLOURS = [
        (DEBUG, "\x1b[40;1m"),
        (INFO, "\x1b[34;1m"),
        (WARNING, "\x1b[33;1m"),
        (ERROR, "\x1b[31m"),
        (CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s \x1b[30;1m(%(filename)s:%(lineno)d)\x1b[0m",
            "%d-%b-%Y %I:%M:%S %p",
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[DEBUG]

        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        record.exc_text = None
        return output


handler = StreamHandler()
formatter = ColourFormatter()

handler.setFormatter(formatter)
logger = getLogger("tipcc_autocollect")
logger.addHandler(handler)
logger.setLevel("INFO")


def cbrt(x):
    return pow(x, 1 / 3)


try:
    from ujson import dump, load
except ModuleNotFoundError:
    logger.warning("ujson not found, using json instead.")
    from json import dump, load
except ImportError:
    logger.warning("ujson not found, using json instead.")
    from json import dump, load
else:
    logger.info("ujson found, using ujson.")


channel = None


print("\033[0;35m")
tprint("QuartzWarrior", font="smslant")
print("\033[0m")



config = {
        "TOKEN": TOKEN,
        "PRESENCE": "invisible",
        "CPM": 80,
        "FIRST": False,
        "id": ID,
        "channel_id": 0,
        "TARGET_AMOUNT": 0.0,
        "SMART_DELAY": True,
        "DELAY": 1,
        "BANNED_WORDS": ["bot", "ban"],
        "WHITELIST": [],
        "BLACKLIST": [],
        "CHANNEL_BLACKLIST": [],
        "IGNORE_USERS": [],
        "WHITELIST_ON": False,
        "BLACKLIST_ON": False,
        "CHANNEL_BLACKLIST_ON": False,
        "IGNORE_DROPS_UNDER": 0.0,
        "IGNORE_TIME_UNDER": 1.0,
        "IGNORE_THRESHOLDS": [],
        "DISABLE_AIRDROP": False,
        "DISABLE_TRIVIADROP": False,
        "DISABLE_MATHDROP": False,
        "DISABLE_PHRASEDROP": False,
        "DISABLE_REDPACKET": True,
    }
token_regex = compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27,}")
decimal_regex = compile(r"^-?\d+(?:\.\d+)$")

banned_words = config["BANNED_WORDS"]
def validate_token(token):
    if token_regex.search(token):
        return True
    else:
        return False


def validate_decimal(decimal):
    if decimal_regex.match(decimal):
        return True
    else:
        return False


def validate_threshold_chance(s):
    try:
        threshold, chance = s.split(":")
        return (
            validate_decimal(threshold)
            and chance.isnumeric()
            and 0 <= int(chance) <= 100
        )
    except ValueError:
        if s == "":
            return True
        return False

client = Client(
    status=(
        Status.invisible
        if config["PRESENCE"] == "invisible"
        else (
            Status.online
            if config["PRESENCE"] == "online"
            else (
                Status.idle
                if config["PRESENCE"] == "idle"
                else Status.dnd if config["PRESENCE"] == "dnd" else Status.unknown
            )
        )
    )
)


@client.event
async def on_ready():
    global channel
    channel = client.get_channel(config["channel_id"])
    logger.info(f"Logged in as {client.user.name}#{client.user.discriminator}")
    if config["channel_id"] != 1 and client.user.id != config["id"]:
        tipping.start()
        logger.info("Tipping started.")
    else:
        logger.warning("Disabling tipping as requested.")


@tasks.loop(minutes=10.0)
async def tipping():
    await channel.send("$bals top")
    logger.debug("Sent command: $bals top")
    answer = await client.wait_for(
        "message",
        check=lambda message: message.author.id == 617037497574359050
        and message.embeds,
    )
    try:
        total_money = float(
            answer.embeds[0]
            .fields[-1]
            .value.split("$")[1]
            .replace(",", "")
            .replace("**", "")
            .replace(")", "")
            .replace("\u200b", "")
            .strip()
        )
    except Exception as e:
        logger.exception("Error occurred while getting total money, skipping tipping.")
        total_money = 0.0
    logger.debug(f"Total money: {total_money}")
    if total_money < config["TARGET_AMOUNT"]:
        logger.info("Target amount not reached, skipping tipping.")
        return
    try:
        pages = int(answer.embeds[0].author.name.split("/")[1].replace(")", ""))
    except:
        pages = 1
    if not answer.components:
        button_disabled = True
    for _ in range(pages):
        try:
            button = answer.components[0].children[1]
            button_disabled = button.disabled
        except:
            button_disabled = True
        for crypto in answer.embeds[0].fields:
            if "Estimated total" in crypto.name:
                continue
            if "DexKit" in crypto.name:
                content = f"$tip <@{config['id']}> all {crypto.name.replace('*', '').replace('DexKit (BSC)', 'bKIT')}"
            else:
                content = f"$tip <@{config['id']}> all {crypto.name.replace('*', '')}"
            async with channel.typing():
                await sleep(len(content) / config["CPM"] * 60)
            await channel.send(content)
            logger.debug(f"Sent tip: {content}")
        if button_disabled:
            try:
                await answer.components[0].children[2].click()
                logger.debug("Clicked next page button")
                return
            except IndexError:
                try:
                    await answer.components[0].children[0].click()
                    logger.debug("Clicked first page button")
                    return
                except IndexError:
                    return
        else:
            await button.click()
            await sleep(1)
            answer = await channel.fetch_message(answer.id)


@tipping.before_loop
async def before_tipping():
    logger.info("Waiting for bot to be ready before tipping starts...")
    await client.wait_until_ready()


"""
import random

def should_ignore_drop(drop_value):
    for threshold in config["IGNORE_THRESHOLDS"]:
        if drop_value <= threshold["threshold"]:
            # Generate a random number between 0 and 100
            random_number = random.randint(0, 100)
            # If the random number is less than the chance, ignore the drop
            if random_number < threshold["chance"]:
                return True
    # If none of the thresholds caused the drop to be ignored, don't ignore the drop
    return False
"""


@client.event
async def on_message(original_message: Message):
    if (
        original_message.content.startswith(
            ("$airdrop", "$triviadrop", "$mathdrop", "$phrasedrop", "$redpacket")
        )
        and not any(word in original_message.content.lower() for word in banned_words)
        and (
            not config["WHITELIST_ON"]
            or (
                config["WHITELIST_ON"]
                and original_message.guild.id in config["WHITELIST"]
            )
        )
        and (
            not config["BLACKLIST_ON"]
            or (
                config["BLACKLIST_ON"]
                and original_message.guild.id not in config["BLACKLIST"]
            )
        )
        and (
            not config["CHANNEL_BLACKLIST_ON"]
            or (
                config["CHANNEL_BLACKLIST_ON"]
                and original_message.channel.id not in config["CHANNEL_BLACKLIST"]
            )
        )
        and original_message.author.id not in config["IGNORE_USERS"]
    ):
        logger.debug(
            f"Detected drop in {original_message.channel.name}: {original_message.content}"
        )
        try:
            tip_cc_message = await client.wait_for(
                "message",
                check=lambda message: message.author.id == 617037497574359050
                and message.channel.id == original_message.channel.id
                and message.embeds
                and message.embeds[0].footer
                and (
                    "ends" in message.embeds[0].footer.text.lower()
                    or (
                        "Trivia time - " in message.embeds[0].title
                        and "ended" in message.embeds[0].footer.text.lower()
                    )
                )
                and str(original_message.author.id) in message.embeds[0].description,
                timeout=15,
            )
            logger.debug("Detected tip.cc message from drop.")
        except TimeoutError:
            logger.exception(
                "Timeout occurred while waiting for tip.cc message, skipping."
            )
            return
        embed = tip_cc_message.embeds[0]
        if "$" not in embed.description or "≈" not in embed.description:
            money = 0.0
        else:
            try:
                money = float(
                    embed.description.split("≈")[1]
                    .split(")")[0]
                    .strip()
                    .replace("$", "")
                    .replace(",", "")
                )
            except IndexError:
                logger.exception(
                    "Index error occurred during money splitting, skipping..."
                )
                return
        if money < config["IGNORE_DROPS_UNDER"]:
            logger.info(
                f"Ignored drop for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
            )
            return
        for threshold in config["IGNORE_THRESHOLDS"]:
            logger.debug(
                f"Checking threshold: {threshold['threshold']} with chance: {threshold['chance']}"
            )
            if money <= threshold["threshold"]:
                logger.debug(
                    f"Drop value {money} is less than or equal to threshold {threshold['threshold']}"
                )
                random_number = randint(0, 100)
                if random_number < threshold["chance"]:
                    logger.info(
                        f"Ignored drop from failed threshold for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
                    )
                    return
        logger.debug(f"Money: {money}")
        logger.debug(f"Drop ends in: {embed.timestamp.timestamp() - time()}")
        drop_ends_in = embed.timestamp.timestamp() - time()
        if drop_ends_in < config["IGNORE_TIME_UNDER"]:
            logger.info(
                f"Ignored drop for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
            )
            return
        if config["SMART_DELAY"]:
            logger.debug("Smart delay enabled, waiting...")
            if drop_ends_in < 0:
                logger.debug("Drop ended, skipping...")
                return
            delay = drop_ends_in / 4
            logger.debug(f"Delay: {round(delay, 2)}")
            await sleep(delay)
            logger.info(f"Waited {round(delay, 2)} seconds before proceeding.")
        elif config["DELAY"] != 0:
            logger.debug(f"Manual delay enabled, waiting {config['DELAY']}...")
            await sleep(config["DELAY"])
            logger.info(f"Waited {config['DELAY']} seconds before proceeding.")
        try:
            if "ended" in embed.footer.text.lower():
                logger.debug("Drop ended, skipping...")
                return
            elif "An airdrop appears" in embed.title and not config["DISABLE_AIRDROP"]:
                logger.debug("Airdrop detected, entering...")
                try:
                    button = tip_cc_message.components[0].children[0]
                except IndexError:
                    logger.exception(
                        "Index error occurred, meaning the drop most likely ended, skipping..."
                    )
                    return
                if "Enter airdrop" in button.label:
                    await button.click()
                    logger.info(
                        f"Entered airdrop in {original_message.channel.name} for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
                    )
            elif "Phrase drop!" in embed.title and not config["DISABLE_PHRASEDROP"]:
                logger.debug("Phrasedrop detected, entering...")
                content = embed.description.replace("\n", "").replace("**", "")
                content = content.split("*")
                try:
                    content = content[1].replace("​", "").replace("\u200b", "").strip()
                except IndexError:
                    logger.exception("Index error occurred, skipping...")
                    pass
                else:
                    logger.debug("Typing and sending message...")
                    length = len(content) / config["CPM"] * 60
                    async with original_message.channel.typing():
                        await sleep(length)
                    await original_message.channel.send(content)
                    logger.info(
                        f"Entered phrasedrop in {original_message.channel.name} for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
                    )
            elif "appeared" in embed.title and not config["DISABLE_REDPACKET"]:
                logger.debug("Redpacket detected, claiming...")
                try:
                    button = tip_cc_message.components[0].children[0]
                except IndexError:
                    logger.exception(
                        "Index error occurred, meaning the drop most likely ended, skipping..."
                    )
                    return
                if "envelope" in button.label:
                    await button.click()
                    logger.info(
                        f"Claimed envelope in {original_message.channel.name} for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
                    )
            elif "Math" in embed.title and not config["DISABLE_MATHDROP"]:
                logger.debug("Mathdrop detected, entering...")
                content = embed.description.replace("\n", "").replace("**", "")
                content = content.split("`")
                try:
                    content = content[1].replace("​", "").replace("\u200b", "")
                except IndexError:
                    logger.exception("Index error occurred, skipping...")
                    pass
                else:
                    logger.debug("Evaluating math and sending message...")
                    answer = eval(content)
                    if isinstance(answer, float) and answer.is_integer():
                        answer = int(answer)
                    logger.debug(f"Answer: {answer}")
                    if not config["SMART_DELAY"] and config["DELAY"] == 0:
                        length = len(str(answer)) / config["CPM"] * 60
                        async with original_message.channel.typing():
                            await sleep(length)
                    await original_message.channel.send(answer)
                    logger.info(
                        f"Entered mathdrop in {original_message.channel.name} for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
                    )
            elif "Trivia time - " in embed.title and not config["DISABLE_TRIVIADROP"]:
                logger.debug("Triviadrop detected, entering...")
                category = embed.title.split("Trivia time - ")[1].strip()
                bot_question = embed.description.replace("**", "").split("*")[1]
                async with ClientSession() as session:
                    async with session.get(
                        f"https://raw.githubusercontent.com/QuartzWarrior/OTDB-Source/main/{quote(category)}.csv"
                    ) as resp:
                        lines = (await resp.text()).splitlines()
                        for line in lines:
                            question, answer = line.split(",")
                            if bot_question.strip() == unquote(question).strip():
                                answer = unquote(answer).strip()
                                try:
                                    buttons = tip_cc_message.components[0].children
                                except IndexError:
                                    logger.exception(
                                        "Index error occurred, meaning the drop most likely ended, skipping..."
                                    )
                                    return
                                for button in buttons:
                                    if button.label.strip() == answer:
                                        await button.click()
                                logger.info(
                                    f"Entered triviadrop in {original_message.channel.name} for {embed.description.split('**')[1]} {embed.description.split('**')[2].split(')')[0].replace(' (','')}"
                                )
                                return

        except AttributeError:
            logger.exception("Attribute error occurred")
            return
        except HTTPException:
            logger.exception("HTTP exception occurred")
            return
        except NotFound:
            logger.exception("Not found exception occurred")
            return
    elif original_message.content.startswith(
        ("$airdrop", "$triviadrop", "$mathdrop", "$phrasedrop", "$redpacket")
    ) and any(word in original_message.content.lower() for word in banned_words):
        logger.info(
            f"Banned word detected in {original_message.channel.name}, skipping..."
        )
    elif original_message.content.startswith(
        ("$airdrop", "$triviadrop", "$mathdrop", "$phrasedrop", "$redpacket")
    ) and (
        config["WHITELIST_ON"] and original_message.guild.id not in config["WHITELIST"]
    ):
        logger.info(
            f"Whitelist enabled and drop not in whitelist, skipping {original_message.channel.name}..."
        )
    elif original_message.content.startswith(
        ("$airdrop", "$triviadrop", "$mathdrop", "$phrasedrop", "$redpacket")
    ) and (config["BLACKLIST_ON"] and original_message.guild.id in config["BLACKLIST"]):
        logger.info(
            f"Blacklist enabled and drop in blacklist, skipping {original_message.channel.name}..."
        )
    elif original_message.content.startswith(
        ("$airdrop", "$triviadrop", "$mathdrop", "$phrasedrop", "$redpacket")
    ) and (
        config["CHANNEL_BLACKLIST_ON"]
        and original_message.channel.id in config["CHANNEL_BLACKLIST"]
    ):
        logger.info(
            f"Channel blacklist enabled and drop in channel blacklist, skipping {original_message.channel.name}..."
        )
    elif (
        original_message.content.startswith(
            ("$airdrop", "$triviadrop", "$mathdrop", "$phrasedrop", "$redpacket")
        )
        and original_message.author.id in config["IGNORE_USERS"]
    ):
        logger.info(
            f"User in ignore list detected in {original_message.channel.name}, skipping..."
        )

def run_bot():
    try:
        client.run(config["TOKEN"], log_handler=handler, log_formatter=formatter)
    except LoginFailure:
        logger.critical("Invalid token, restart the program.")
        config["TOKEN"] = ""
        with open("config.json", "w") as f:
            dump(config, f, indent=4)

def run_server():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":

    flask_thread = threading.Thread(target=run_server)
    discord_thread = threading.Thread(target=run_bot)
    
    flask_thread.start()
    discord_thread.start()
    
    flask_thread.join()
    discord_thread.join()
