import discord, peewee, random, shutil, os, asyncio
from discord.ext import commands
import database
from models.voter import Voter
from string import ascii_letters, digits
from dotenv import dotenv_values
from datetime import datetime
from zoneinfo import ZoneInfo

bot = commands.Bot(command_prefix="+", intents=discord.Intents.all())


config = dotenv_values(".env")


def dt_to_timestamp(dt: datetime, f: str) -> str:
    formats = ["d", "D", "t", "T", "f", "F", "R"]
    if f not in formats:
        return str(int(dt.timestamp()))
    else:
        return f"<t:{int(dt.timestamp())}:{f}>"


@bot.command()
@commands.is_owner()
@commands.dm_only()
async def sync(ctx: commands.Context):
    await ctx.send(content="Syncing...")
    await bot.tree.sync()
    await ctx.send(content="Synced.")


@bot.event
async def on_ready():
    database.db.create_tables([Voter])


@bot.command()
@commands.is_owner()
@commands.dm_only()
async def clear(ctx: commands.Context):
    # clear database
    d = Voter.select()
    for voter in d:
        voter.delete_instance()
    # clear ballots folder
    ballot_files = os.listdir(path="ballots")
    for file in ballot_files:
        file = f"ballots/{file}"
        os.remove(file)
    # clear ballot-zips folder
    ballotzips_files = os.listdir(path="ballot-zips")
    for file in ballotzips_files:
        file = f"ballot-zips/{file}"
        os.remove(file)
    await ctx.send(content="Data cleared!")


@bot.command()
@commands.is_owner()
@commands.dm_only()
async def zip(ctx: commands.Context):
    name = "".join(random.choices(ascii_letters + digits, k=10))
    arc = shutil.make_archive(f"ballot-zips/{name}", "zip", "ballots")

    channel = bot.get_guild(1195698082797592577).get_channel(1269131011489402921)
    await channel.send(file=discord.File(arc))

    await ctx.send(content="Sent!")


@bot.tree.command(name="vote", description="Submit your ballot!")
@discord.app_commands.dm_only()
async def vote(interaction: discord.Interaction, ballot: discord.Attachment):
    if (
        ballot.filename.split(".")[-1] == "png"
        or ballot.filename.split(".")[-1] == "pdf"
        or ballot.filename.split(".")[-1] == "jpeg"
        or ballot.filename.split(".")[-1] == "jpg"
    ):
        voter, created = Voter.get_or_create(user_id=interaction.user.id)
        if voter.voted:
            await interaction.response.send_message(
                content="You've already voted!", ephemeral=False
            )
        else:
            await interaction.response.defer(ephemeral=False)
            file_extension = ballot.filename.split(".")[-1]
            new_name = "".join(random.choices(ascii_letters + digits, k=10))
            new_filename = f"{new_name}.{file_extension}"

            await ballot.save(f"ballots/{new_filename}")

            voter.voted = True
            voter.save()

            await interaction.followup.send(content="Ballot submitted!")
    else:
        await interaction.response.send_message(
            content="I only accept `.jpg`, `.jpeg`, `.png`, or `.pdf` files.\n\nYou can use [this tool](https://cloudconvert.com/jpg-to-png) to convert any image to a supported format if you need.",
            ephemeral=True,
        )


poll_closes_at = datetime(2024, 8, 4, 22)


async def poll_close():
    while True:
        now = dt_to_timestamp(datetime.now("Europe/London"))
        close_at = dt_to_timestamp(poll_closes_at)

        if now == close_at:
            name = "".join(random.choices(ascii_letters + digits, k=10))
            arc = shutil.make_archive(f"ballot-zips/{name}", "zip", "ballots")

            channel = bot.get_guild(1195698082797592577).get_channel(
                1269131011489402921
            )
            await channel.send(file=discord.File(arc))


bot.run(config["DISCORD_TOKEN"])
