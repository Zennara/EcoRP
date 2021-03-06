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

async def payUsers():
  while True:
    await asyncio.sleep(3600)
    for guild in bot.guilds:
      if not db[str(guild.id)]["bankrupt"]:
        for userID in db[str(guild.id)]["users"]:
          if db[str(guild.id)]["users"][userID]["job"] != "none":
           db[str(guild.id)]["users"][userID]["bal"] += db[str(guild.id)]["jobs"][db[str(guild.id)]["users"][userID]["job"]][1]

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
    discord.SelectOption(label='General', value="General", description='View this for general ands server commands', emoji="❓"),
    discord.SelectOption(label='Jobs', value="Jobs", description='Commands related to jobs', emoji="🧑‍🏭"),
    discord.SelectOption(label='Bank', value="Bank", description='Commands related to money', emoji="💸")
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
        `/clear` - Clears everyone's money and jobs (CANNOT BE UNDONE)
        `/teller` - Add the lowest role in the server heirarchy to perform mod commands
        """
    elif select.values[0] == "Jobs":
      text = """
      These are the commands related to jobs. Salary for jobs is paid hourly.
    
      **Commands**
      `/positions` - Show all the active jobs on the server
      `/job` - Show your current job

      """
      if staff(interaction):
        text += """
        **Mod Commands**
        `/hire` - Give someone a job
        `/fire` - Remove someone's job
        `/createjob` - Create a new job
        `/deletejob` - Remove a job
        """
    elif select.values[0] == "Bank":
      text = """
      These are all the commands related to money, including bank commands.
    
      **Commands**
      `/pay` - Give money to another user
      `/balance` - View your current balance

      """
      if staff(interaction):
        text += """
        **Mod Commands**
        `/bankruptcy` - Stop the hourly payments
        `/inflate` - Add money from a user
        `/tax` - Remove money from a user
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
    Some general things to know as a server mod. Ensure anyone you wish to have moderating permissions like printing money and taxing by setting up the `/teller` role. Anybody with this role or higher in the role heirarchy will be able to use server and bot managing commands. Only give this to trusted moderators or admins, if at all.
    """
  embed = discord.Embed(color=0x00FF00,description=helpText)
  embed.set_footer(text="_______________________\nMade By Zennara#8377\nSelect an module for extensive help", icon_url=ctx.guild.get_member(bot.user.id).display_avatar.url)
  #reply message
  await ctx.respond(embed=embed, view=helpClass())

  
#<-----------------------COMMANDS----------------------->
@bot.slash_command(description="Clear the database",guild_ids=guild_ids)
@permissions.is_owner()
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

@bot.slash_command(description="Show your current job",guild_ids=guild_ids)
async def job(ctx, user:Option(discord.Member, "The member to view their job", required=False, default=None)):
  if user == None:
    user = ctx.author
  if str(user.id) in db[str(ctx.guild.id)]["users"]:
    u = db[str(ctx.guild.id)]["users"][str(user.id)]["job"]
    jobTitle = u
    if jobTitle != "none":
      jobDesc = db[str(ctx.guild.id)]["jobs"][u][0]
      salary = db[str(ctx.guild.id)]["jobs"][u][1]
    else:
      jobTitle = "No Current Job"
      jobDesc = "No Job Description"
      salary = "0"
  else:
    jobTitle = "No Current Job"
    jobDesc = "No Job Description"
    salary = "0"
  embed = discord.Embed(title=f"{jobTitle}", description=f"{jobDesc}", color=0x00FF00)
  embed.set_author(name=f"{user.display_name}", icon_url=user.display_avatar.url)
  embed.set_footer(text=f"{salary}💸 / hour")
  await ctx.respond(embed=embed)

@bot.slash_command(description="Sets a user's job",guild_ids=guild_ids)
async def hire(ctx, user:Option(discord.Member, "The member to give the job", required=True), job:Option(str, "The name of the job. If it doesn't exist a job will be created for you.", required=True)):
  if staff(ctx):
    info = ""
    if job not in db[str(ctx.guild.id)]["jobs"]:
      db[str(ctx.guild.id)]["jobs"][job] = ["No Description Provided",0.0]
      info = "Job automatically created. Use `/edit job` to edit the job's description and salary.\n"
    checkUser(user)
    oldJob = db[str(ctx.guild.id)]["users"][str(user.id)]["job"]
    if db[str(ctx.guild.id)]["users"][str(user.id)]["job"] != "none":
      addition = f"'s job was switched from **{oldJob}** to **{job}**"
    else:
      addition = f" was given the job **{job}**"
    db[str(ctx.guild.id)]["users"][str(user.id)]["job"] = job
    await confirm(ctx, f"{info}{user.mention} {addition}", False)
  else:
    await error(ctx, "You do not have valid permissions")

@bot.slash_command(description="Remove a user's job",guild_ids=guild_ids)
async def fire(ctx, user:Option(discord.Member, "The member to remove from their job", required=True)):
  if staff(ctx):
    if str(user.id) in db[str(ctx.guild.id)]["users"]:
      job = db[str(ctx.guild.id)]["users"][str(user.id)]["job"]
      if job != "none":
        db[str(ctx.guild.id)]["users"][str(user.id)]["job"] = "none"
        await confirm(ctx, f"{user.mention} was fired from their job, **{job}**", False)
      else:
        await error(ctx, "User is unemployed")
    else:
      await error(ctx, "User is unemployed")
  else:
    await error(ctx, "You do not have valid permissions")

@bot.slash_command(description="Create a new job",guild_ids=guild_ids)
async def createjob(ctx, title:Option(str, "The title of the job", required=True), salary:Option(float, "The salary for this job per hour", required=True), description:Option(str, "The description of this job", required=False, default=None)):
  if staff(ctx):
    if description == None:
      description = "No Description Provided"
    if title not in db[str(ctx.guild.id)]["jobs"]:
      db[str(ctx.guild.id)]["jobs"][title] = [description,salary]
      await confirm(ctx, f"The job, `{title}`, was created. Assign users to it with `/hire`", True)
    else:
      await error(ctx, f"This job already exists.")
  else:
    await error(ctx, "You do not have valid permissions")

@bot.slash_command(description="Create a new job",guild_ids=guild_ids)
async def deletejob(ctx, title:Option(str, "The title of the job", required=True)):
  checkGuild(ctx.guild)
  if staff(ctx):
    if title in db[str(ctx.guild.id)]["jobs"]:
      del db[str(ctx.guild.id)]["jobs"][title]
      for user in db[str(ctx.guild.id)]["users"]:
        if db[str(ctx.guild.id)]["users"][user]["job"] == title:
          db[str(ctx.guild.id)]["users"][user]["job"] = "none"
      await confirm(ctx, f"The job, `{title}`, was deleted. All users with this job were fired.", True)
    else:
      await error(ctx, f"This job does not exist")
  else:
    await error(ctx, "You do not have valid permissions")

@bot.slash_command(description="View all the active jobs in the server",guild_ids=guild_ids)
async def positions(ctx):
  await ctx.defer()
  desc = ""
  if db[str(ctx.guild.id)]["jobs"]:
    for job in db[str(ctx.guild.id)]["jobs"]:
      count = 0
      for worker in db[str(ctx.guild.id)]["users"]:
        if  db[str(ctx.guild.id)]["users"][worker]["job"] == job:
          count += 1
      pay = db[str(ctx.guild.id)]["jobs"][job][1]
      desc += f"**{job}** | **{count}** employees | **{pay}** 💸 / hour\n"
    embed = discord.Embed(description=desc)
    embed.set_author(name=f"{ctx.guild.name}'s Jobs", icon_url=ctx.guild.icon.url)
    await ctx.respond(embed=embed)
  else:
    await error(ctx, "This guild has no jobs at this time")

@bot.slash_command(description="Change the lowest staff role", guild_ids=guild_ids)
@permissions.is_owner()
async def teller(ctx, role:Option(discord.Role, "The lowest role in the heirarchy for bank commands", required=True)):
  db[str(ctx.guild.id)]["mod"] = int(role.id)
  await confirm(ctx, f"The lowest role in the heirarchy for bank commands is now {role.mention}", True)

@bot.slash_command(description="View your current balance", guild_ids=guild_ids)
async def balance(ctx, user:Option(discord.Member, "The user to view their balance", required=False, default=None)):
  if user == None:
    user = ctx.author
  if str(user.id) in db[str(ctx.guild.id)]["users"]:
    bal = db[str(ctx.guild.id)]["users"][str(user.id)]["bal"]
  else:
    bal = 0
  await confirm(ctx, f"{user.mention}'s balance is {bal} 💸", True)

@bot.slash_command(description="Stop the hourly payments", guild_ids=guild_ids)
async def bankuptcy(ctx):
  set = not db[str(ctx.guild.id)]["bankrupt"]
  if set:
    flag = "now bankrupt.\nHourly wages will **not** be paid"
  else:
    flag = "no longer bankrupt.\nHourly wages will **now** be paid"
  db[str(ctx.guild.id)]["bankrupt"] = set
  await confirm(ctx, f"The server is {flag}", False)
  

@bot.slash_command(description="Inflate money of another user", guild_ids=guild_ids)
async def inflate(ctx, amount:Option(float, "The amount of money to print", required=True), user:Option(discord.Member, "The member you wish to inflate", required=False, default=None)):
  if staff(ctx):
    if user == None:
      user = ctx.author
    if amount > 0:
      checkUser(user)
      db[str(ctx.guild.id)]["users"][str(user.id)]["bal"] = db[str(ctx.guild.id)]["users"][str(user.id)]["bal"] + amount
      embed = discord.Embed(description=f"gave **{amount}** 💸 to", color=0x00FF00)
      embed.set_author(name=f"{ctx.guild.name}", icon_url=bot.user.display_avatar.url)
      embed.set_footer(text=f"{user.display_name}", icon_url=user.display_avatar.url)
      await ctx.respond(embed=embed)
    else:
      await error(ctx, "You can not print negative money")
  else:
    await error(ctx, "You do not have the correct permissions")

@bot.slash_command(description="Remove money from a user", guild_ids=guild_ids)
async def tax(ctx, amount:Option(float, "The amount of money to tax", required=True), user:Option(discord.Member, "The member you wish to tax", required=False, default=None)):
  if staff(ctx):
    if user == None:
      user = ctx.author
    if amount > 0:
      checkUser(user)
      db[str(ctx.guild.id)]["users"][str(user.id)]["bal"] = db[str(ctx.guild.id)]["users"][str(user.id)]["bal"] - amount
      embed = discord.Embed(description=f"taxed **{amount}** 💸 from", color=0x00FF00)
      embed.set_author(name=f"{ctx.guild.name}", icon_url=bot.user.display_avatar.url)
      embed.set_footer(text=f"{user.display_name}", icon_url=user.display_avatar.url)
      await ctx.respond(embed=embed)
    else:
      await error(ctx, "You can not tax negative money")
  else:
    await error(ctx, "You do not have the correct permissions")

@bot.slash_command(description="Give money to another user", guild_ids=guild_ids)
async def pay(ctx, user:Option(discord.Member, "The member you wish to pay", required=True), amount:Option(float, "The amount of money to give", required=True)):
  if user != ctx.author:
    if str(ctx.author.id) in db[str(ctx.guild.id)]["users"]:
      authorBal = db[str(ctx.guild.id)]["users"][str(ctx.author.id)]["bal"]
      if amount > 0:
        if authorBal >= amount:
          checkUser(user)
          db[str(ctx.guild.id)]["users"][str(ctx.author.id)]["bal"] = authorBal - amount
          db[str(ctx.guild.id)]["users"][str(user.id)]["bal"] = db[str(ctx.guild.id)]["users"][str(user.id)]["bal"] + amount
          embed = discord.Embed(description=f"gave **{amount}** 💸 to", color=0x00FF00)
          embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
          embed.set_footer(text=f"{user.display_name}", icon_url=user.display_avatar.url)
          await ctx.respond(embed=embed)
        else:
          await error(ctx, "You do not have enough money")
      else:
        await error(ctx, "You can not give an amount less than 0")
    else:
      await error("You do not have any money to give")
  else:
    await error(ctx, "You can not pay yourself")
  
  
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
  db[str(guild.id)] = {"mod":0, "bankrupt":False, "jobs":{}, "users":{}} #this is where you set up your db format

#check if a guild is in the db
def checkGuild(guild):
  if guild != None:
    if str(guild.id) not in db:
      resetDB(guild)

def checkUser(user):
  checkGuild(user.guild)
  if str(user.id) not in db[str(user.guild.id)]["users"]:
    db[str(user.guild.id)]["users"][str(user.id)] = {"job":"none", "bal":0.0}

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

#create task loops
bot.loop.create_task(payUsers())
  
#bot
keep_alive.keep_alive()  #keep the bot alive
bot.run(os.environ.get("TOKEN"))  #secret variable named 'TOKEN'