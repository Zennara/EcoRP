#general imports I almost always need for bots
import discord #pycord
import os #for token
import keep_alive #keep alive file
from replit import db #database
import requests #for rate limit checker
import random #random numbers
import asyncio #for asyncio functions
import json #to write to json
from discord.ext import commands #for commands
from discord.commands import SlashCommandGroup, Option, permissions #slash commands, options, permissions
from datetime import datetime, timedelta #time and ping command
import math #for math

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

guild_ids = [806706495466766366] #enter your guild ID's here for instant use instead of waiting for global slash registration

#api limit checker | use 'kill 1' in the shell if you get limited
r = requests.head(url="https://discord.com/api/v1")
try:
  print(f"Rate limit {int(r.headers['Retry-After']) / 60} minutes left")
except:
  print("No rate limit")

#<-----------------------HELP--------------------->
class helpClass(discord.ui.View):
  def __init__(self):
    super().__init__(timeout=None)

    bwebsite = discord.ui.Button(label='Website', style=discord.ButtonStyle.gray, url='https://www.zennara.me', emoji="<:zennara:931725235676397650>")
    self.add_item(bwebsite)
    bdiscord = discord.ui.Button(label='Discord', style=discord.ButtonStyle.gray, url='https://www.discord.gg/KUmkWVpBtR', emoji="<:bot:929180626706374656>")
    self.add_item(bdiscord)
    bdonate = discord.ui.Button(label='Donate', style=discord.ButtonStyle.gray, url='https://www.paypal.me/keaganlandfried', emoji="💟")
    self.add_item(bdonate)

  @discord.ui.select(custom_id="select-2", placeholder='View help with a specific section of commands', min_values=1, max_values=1, options=[
    discord.SelectOption(label='General', value="General", description='View this for general ands server commands', emoji="❓")
  ])
  async def select_callback(self, select, interaction):
    if select.values[0] == "General":
      text = """
      This bot uses **slash commands**. This mean all bot commands starts with `/`.
      You can find more help in my [Discord server](https://discord.gg/KUmkWVpBtR).
    
      **Commands**
      `/help` - Show the preview help page
      `/ping` - Ping the bot for it's uptime

      """
      if staff(interaction):
        text += """
        **Mod Commands**
        `/clear` - Clears the guilds database
        """
    embed = discord.Embed(color=0x00FF00,description=text, title=select.values[0])
    embed.set_footer(text="________________________\n<> Required | [] Optional\nMade By Zennara#8377")
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@bot.slash_command(description="Use me for help!",guild_ids=guild_ids, hidden=True)
async def help(ctx):
  helpText = """
  **Slash Commands**
  This bot uses **slash commands**. This mean all bot commands starts with `/`.
  You can find more help in my [Discord server](https://discord.gg/YHHvT5vWnV).
  
  """
  if staff(ctx):
    helpText += """
    **Staff Setup**
    Some general things to know as a server mod. Ensure to set up the staff role with `/staff`. Anybody with this role or higher in the role heirarchy will be able to use server and bot managing commands. Only give this to trusted moderators or admins, if at all. If t
    """
  embed = discord.Embed(color=0x00FF00,description=helpText)
  embed.set_footer(text="_______________________\nMade By Zennara#8377\nSelect an module for extensive help", icon_url=ctx.guild.get_member(bot.user.id).display_avatar.url)
  #reply message
  await ctx.respond(embed=embed, view=helpClass())

  
#<-----------------------COMMANDS----------------------->
@bot.slash_command(description="Clear the database",guild_ids=guild_ids)
async def clear(ctx):
  if staff(ctx):
    for key in db:
      del key
    resetDB(ctx.guild)
    await confirm(ctx, "Guild database cleared", True)
  else:
    await error(ctx, "You do not have the proper permissions to do this")

@bot.slash_command(description="Reset the database",guild_ids=guild_ids, default_permissions=False)
@permissions.is_user(427968672980533269)
async def reset(ctx):
  for guild in bot.guilds:
    resetDB(guild)
  await confirm(ctx, "Database was reset", True)
    
@bot.slash_command(description="Show the bot's uptime",guild_ids=guild_ids)
async def ping(ctx):
  embed = discord.Embed(color=0x00FF00, title="**Pong!**", description=f"{bot.user.name} has been online for {datetime.now()-onlineTime}!")
  await ctx.respond(embed=embed)

set = SlashCommandGroup("set", "Set user's jobs and incomes", guild_ids=guild_ids)

@set.command(name="job", description="Sets a user's job",guild_ids=guild_ids)
async def setJob(ctx, user:Option(discord.Member, "The member to give the job", required=True), job:Option(str, "The name of the job. If it doesn't exist a job will be created for you.", required=True)):
  info = ""
  if job not in db[str(ctx.guild.id)]["jobs"]:
    db[str(ctx.guild.id)]["jobs"][job] = [job,"No Description Provided",0.0]
    info = "Job automatically created. Use `/edit job` to edit the job's description and salary.\n"
  await confirm(ctx, f"{info} {user.mention} was given the job **{job}**", True)
  

bot.add_application_command(set)
  
#<-----------------------EVENTS----------------------->
@bot.event
async def on_ready():
  print(f"{bot.user.name} Online.")
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your income"))
  #set onlineTime for /ping commands 
  global onlineTime
  onlineTime = datetime.now()
  #loop through guild and check them in db
  for guild in bot.guilds:
    checkGuild(guild)

  #persistance
  #bot.add_view(helpClass())
  
@bot.event
async def on_guild_join(guild):
  checkGuild(guild)

@bot.event
async def on_message(message):
  checkGuild(message.guild)
  #dump data into a .json file for easy readability
  DUMP = True
  if DUMP:
    data2 = {}
    count = 0
    for key in db.keys():
      data2[str(key)] = db[str(key)]
      count += 1

    #ensure you have a 'database.json' file created
    with open("database.json", 'w') as f:
      json.dump(str(data2), f)
  
#<-----------------------FUNCTIONS----------------------->
#used to reset the database for a guild
def resetDB(guild):
  db[str(guild.id)] = {"mod":0, "channel":0, "jobs":{}, "users":{}} #this is where you set up your db format

#check if a guild is in the db
def checkGuild(guild):
  if guild != None:
    if str(guild.id) not in db:
      resetDB(guild)

#simple error message, passes ctx from commands
async def error(ctx, code):
  embed = discord.Embed(color=0xFF0000, description= f"❌ {code}")
  await ctx.respond(embed=embed, ephemeral=True)

#simple confirmation message, passes ctx from commands
async def confirm(ctx, code, eph): 
  embed = discord.Embed(color=0x00FF00, description= f"✅ {code}")
  await ctx.respond(embed=embed, ephemeral=eph)

def staff(ctx):
  checkGuild(ctx.guild)
  mod = db[str(ctx.guild.id)]["mod"]
  if hasattr(ctx, "author"):
    if ctx.author == ctx.author.guild.owner:
        return True
    if mod != 0:
      if ctx.guild.get_role(mod) <= ctx.author.top_role:
        return True
  else:
    if ctx.user.id == ctx.guild.owner.id:
      return True
    if mod != 0:
      if ctx.guild.get_role(mod) <= ctx.guild.get_member(ctx.user.id).top_role:
        return True
  return False

#bot
keep_alive.keep_alive()  #keep the bot alive
bot.run(os.environ.get("TOKEN"))  #secret variable named 'TOKEN'