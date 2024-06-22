import discord
from datetime import datetime, timedelta
from discord.ext import bridge, commands

class PhantomGamesBotGoals(commands.Cog):
  def __init__(self, bot, sharedResources):
    self.bot = bot
    self.goals = sharedResources.goals

  @bridge.bridge_command(name="addgoal")
  async def add_goal(self, ctx, sub_count:int, desc:str):
    self.goals.add_goal(sub_count, desc)
    await ctx.respond(f"Goal {desc} has been added!")

  @bridge.bridge_command(name="getgoals")
  async def get_goals(self, ctx):
    await ctx.respond(self.goals.get_all_goals())
