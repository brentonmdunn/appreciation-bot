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

# BOT_SPAM_CHANNEL_ID = 801996449373356094
BOT_SPAM_CHANNEL_ID = 1359287733335363724


roles_dict = {
    "🎵": "worship", 
    "🎁": "gifts", 
    "🎀": "decorations", 
    "🎲": "games", 
    "🧑‍🍳": "food", 
    "🙏": "prayer", 
    "📷": "photos"
}

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
        if payload.message_id != 1362160618542469302:
            return 
        
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return  # DM or unknown guild

        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return  # Ensure it's a text channel


        member = payload.member
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                print("Member not found.")
                return

        # Check if the reaction is from a bot
        if member.bot:
            print(f"Ignoring bot reaction from {member.name}")
            return



        if str(payload.emoji) in roles_dict:
            role_name = roles_dict[str(payload.emoji)]
            role = discord.utils.get(guild.roles, name=role_name)

            if role is None:
                print(f"Role '{role_name}' not found.")
                return

            if role in member.roles:
                print("User already has the role.")
            else:
                await member.add_roles(role)
                print(f"Gave role '{role_name}' to {member.name}")





    @bot.event
    async def on_raw_reaction_remove(payload):
        if payload.message_id != 1362160618542469302:
            return 
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return  # DM or unknown guild

        channel = bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return  # Ensure it's a text channel

        member = payload.member
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                print("Member not found.")
                return

        # Skip bots
        if member.bot:
            return



        emoji = str(payload.emoji)
        if emoji in roles_dict:
            role_name = roles_dict[emoji]
            role = discord.utils.get(guild.roles, name=role_name)

            if role is None:
                print(f"Role '{role_name}' not found.")
                return

            if role in member.roles:
                await member.remove_roles(role)
                print(f"Removed role '{role_name}' from {member.name}")
            else:
                print(f"{member.name} didn't have role '{role_name}'")


    @bot.tree.command(name="help", description="Available commands for ApppreciationBot")
    async def help_bot(interaction: discord.Interaction) -> None:
        if interaction.channel_id != BOT_SPAM_CHANNEL_ID:
            await interaction.response.send_message(
                f"Bot commands can only be run in <#{BOT_SPAM_CHANNEL_ID}>",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="AppreciationBot Commands", color=discord.Color.blue()
        )

        embed.add_field(
            name="`/rsvps`", value="Lists everyone who has RSVP'd", inline=False
        )

        embed.add_field(
            name="`/rsvps-seniors`", value="Lists seniors who have RSVP'd", inline=False
        )

        embed.add_field(
            name="`/food-allergies`",
            value="Lists people who have food allergies",
            inline=False,
        )

        embed.add_field(
            name="`/profile <name>`",
            value="Lists answers to the questions that the senior put on RSVP form",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="profile",
        description="Lists answers to the questions that the senior put on RSVP form",
    )
    async def profile(interaction: discord.Interaction, name: str) -> None:
        if interaction.channel_id != BOT_SPAM_CHANNEL_ID:
            await interaction.response.send_message(
                f"Bot commands can only be run in <#{BOT_SPAM_CHANNEL_ID}>",
                ephemeral=True,
            )
            return

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
                name.lower() not in row[FNAME_COL].lower()
                and name.lower() not in row[LNAME_COL].lower()
                or "senior" not in row[IS_SENIOR_COL]
            ):
                continue

            responses[
                f"{row[FNAME_COL].capitalize().strip()} {row[LNAME_COL].capitalize().strip()}"
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
            await interaction.response.send_message(
                f"""No senior named "{name}" found."""
            )
            return

        embed = discord.Embed(
            title=f"Profile for {name}",
            color=discord.Color.blue(),
        )

        for person, attr in responses.items():
            embed.add_field(
                name=f"{person}",
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
        if interaction.channel_id != BOT_SPAM_CHANNEL_ID:
            await interaction.response.send_message(
                f"Bot commands can only be run in <#{BOT_SPAM_CHANNEL_ID}>",
                ephemeral=True,
            )
            return

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
                f"{row[FNAME_COL].capitalize().strip()} {row[LNAME_COL].capitalize().strip()}"
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
        if interaction.channel_id != BOT_SPAM_CHANNEL_ID:
            await interaction.response.send_message(
                f"Bot commands can only be run in <#{BOT_SPAM_CHANNEL_ID}>",
                ephemeral=True,
            )
            return

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
                    f"{row[FNAME_COL].capitalize().strip()} {row[LNAME_COL].capitalize().strip()}"
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
        if interaction.channel_id != BOT_SPAM_CHANNEL_ID:
            await interaction.response.send_message(
                f"Bot commands can only be run in <#{BOT_SPAM_CHANNEL_ID}>",
                ephemeral=True,
            )
            return

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
                    f"{row[FNAME_COL].capitalize().strip()} {row[LNAME_COL].capitalize().strip()}"
                )
            else:
                responses["nonseniors"].append(
                    f"{row[FNAME_COL].capitalize().strip()} {row[LNAME_COL].capitalize().strip()}"
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

    # @bot.tree.command(name="react-roles", description="Lists everyone who has RSVP'd")
    # async def react_roles(interaction: discord.Interaction) -> None:
    

    #     embed = discord.Embed(
    #         title="React for roles",
    #         color=discord.Color.blue(),
    #         description="""
    #             🎵 Worship
    #             🎁 Gifts
    #             🎀 Decorations
    #             🎲 Games
    #             🧑‍🍳 Food
    #             🙏 Prayer
    #             📷 Photos
    #         """
    #     )

    #     await interaction.response.send_message(embed=embed)

    #     sent_message = await interaction.original_response()

    #     reactions = ["🎵", "🎁", "🎀", "🎲", "🧑‍🍳", "🙏", "📷"]
    #     for reaction in reactions:
    #         await sent_message.add_reaction(reaction)


    bot.run(TOKEN)


if __name__ == "__main__":
    run()
