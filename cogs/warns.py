import json
import os

from datetime import datetime
from discord import app_commands
from discord.ext import commands

from config.constants import ErrorMessages
from libs.lbs import *
from libs.lbs import get_bot_language


class Warns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns_file = "data/warns.json"
        self._ensure_warns_file()

    def _ensure_warns_file(self):
        """Ensure the warns.json file exists"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.warns_file):
            with open(self.warns_file, "w") as f:
                json.dump({}, f)

    def _load_warns(self):
        """Load warns from JSON file"""
        try:
            with open(self.warns_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_warns(self, warns):
        """Save warns to JSON file"""
        with open(self.warns_file, "w") as f:
            json.dump(warns, f, indent=4)

    def _get_user_warns(self, user_id: str):
        """Get warns for a specific user"""
        warns = self._load_warns()
        return warns.get(str(user_id), [])

    def _add_warn(self, user_id: str, warn_type: str, reason: str, moderator_id: str):
        """Add a warn to a user"""
        warns = self._load_warns()
        if str(user_id) not in warns:
            warns[str(user_id)] = []

        warn_data = {
            "type": warn_type,
            "reason": reason,
            "moderator_id": moderator_id,
            "timestamp": datetime.now().isoformat()
        }
        warns[str(user_id)].append(warn_data)
        self._save_warns(warns)
        return len(warns[str(user_id)])

    @app_commands.command(name="warn", description="Give warn")
    @app_commands.describe(
        member="The member to warn",
        what_warn="Type of warning (Administrative or Clan)",
        reason="Reason for the warning"
    )
    async def warn(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        what_warn: str,
        reason: str
    ):
        lang = get_bot_language()
        if check_permissions(interaction):
            try:
                # Add the warn
                warn_count = self._add_warn(
                    str(member.id),
                    what_warn,
                    reason,
                    str(interaction.user.id)
                )

                # Create embed for the warning
                embed = discord.Embed(
                    title="⚠️ Warning Issued",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="User",
                    value=f"{member.mention} (`{member.id}`)",
                    inline=False
                )
                embed.add_field(
                    name="Warning Type",
                    value=what_warn.capitalize(),
                    inline=True
                )
                embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=True
                )
                embed.add_field(
                    name="Total Warnings",
                    value=f"This is warning #{warn_count}",
                    inline=False
                )
                embed.set_footer(
                    text=f"Warned by {interaction.user}",
                    icon_url=interaction.user.display_avatar.url
                )

                # Send the warning embed
                await interaction.response.send_message(embed=embed)

                # Send DM to the warned user
                try:
                    user_embed = discord.Embed(
                        title="⚠️ You have been warned",
                        description=f"You have received a warning in {interaction.guild.name}",
                        color=discord.Color.yellow(),
                        timestamp=datetime.now()
                    )
                    user_embed.add_field(
                        name="Warning Type",
                        value=what_warn.capitalize(),
                        inline=True
                    )
                    user_embed.add_field(
                        name="Reason",
                        value=reason,
                        inline=True
                    )
                    user_embed.add_field(
                        name="Total Warnings",
                        value=f"This is warning #{warn_count}",
                        inline=False
                    )
                    user_embed.set_footer(
                        text=f"Warned by {interaction.user}",
                        icon_url=interaction.user.display_avatar.url
                    )
                    await member.send(embed=user_embed)
                except:
                    pass  # User might have DMs disabled

                # Log the warning
                log_message(f"Warned {member} ({member.id}) - Type: {what_warn}, Reason: {reason}, By: {interaction.user}")

            except Exception as e:
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
                log_message(f"ERROR (warn): {e}")

    @app_commands.command(name="warn_list", description="View warnings for a user")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member = None):
        if check_permissions(interaction):
            try:
                target = member or interaction.user
                warns = self._get_user_warns(str(target.id))

                if not warns:
                    embed = discord.Embed(
                        title="No Warnings",
                        description=f"{target.mention} has no warnings.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title=f"Warnings for {target}",
                        color=discord.Color.yellow()
                    )
                    
                    for i, warn in enumerate(warns, 1):
                        moderator = interaction.guild.get_member(int(warn['moderator_id']))
                        moderator_name = moderator.name if moderator else "Unknown"
                        
                        embed.add_field(
                            name=f"Warning #{i}",
                            value=f"**Type:** {warn['type'].capitalize()}\n"
                                  f"**Reason:** {warn['reason']}\n"
                                  f"**By:** {moderator_name}\n"
                                  f"**When:** <t:{int(datetime.fromisoformat(warn['timestamp']).timestamp())}:R>",
                            inline=False
                        )

                await interaction.response.send_message(embed=embed, ephemeral=True)

            except Exception as e:
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
                log_message(f"ERROR (warnings): {e}")

    @warn.autocomplete('what_warn')
    async def warn_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        choices = [
            app_commands.Choice(name="Administrative", value="adm"),
            app_commands.Choice(name="Clan", value="clan")
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]

async def setup(bot):
    await bot.add_cog(Warns(bot))
