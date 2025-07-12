import discord
import json
import os
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging

from config.settings import id_log_channel, ALLOWED_ROLE, OWNER_USER
from libs.lbs import *

LOG_CONFIG_FILE = "data/logs_config.json"
DEFAULT_LOG_CONFIG = {
    "messages": True,
    "channels": True,
    "roles": True,
    "members": True,
    "emojis": True,
    "pins": True,
    "lang": "ru"
}

LANGS = {
    "ru": {
        "message_sent": "📥 Сообщение отправлено",
        "message_deleted": "🗑️ Сообщение удалено",
        "message_edited": "✏️ Сообщение изменено",
        "member_joined": "✅ Участник зашёл",
        "member_left": "❌ Участник вышел",
        "nickname_changed": "📝 Ник изменён",
        "role_added": "➕ Роль выдана",
        "role_removed": "➖ Роль снята",
        "member_banned": "⛔ Участник забанен",
        "member_unbanned": "♻️ Участник разбанен",
        "channel_created": "📁 Канал создан",
        "channel_deleted": "🗑️ Канал удалён",
        "channel_renamed": "✏️ Канал переименован",
        "role_created": "🔵 Роль создана",
        "role_deleted": "🔴 Роль удалена",
        "role_renamed": "✏️ Роль переименована",
        "emoji_added": "🆕 Эмодзи добавлен",
        "emoji_removed": "❌ Эмодзи удалён",
        "pins_updated": "📌 Пины обновлены",
        "log_enabled": "Логирование `{}` теперь включено.",
        "log_disabled": "Логирование `{}` теперь выключено.",
        "unknown_log_type": "Неизвестный тип лога: {}",
        "no_permission": "Нет прав для выполнения этой команды.",
        "language_set": "Язык логов теперь русский.",
        "language_set_en": "Язык логов теперь английский.",
        "log_language": "Язык логов"
    },
    "en": {
        "message_sent": "📥 Message Sent",
        "message_deleted": "🗑️ Message Deleted",
        "message_edited": "✏️ Message Edited",
        "member_joined": "✅ Member Joined",
        "member_left": "❌ Member Left",
        "nickname_changed": "📝 Nickname Changed",
        "role_added": "➕ Role Added",
        "role_removed": "➖ Role Removed",
        "member_banned": "⛔ Member Banned",
        "member_unbanned": "♻️ Member Unbanned",
        "channel_created": "📁 Channel Created",
        "channel_deleted": "🗑️ Channel Deleted",
        "channel_renamed": "✏️ Channel Renamed",
        "role_created": "🔵 Role Created",
        "role_deleted": "🔴 Role Deleted",
        "role_renamed": "✏️ Role Renamed",
        "emoji_added": "🆕 Emoji Added",
        "emoji_removed": "❌ Emoji Removed",
        "pins_updated": "📌 Pins Updated",
        "log_enabled": "Logging for `{}` is now enabled.",
        "log_disabled": "Logging for `{}` is now disabled.",
        "unknown_log_type": "Unknown log type: {}",
        "no_permission": "Sorry, no permission to execute this command.",
        "language_set": "Log language is now Russian.",
        "language_set_en": "Log language is now English.",
        "log_language": "Log language"
    }
}

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self._load_config()

    def _lang(self, key):
        lang = self.config.get("lang", "ru")
        return LANGS[lang].get(key, key)

    def _load_config(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(LOG_CONFIG_FILE):
            with open(LOG_CONFIG_FILE, "w") as f:
                json.dump(DEFAULT_LOG_CONFIG, f, indent=4)
            return DEFAULT_LOG_CONFIG.copy()
        with open(LOG_CONFIG_FILE, "r") as f:
            return json.load(f)

    def _save_config(self):
        with open(LOG_CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    async def send_log(self, guild: discord.Guild, embed: discord.Embed):
        log_channel = discord.utils.get(guild.text_channels, id=id_log_channel)
        if log_channel:
            await log_channel.send(embed=embed)

    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if not self.config.get("messages", True):
    #         return
    #     if message.author.bot:
    #         return
    #     embed = discord.Embed(
    #         title=self._lang("message_sent"),
    #         description=message.content or "[Embed/Attachment]",
    #         color=discord.Color.green(),
    #         timestamp=message.created_at
    #     )
    #     embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=True)
    #     embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    #     embed.set_footer(text=f"Message ID: {message.id}")
    #     await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not self.config.get("messages", True):
            return
        if message.author.bot:
            return
        embed = discord.Embed(
            title=self._lang("message_deleted"),
            description=message.content or "[Embed/Attachment]",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.set_footer(text=f"Message ID: {message.id}")
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.config.get("members", True):
            return
        embed = discord.Embed(
            title=self._lang("member_joined"),
            description=f"{member.mention} ({member.id})",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not self.config.get("members", True):
            return
        guild = member.guild
        # Проверяем audit log на кик
        try:
            entry = None
            async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if log.target.id == member.id and (datetime.utcnow() - log.created_at).total_seconds() < 10:
                    entry = log
                    break
            if entry:
                # Был кик
                await self.log_member_remove(member, moderator=entry.user, reason=entry.reason)
                return
        except Exception as e:
            log_message(f"Error checking kick audit log: {e}")
        # Обычный выход
        embed = discord.Embed(
            title=self._lang("member_left"),
            description=f"{member.mention} ({member.id})",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not self.config.get("members", True):
            return
        if before.nick != after.nick:
            embed = discord.Embed(
                title=self._lang("nickname_changed"),
                description=f"{after.mention} ({after.id})",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Before", value=before.nick or before.name, inline=True)
            embed.add_field(name="After", value=after.nick or after.name, inline=True)
            await self.send_log(after.guild, embed)
        if before.roles != after.roles:
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                for role in added:
                    await self.log_role_added(after, role, moderator=after)
            if removed:
                for role in removed:
                    await self.log_role_removed(after, role, moderator=after)
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                # Выдан таймаут
                guild = after.guild
                try:
                    entry = None
                    async for log in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                        if log.target.id == after.id and (datetime.utcnow() - log.created_at).total_seconds() < 60:
                            entry = log
                            break
                    moderator = entry.user if entry else None
                    reason = entry.reason if entry else None
                except Exception as e:
                    log_message(f"Error checking timeout audit log: {e}")
                    moderator = None
                    reason = None
                # Вычисляем длительность таймаута
                now = datetime.utcnow().replace(tzinfo=after.timed_out_until.tzinfo)
                duration = after.timed_out_until - now
                total_seconds = int(duration.total_seconds())
                days, remainder = divmod(total_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = (
                    (f"{days}d " if days else "") +
                    (f"{hours}h " if hours else "") +
                    (f"{minutes}m " if minutes else "") +
                    (f"{seconds}s" if seconds else "")
                ).strip()
                embed = discord.Embed(
                    title="⏳ Member timed out" if self.config.get("lang", "ru") != "ru" else "⏳ Участник получил таймаут",
                    description=f"{after.mention} ({after.id})",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Duration" if self.config.get("lang", "ru") != "ru" else "Длительность", value=duration_str, inline=False)
                embed.add_field(
                    name="Moderator" if self.config.get("lang", "ru") != "ru" else "Модератор",
                    value=f"{moderator.mention} ({moderator})" if moderator else "Unknown",
                    inline=False
                )
                if reason:
                    embed.add_field(name="Reason" if self.config.get("lang", "ru") != "ru" else "Причина", value=reason, inline=False)
                await self.send_log(after.guild, embed)
            else:
                # Снят таймаут
                guild = after.guild
                try:
                    entry = None
                    async for log in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                        if log.target.id == after.id and (datetime.utcnow() - log.created_at).total_seconds() < 60:
                            entry = log
                            break
                    moderator = entry.user if entry else None
                except Exception as e:
                    log_message(f"Error checking timeout audit log: {e}")
                    moderator = None
                embed = discord.Embed(
                    title="✅ Timeout removed" if self.config.get("lang", "ru") != "ru" else "✅ Таймаут снят",
                    description=f"{after.mention} ({after.id})",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(
                    name="Moderator" if self.config.get("lang", "ru") != "ru" else "Модератор",
                    value=f"{moderator.mention} ({moderator})" if moderator else "Unknown",
                    inline=False
                )
                await self.send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not self.config.get("members", True):
            return
        embed = discord.Embed(
            title=self._lang("member_banned"),
            description=f"{user.mention} ({user.id})",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if not self.config.get("members", True):
            return
        embed = discord.Embed(
            title=self._lang("member_unbanned"),
            description=f"{user.mention} ({user.id})",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not self.config.get("channels", True):
            return
        embed = discord.Embed(
            title=self._lang("channel_created"),
            description=f"{channel.mention} ({channel.id})",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.config.get("channels", True):
            return
        embed = discord.Embed(
            title=self._lang("channel_deleted"),
            description=f"{channel.name} ({channel.id})",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if not self.config.get("channels", True):
            return
        if before.name != after.name:
            embed = discord.Embed(
                title=self._lang("channel_renamed"),
                description=f"{before.name} → {after.name} (<#{after.id}>   {after.id})",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            await self.send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if not self.config.get("roles", True):
            return
        embed = discord.Embed(
            title=self._lang("role_created"),
            description=f"{role.mention} ({role.id})",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if not self.config.get("roles", True):
            return
        embed = discord.Embed(
            title=self._lang("role_deleted"),
            description=f"{role.name} ({role.id})",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if not self.config.get("roles", True):
            return
        if before.name != after.name:
            embed = discord.Embed(
                title=self._lang("role_renamed"),
                description=f"{before.name} → {after.name} ({after.id})",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            await self.send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        if not self.config.get("emojis", True):
            return
        before_set = set(before)
        after_set = set(after)
        added = after_set - before_set
        removed = before_set - after_set
        for emoji in added:
            embed = discord.Embed(
                title=self._lang("emoji_added"),
                description=f"{str(emoji)} ({emoji.id})",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            await self.send_log(guild, embed)
        for emoji in removed:
            embed = discord.Embed(
                title=self._lang("emoji_removed"),
                description=f"{str(emoji)} ({emoji.id})",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        if not self.config.get("pins", True):
            return
        embed = discord.Embed(
            title=self._lang("pins_updated"),
            description=f"Channel: {channel.mention} ({channel.id})\nLast pin: {last_pin}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not self.config.get("messages", True):
            return
        if before.author.bot:
            return
        if before.content == after.content:
            return
        embed = discord.Embed(
            title=self._lang("message_edited"),
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{before.author} ({before.author.id})", inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before:", value=f"```{before.content or '[Embed/Attachment]'}```", inline=False)
        embed.add_field(name="After:", value=f"```{after.content or '[Embed/Attachment]'}```", inline=False)
        embed.set_footer(text=f"Message ID: {before.id}")
        await self.send_log(before.guild, embed)

    async def log_member_remove(self, member, moderator=None, reason=None):
        embed = discord.Embed(
            title="👋 Участник выгнан." if self.config.get("lang", "ru") == "ru" else "👋 Member kicked.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        if hasattr(member, "avatar") and member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        if moderator:
            embed.add_field(
                name="Ответственный модератор:" if self.config.get("lang", "ru") == "ru" else "Responsible moderator:",
                value=f"{moderator.mention} ({moderator})",
                inline=False
            )
        if reason:
            embed.add_field(
                name="Причина:" if self.config.get("lang", "ru") == "ru" else "Reason:",
                value=reason,
                inline=False
            )
        await self.send_log(member.guild, embed)

    async def log_role_added(self, member, role, moderator=None):
        lang = self.config.get("lang", "ru")
        embed = discord.Embed(
            title="➕ Роль выдана" if lang == "ru" else "➕ Role Added",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)  # Аватар справа

        embed.add_field(
            name="Пользователь:" if lang == "ru" else "User:",
            value=f"{member.mention} ({member})",
            inline=False
        )
        embed.add_field(
            name="Роль:" if lang == "ru" else "Role:",
            value=role.mention,
            inline=False
        )
        if moderator:
            embed.add_field(
                name="Ответственный модератор:" if lang == "ru" else "Responsible moderator:",
                value=f"{moderator.mention} ({moderator})",
                inline=False
            )
        await self.send_log(member.guild, embed)

    async def log_role_removed(self, member, role, moderator=None):
        lang = self.config.get("lang", "ru")
        embed = discord.Embed(
            title="➖ Роль снята" if lang == "ru" else "➖ Role Removed",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Пользователь:" if lang == "ru" else "User:",
            value=f"{member.mention} ({member})",
            inline=False
        )
        embed.add_field(
            name="Роль:" if lang == "ru" else "Role:",
            value=role.mention,
            inline=False
        )
        if moderator:
            embed.add_field(
                name="Ответственный модератор:" if lang == "ru" else "Responsible moderator:",
                value=f"{moderator.mention} ({moderator})",
                inline=False
            )
        await self.send_log(member.guild, embed)

    @app_commands.command(name="log_settings", description="Enable or disable specific log types.")
    @app_commands.describe(
        log_type="Log type (messages, channels, roles, members, emojis, pins)",
        enabled="Enable or disable log (true/false)"
    )
    async def log_settings(self, interaction: discord.Interaction, log_type: str, enabled: bool):
        if not check_permissions(interaction):
            await send_message(interaction, self._lang("no_permission"), True)
            return
        if log_type not in self.config:
            await send_message(interaction, self._lang("unknown_log_type").format(log_type), True)
            return
        self.config[log_type] = enabled
        self._save_config()
        status = self._lang("log_enabled" if enabled else "log_disabled").format(log_type)
        await send_message(interaction, status, True)

    @log_settings.autocomplete('log_type')
    async def log_type_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = [
            app_commands.Choice(name=key, value=key)
            for key in self.config.keys() if key != "lang" and current.lower() in key.lower()
        ]
        return choices[:25]

    @app_commands.command(name="log_language", description="Set log language (ru/en)")
    @app_commands.describe(
        lang="Log language: ru (Russian) or en (English)"
    )
    async def log_language(self, interaction: discord.Interaction, lang: str):
        if not check_permissions(interaction):
            await send_message(interaction, self._lang("no_permission"), True)
            return
        if lang not in ("ru", "en"):
            await send_message(interaction, "ru / en", True)
            return
        self.config["lang"] = lang
        self._save_config()
        await send_message(interaction, self._lang("language_set") if lang == "ru" else self._lang("language_set_en"), True)

    @log_language.autocomplete('lang')
    async def lang_autocomplete(self, interaction: discord.Interaction, current: str):
        langs = [
            app_commands.Choice(name="Русский", value="ru"),
            app_commands.Choice(name="English", value="en")
        ]
        return [l for l in langs if current.lower() in l.name.lower() or current.lower() in l.value.lower()]

    @app_commands.command(name="console_logs", description="Send the bot's console log file")
    async def console_logs(self, interaction: discord.Interaction):
        if interaction.user.id in OWNER_USER:
            log_file = "data/logs.txt"
            if not os.path.exists(log_file):
                await send_message(interaction, "Файл лога не найден.", True)
                return

            await interaction.response.defer()
            file = discord.File(log_file, filename="console_log.txt")
            await interaction.followup.send("Лог консоли:", file=file)

            try:
                open(log_file, 'w').close()
            except Exception as e:
                await send_message(interaction, f"Не удалось очистить файл: {e}", True)
        else:
            await send_message(interaction, self._lang("no_permission"), True)

async def setup(bot):
    await bot.add_cog(Logs(bot))
