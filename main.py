import discord, peewee, random, shutil, os
from discord.ext import commands
import database
from models.voter import Voter
from string import ascii_letters, digits
from dotenv import dotenv_values

bot = commands.Bot(command_prefix="+", intents=discord.Intents.all())


config = dotenv_values(".env")


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


@bot.tree.command(name="vote", description="Submit your ballot!")
@discord.app_commands.dm_only()
async def vote(interaction: discord.Interaction, ballot: discord.Attachment):
    if (
        ballot.filename.split(".")[-1] == "png"
        or ballot.filename.split(".")[-1] == "pdf"
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
            content="I only accept `.png` or `.pdf` files.\n\nYou can use [this tool](https://cloudconvert.com/jpg-to-png) to convert any image to a PNG if you need.",
            ephemeral=True,
        )


counters = [
    458672342885859359,  # mint
    891289393095131206,  # mad
    # 1191850547138007132,  # val (for debugging)
]


@bot.tree.command(
    name="zip", description="(COUNTER ONLY) Sends a ZIP file of all the ballots."
)
async def zip(interaction: discord.Interaction):
    if interaction.user.id in counters:
        await interaction.response.defer(ephemeral=True)
        name = "".join(random.choices(ascii_letters + digits, k=10))
        arc = shutil.make_archive(f"ballot-zips/{name}", "zip", "ballots")

        channel = bot.get_guild(1195698082797592577).get_channel(1269131011489402921)
        await channel.send(file=discord.File(arc))

        await interaction.followup.send(content="Sent to ballots channel!")
    else:
        await interaction.response.send_message(
            content="You're not allowed to do this!", ephemeral=True
        )


bot.run(config["DISCORD_TOKEN"])
