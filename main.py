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

    bot.run(TOKEN)


if __name__ == "__main__":
    run()
