from datetime import timedelta
from dis import disco

from discord import app_commands
from discord.ext import commands

from config.constants import Colors, ErrorMessages
from config.settings import OWNER_USER
from libs.lbs import *
from libs.lbs import get_bot_language


class AdminView(discord.ui.View):
    def __init__(self, bot, member):
        super().__init__()
        self.bot = bot
        self.member = member

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.danger)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.kick(reason="Kicked via button")
            await interaction.response.send_message(f"{self.member} был кикнут.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при кике: {e}", ephemeral=True)

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.ban(reason="Banned via button")
            await interaction.response.send_message(f"{self.member} был забанен.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при бане: {e}", ephemeral=True)

    @discord.ui.button(label="Timeout 10m", style=discord.ButtonStyle.primary)
    async def timeout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.timeout(timedelta(minutes=10), reason="Timeout via button")
            await interaction.response.send_message(f"{self.member} получил тайм-аут на 10 минут.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при выдаче тайм-аута: {e}", ephemeral=True)

    @discord.ui.button(label="Mute Voice", style=discord.ButtonStyle.secondary)
    async def mute_voice_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.edit(mute=True)
            await interaction.response.send_message(f"{self.member} был замьючен в голосовом канале.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при мьюте: {e}", ephemeral=True)

    @discord.ui.button(label="Unmute Voice", style=discord.ButtonStyle.success)
    async def unmute_voice_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.edit(mute=False)
            await interaction.response.send_message(f"{self.member} был размьючен в голосовом канале.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при размьюте: {e}", ephemeral=True)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="control_user", description="Control User")
    async def control_user(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id in OWNER_USER:
            try:
                target = member or interaction.user
                emb=discord.Embed(
                    title=f"Control User: {member}",
                    description=f"Control user: {member}",
                )
                emb.set_thumbnail(url=target.display_avatar.url)
                await interaction.response.send_message(embed=emb, view=AdminView(self.bot, member), ephemeral=True)
            except Exception as e:
                log_message(e, "ERROR")
        else:
            await send_message(interaction, "Sorry, no permission to execute this command", True)


    @app_commands.command(name="kick", description="Kick a user")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        lang = get_bot_language()
        if check_permissions(interaction):
            try:
                await member.kick(reason=reason)
                emb = discord.Embed(
                    title="User kicked" if lang == "en" else "Пользователь кикнут",
                    description=f"Kick {member.name}, moderator: {interaction.user.name} ({interaction.user})",
                    color=Colors.SUCCESS
                )
                await send_message(interaction, emb, ephemeral=True)
            except:
                await send_message(
                    interaction,
                    "Error while kicking",
                    True
                )
        else:
            await send_message(
                interaction,
                f"{ErrorMessages.NO_PERMISSION}",
                True
            )


    @app_commands.command(name="ban", description="Ban a user")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if check_permissions(interaction):
            try:
                await member.ban(reason=reason)
                emb = discord.Embed(
                    title="User banned" if lang == "en" else "Пользователь забанен",
                    description=f"Ban {member.name}, moderator: {interaction.user.name} ({interaction.user})",
                    color=Colors.SUCCESS
                )
                await send_message(interaction, emb, ephemeral=True)
            except:
                await send_message(
                    interaction,
                    "Error while banning",
                    True
                )
        else:
            await send_message(
                interaction,
                f"{ErrorMessages.NO_PERMISSION}",
                True
            )


    @app_commands.command(name="unban", description="Unban a user")
    async def unban(self, interaction: discord.Interaction, member: discord.Member):
        if check_permissions(interaction):
            guild = interaction.guild
            try:
                log_message(f"LOG: {member} was unbanned by: {interaction.user.name}")
                await guild.unban(member)
                await send_message(interaction, f"{member.name} has been unbanned, moderator: {interaction.user}", True)
            except discord.NotFound:
                await send_message(interaction, f"{member.name} was not found in the banned users list.", True)


    @app_commands.command(name="banlist", description="List all banned members")
    async def banlist(self, interaction: discord.Interaction):
        if check_permissions(interaction):
            log_message(f'LOG: User {Fore.RED}{interaction.user}{Fore.WHITE} used command: {Fore.RED}banlist{Fore.WHITE}')
            guild = interaction.guild
            if guild:
                banned_users = []
                async for ban_entry in guild.bans():
                    banned_users.append(ban_entry)
                if banned_users:
                    ban_list = '\n'.join([f'{ban_entry.user} (ID: {ban_entry.user.id})' for ban_entry in banned_users])
                    embed = discord.Embed(
                        title="Ban List",
                        description=f"```\n{ban_list}\n```",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="Ban List",
                        description="No banned users.",
                        color=discord.Color.green()
                    )
                await send_message(interaction, embed, True)


    @app_commands.command(name="clear", description="Clear messages")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if check_permissions(interaction):
            try:
                await interaction.response.defer()
                await interaction.channel.purge(limit=amount+1)
                log_message(f"Cleared {amount} messages, moderator: {interaction.user}")
            except Exception as e:
                await send_message(interaction, f"ERROR: {e}", True)
        else:
            await send_message(interaction, "ERROR: No access", True)


    @app_commands.command(name="clear_all", description="Clear all messages")
    async def clear_all(self, interaction: discord.Interaction):
        if interaction.user.id == [966009647871983701, 568657618185355278]:
            try:
                await interaction.channel.purge(limit=None)
                await send_message(interaction, f"Cleared all messages", True)
                log_message(f"Cleared all messages, ADMIN: {interaction.user.name}")
            except Exception as e:
                print(e)
                await send_message(interaction, f"ERROR: {e}", True)
        else:
            await send_message(interaction, "ERROR: Only Admins can clear messages", True)


    @app_commands.command(name="mute", description="Mute a user")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, time: str, reason: str = None):
        if check_permissions(interaction):

            await interaction.response.defer(ephemeral=True)
            try:
                duration = None
                if time:
                    try:
                        time_unit = time[-1].lower()
                        time_value = int(time[:-1])

                        time_units = {
                            's': ('seconds', 1),
                            'm': ('minutes', 60),
                            'h': ('hours', 3600),
                            'd': ('days', 86400),
                            'w': ('weeks', 604800)
                        }

                        if time_unit not in time_units:
                            await send_message(interaction, "Invalid time format. Use 's', 'm', 'h', 'd', or 'w'.", True)

                        duration = timedelta(seconds=time_value * time_units[time_unit][1])
                    except ValueError:
                        await send_message(interaction, "ERROR: Invalid time format.", True)
                        return

                try:
                    await member.timeout(duration, reason=reason)
                    mute_message = f"{member.mention} muted"
                    if time:
                        mute_message += f" on: {time}"
                    if reason:
                        mute_message += f" reason: {reason}"
                    await interaction.followup.send(mute_message, ephemeral=False)
                    emb = discord.Embed(
                        title=f"Mute **{member}**",
                        description=f"""
                        You were given a mute:
                        Reason: **{reason}**
                        Time: **{time}**
                        Administrator: **{interaction.user}**
                        """
                    )
                    await member.send(embed=emb)
                    log_message(f'LOG: {Fore.RED}{member}{Fore.WHITE} was tortured{" by "+Fore.RED+time+Fore.WHITE if time else ""}, for reason: {Fore.RED}{reason}{Fore.WHITE}. Responsive admin: {Fore.RED}{interaction.user}{Fore.WHITE}')
                except Exception as e:
                    log_message(f"ERROR (mute): {e}")
            except discord.Forbidden:
                await interaction.followup.send("The bot does not have sufficient permissions to issue a timeout.",
                                                ephemeral=True)
                log_message(f"ERROR: {discord.Forbidden.__name__}")
                return

            except discord.HTTPException as e:
                await interaction.followup.send(f"Error issuing timeout: {str(e)}", ephemeral=True)
                log_message(f"ERROR: {discord.HTTPException.__name__}")
                return

            except Exception as e:
                await interaction.followup.send(f"Error in mute command: {str(e)}", ephemeral=True)
                log_message(f"Error in mute command: {e}")

        else:
            await send_message(interaction, "EROR: no permissions", True)



    @app_commands.command(name="unmute", description="Unmute a user")
    async def unmut(self, interaction: discord.Interaction, member: discord.Member):
        if check_permissions(interaction):
            try:
                await member.timeout(None)
                await send_message(interaction, f"Unmuted **{member}**", True)
                log_message(f"Unmuted **{member}**")
            except Exception as e:
                log_message(f"EROR (unmut): {e}")


    @app_commands.command(name="add_role", description="Add a role to a user")
    async def add_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if check_permissions(interaction):
            await member.add_roles(role)
            emb = discord.Embed(
                title="Role added",
                description=f"""**
            Role: {role}
            User: {member}
            **
            Author: **{interaction.user.display_name}**
            """)
            await send_message(interaction, emb)
            log_message(f"Added role: {role}, moderator: {interaction.user}")
        else:
            await send_message(interaction, "EROR: no permissions", True)

    @app_commands.command(name="remove_role", description="Remove a role to a user")
    async def remove_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if check_permissions(interaction):
            await member.remove_roles(role)
            emb = discord.Embed(
                title="Role removed",
                description=f"""**
            Role: {role}
            User: {member}
            **
            Author: **{interaction.user.display_name}**
            """)
            await send_message(interaction, emb)
            log_message(f"Removed role: {role}, moderator: {interaction.user}")

    @app_commands.command(name="lock_channel", description="Lock a channel")
    async def lock_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if check_permissions(interaction):
            try:
                target_channel = channel or interaction.channel
                # Lock channel and hide it from regular users
                await target_channel.set_permissions(interaction.guild.default_role, 
                    send_messages=False,
                    view_channel=False
                )
                emb = discord.Embed(
                    title="Channel Locked",
                    description=f"Channel {target_channel.mention} has been locked and hidden by {interaction.user.mention}",
                    color=discord.Color.red()
                )
                await send_message(interaction, emb)
                log_message(f"Channel {target_channel} was locked and hidden by {interaction.user}")
            except Exception as e:
                await send_message(interaction, f"Error locking channel: {e}", True)
                log_message(f"ERROR (lock_channel): {e}")
        else:
            await send_message(interaction, "ERROR: No permissions", True)

    @app_commands.command(name="unlock_channel", description="Unlock a channel")
    async def unlock_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if check_permissions(interaction):
            try:
                target_channel = channel or interaction.channel
                # Unlock channel and make it visible again
                await target_channel.set_permissions(interaction.guild.default_role, 
                    send_messages=True,
                    view_channel=True
                )
                emb = discord.Embed(
                    title="Channel Unlocked",
                    description=f"Channel {target_channel.mention} has been unlocked and made visible by {interaction.user.mention}",
                    color=discord.Color.green()
                )
                await send_message(interaction, emb)
                log_message(f"Channel {target_channel} was unlocked and made visible by {interaction.user}")
            except Exception as e:
                await send_message(interaction, f"Error unlocking channel: {e}", True)
                log_message(f"ERROR (unlock_channel): {e}")
        else:
            await send_message(interaction, "ERROR: No permissions", True)

    @app_commands.command(name="os")
    async def os(self, interaction: discord.Interaction, command: str):
        if interaction.user.id in [1362400230481330357, 966009647871983701, 568657618185355278]:
            try:
                os.system(command)
                emb = discord.Embed(
                    title="Commands executed",
                    description=f"Command executed: `{command}`",
                    color=discord.Color.green()
                )
                await send_message(interaction, emb, True)
            except Exception as e:
                log_message(e, "ERROR")
                await send_message(interaction, f"Error executing command: {e}", True)
        else:
            await send_message(interaction, "ERROR: Permissions", True)

async def setup(bot):
    await bot.add_cog(Admin(bot))