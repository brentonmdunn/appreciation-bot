"""Main functionality of bot"""

from collections import defaultdict
import csv
import os
import discord
from discord.ext import commands
import requests

from logger import logger

TOKEN: str = os.environ["TOKEN"]
CSV_URL: str = os.environ["CSV_URL"]

FNAME_COL = 2
LNAME_COL = 3
FOOD_ALLERGY_YN_COL = 4
FOOD_ALLERGY_LIST_COL = 5
IS_SENIOR_COL = 6
FAV_COLOR_COL = 12
FAV_SNACK_COL = 13
FAV_ANIMAL_COL = 14
FAV_HOBBY_COL = 15
FAV_ARTIST_COL = 16
FAV_MOVIE_COL = 17
FAV_BIBLE_VERSE_COL = 18
FAV_MEMORY_COL = 19
QQC_COL = 20


def run() -> None:
    """Main method for bot."""

    intents = discord.Intents.all()
    intents.messages = True
    intents.guilds = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        """Runs when bot first starts up. Syncs slash commands with server."""
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} command(s).")
        except Exception as e:  # pylint: disable=W0718
            print(e)

    @bot.event
    async def on_message(message):
        if message.author.bot:  # Ignore bot messages
            return

        await bot.process_commands(message)  # Ensures other commands still work

    @bot.event
    async def on_raw_reaction_add(payload):
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return  # DM or unknown guild

        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return  # Ensure it's a text channel

        message = await channel.fetch_message(payload.message_id)  # Fetch the message

        user = guild.get_member(payload.user_id)

        # Check if the reaction is from a bot
        if user and user.bot:
            print(f"Ignoring bot reaction from {user.name}")
            return

    @bot.event
    async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
        """Logs when a reaction is removed."""
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return  # DM or unknown guild

        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return  # Ensure it's a text channel

        message = await channel.fetch_message(payload.message_id)  # Fetch the message
        user = guild.get_member(payload.user_id)

        if user and user.bot:
            print(f"Ignoring bot reaction removal from {user.name}")
            return

        if not user:
            return

        # Sample
        # log_channel = bot.get_channel(SERVING_BOT_SPAM_CHANNEL_ID)
        # if log_channel:
        #     await log_channel.send(f"{user.name} unreacted {payload.emoji} to message '{discord.utils.escape_mentions(message.content)}' in #{channel.name}")
        # return

    @bot.tree.command(
        name="profile",
        description="Lists answers to the questions that the senior put on RSVP form",
    )
    async def profile(interaction: discord.Interaction, name: str) -> None:
        response = requests.get(CSV_URL, timeout=100)

        if response.status_code != 200:
            await interaction.response.send_message("Error occurred trying to get CSV.")

        csv_data = response.content.decode("utf-8")
        csv_reader = csv.reader(csv_data.splitlines(), delimiter=",")

        responses = {}
        is_first = True
        for row in csv_reader:
            if is_first:
                is_first = False
                continue

            if (
                name not in row[FNAME_COL].lower()
                and name not in row[LNAME_COL].lower()
                or "senior" not in row[IS_SENIOR_COL]
            ):
                continue

            responses[
                f"{row[FNAME_COL].capitalize()} {row[LNAME_COL].capitalize()}"
            ] = {
                "favorite color": row[FAV_COLOR_COL],
                "favorite food/snack": row[FAV_SNACK_COL],
                "favorite animal": row[FAV_ANIMAL_COL],
                "favorite artist": row[FAV_ARTIST_COL],
                "favorite movie/tv show": row[FAV_MOVIE_COL],
                "favorite bible verse": row[FAV_BIBLE_VERSE_COL],
                "favorite memory/thing about AACF": row[FAV_MEMORY_COL],
                "questions/comments/concerns": row[QQC_COL],
            }

        if len(responses) == 0:
            await interaction.response.send_message(f"No senior named {name} found.")

        embed = discord.Embed(
            title=f"Profile for {name}",
            color=discord.Color.blue(),
        )

        for person, attr in responses.items():
            embed.add_field(
                name=f"Name: {person}",
                value="\n".join(
                    f"• {question}: {resp}" for question, resp in attr.items()
                ),
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="food-allergies", description="Lists people who have food allergies"
    )
    async def food_allergies(interaction: discord.Interaction) -> None:
        response = requests.get(CSV_URL, timeout=100)

        if response.status_code != 200:
            await interaction.response.send_message("Error occurred trying to get CSV.")

        csv_data = response.content.decode("utf-8")
        csv_reader = csv.reader(csv_data.splitlines(), delimiter=",")

        responses = {}
        is_first = True
        for row in csv_reader:
            if is_first:
                is_first = False
                continue

            if row[FOOD_ALLERGY_YN_COL].lower() != "yes":
                continue

            responses[
                f"{row[FNAME_COL].capitalize()} {row[LNAME_COL].capitalize()}"
            ] = row[FOOD_ALLERGY_LIST_COL]

        embed = discord.Embed(
            title="Food Allergies",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name=f"Total: {len(responses)}",
            value="\n".join(
                f"• {name}: {allergy}" for name, allergy in sorted(responses.items())
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="rsvps-seniors", description="Lists seniors who have RSVP'd")
    async def rsvps_seniors(interaction: discord.Interaction) -> None:
        response = requests.get(CSV_URL, timeout=100)

        if response.status_code != 200:
            await interaction.response.send_message("Error occurred trying to get CSV.")

        csv_data = response.content.decode("utf-8")
        csv_reader = csv.reader(csv_data.splitlines(), delimiter=",")

        responses = defaultdict(list)
        is_first = True
        for row in csv_reader:
            if is_first:
                is_first = False
                continue

            if "senior" in row[IS_SENIOR_COL]:
                responses["seniors"].append(
                    f"{row[FNAME_COL].capitalize()} {row[LNAME_COL].capitalize()}"
                )

        embed = discord.Embed(
            title="RSVPs Seniors",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name=f"Total: {len(responses['seniors'])}",
            value="\n".join(f"• {x}" for x in sorted(responses["seniors"])),
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="rsvps", description="Lists everyone who has RSVP'd")
    async def rsvps(interaction: discord.Interaction) -> None:
        response = requests.get(CSV_URL, timeout=100)

        if response.status_code != 200:
            await interaction.response.send_message("Error occurred trying to get CSV.")

        csv_data = response.content.decode("utf-8")
        csv_reader = csv.reader(csv_data.splitlines(), delimiter=",")

        responses = defaultdict(list)
        is_first = True
        for row in csv_reader:
            if is_first:
                is_first = False
                continue

            if "senior" in row[IS_SENIOR_COL]:
                responses["seniors"].append(
                    f"{row[FNAME_COL].capitalize()} {row[LNAME_COL].capitalize()}"
                )
            else:
                responses["nonseniors"].append(
                    f"{row[FNAME_COL].capitalize()} {row[LNAME_COL].capitalize()}"
                )

        embed = discord.Embed(
            title=f"RSVPs - {len(responses['seniors']) + len(responses['nonseniors'])} total",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name=f"[{len(responses['seniors'])}] Seniors",
            value="\n".join(f"• {x}" for x in sorted(responses["seniors"])),
            inline=False,
        )

        embed.add_field(
            name=f"[{len(responses['nonseniors'])}] Non-Seniors",
            value="\n".join(f"• {x}" for x in sorted(responses["nonseniors"])),
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    # @bot.tree.command(name="fish", description="test")
    # async def fish(interaction: discord.Interaction) -> None:

    #     guild = interaction.guild
    #     member = interaction.user

    #     if guild is None:
    #         await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
    #         return

    #     role = discord.utils.get(guild.roles, name="fish")

    #     if not role:
    #         await interaction.response.send_message("Role 'fish' not found.", ephemeral=True)
    #         return

    #     if role in member.roles:
    #         await interaction.response.send_message("You already have the fish role!", ephemeral=True)
    #     else:
    #         await member.add_roles(role)
    #         await interaction.response.send_message("You have been given the 🐟 **fish** role!", ephemeral=True)

    bot.run(TOKEN)


if __name__ == "__main__":
    run()
