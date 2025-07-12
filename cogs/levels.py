import discord

from discord import app_commands
from discord.ext import commands

from config.database import Database
from libs.lbs import *
from libs.lbs import get_bot_language


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    def check_level_up(self, user_id: str) -> bool:
        user_data = self.db.get_user_level(user_id)
        if not user_data:
            return False
        
        xp, current_level = user_data
        xp_to_next_level = (current_level + 1) * 100

        if xp >= xp_to_next_level:
            self.db.update_user_level(user_id, 0, current_level + 1)
            return True
        return False
    
    @app_commands.command(name="rank", description="Shows your current level and XP")
    async def rank(self, interaction: discord.Interaction):
        lang = get_bot_language()
        user_id = str(interaction.user.id)
        user_data = self.db.get_user_level(user_id)
        
        if not user_data:
            await send_message(interaction, "You don't have any XP yet. Start chatting to earn experience!", True)
            return

        self.check_level_up(user_id)
        xp, level = self.db.get_user_level(user_id)
        xp_to_next_level = (level + 1) * 100
        
        embed = discord.Embed(
            title=f"Rank of {interaction.user.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{xp_to_next_level}", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await send_message(interaction, embed, True)


    @app_commands.command(name="leaderboard", description="Shows the leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        leaderboard_data = self.db.get_leaderboard()
        
        if not leaderboard_data:
            await send_message(interaction, "The leaderboard is empty!")
            return
        
        embed = discord.Embed(title="Leaderboard", color=discord.Color.gold())
        
        for i, (user_id, xp, level) in enumerate(leaderboard_data, 1):
            user = interaction.guild.get_member(int(user_id))
            username = user.name if user else f"User {user_id}"
            embed.add_field(
                name=f"#{i}: **\n{username}**",
                value=f"Level: **{level}** | XP: **{xp}**",
                inline=False
            )

        await send_message(interaction, embed)

    @app_commands.command(name="level", description="Shows detailed information about your level")
    async def my_level(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = self.db.get_user_level(user_id)

        if not user_data:
            await send_message(interaction, "You don't have any XP yet. Start chatting to earn experience!", True)
            return

        xp, level = user_data
        xp_to_next_level = (level + 1) * 100
        current_level_xp = level * 100
        progress = xp - current_level_xp
        progress_percentage = (progress / (xp_to_next_level - current_level_xp)) * 100

        progress_bar = "▰" * int(progress_percentage / 10) + "▱" * (10 - int(progress_percentage / 10))
        
        embed = discord.Embed(title=f"Detailed Statistics for {interaction.user.name}", color=discord.Color.green())
        embed.add_field(name="Current Level", value=str(level), inline=False)
        embed.add_field(name="Total XP", value=str(xp), inline=True)
        embed.add_field(name="To Next Level", value=f"{xp_to_next_level - xp} XP", inline=True)
        embed.add_field(name="Progress", value=f"{progress_bar} ({progress_percentage:.1f}%)", inline=False)
        
        await send_message(interaction, embed, True)

    # @app_commands.command(name="level_awards", description="Shows level rewards")
    # async def level_awards(self, interaction: discord.Interaction):
    #     emb = discord.Embed(title="Level Rewards", description="""
    #     level **50**: Access to rutracker.org and bot search 🔍
    #     level **75**: Exclusive "Active Member" role 🌟
    #     level **100**: Ability to create custom role 👑
    #     level **175**: VIP status 💎
    #     level **225**: Special "Server Legend" role 🏆
    #     level **250**: Ability to pin messages 📌
    #     level **275**: Special "Server Star" role 🌠
    #     level **300**: Right to create personal channel 🏰
    #     level **325**: Immunity to slow mode ⚡
    #     level **350**: Search IP 🔍
    #     level **375**: Exclusive "Server Guardian" title 👨‍💼
    #     level **400**: All previous rewards + special "Emperor" status 👑
    #     level **500**: Chat moderator status 🛡️
    #     level **10000**: Junior Admin role               XDDDD
    #     """)
    #     await interaction.response.send_message(embed=emb, ephemeral=True)

    def cog_unload(self):
        """Close database connection when cog is unloaded"""
        self.db.close()

async def setup(bot):
    await bot.add_cog(Levels(bot))