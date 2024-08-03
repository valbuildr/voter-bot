import discord, peewee, random
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
    await ctx.send(content="Data cleared!")


@bot.tree.command(name="vote", description="Submit your ballot!")
@discord.app_commands.dm_only()
async def vote(interaction: discord.Interaction, ballot: discord.Attachment):
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

        ballot_downloaded = await ballot.save(f"ballots/{new_filename}")

        # channel = bot.get_guild(1195698082797592577).get_channel(1269131011489402921)

        voter.voted = True
        voter.save()

        # await channel.send(file=discord.File(f"ballots/{new_filename}"))

        await interaction.followup.send(content="Ballot submitted!")


bot.run(config["DISCORD_TOKEN"])
