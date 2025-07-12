import random
import discord.embeds
import requests
import qrcode

from io import BytesIO
from discord import app_commands
from discord.ext import commands

from libs.lbs import *
from libs.lbs import get_bot_language


class AllHuman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_count = {}
        self.magic_shield = {}
        self.random_emojis = {}

    async def apply_magic_effects(self, message):
        user_id = str(message.author.id)

        # Check for sparkle effect
        if user_id in self.message_count and self.message_count[user_id] > 0:
            await message.add_reaction("✨")
            self.message_count[user_id] -= 1
            if self.message_count[user_id] == 0:
                del self.message_count[user_id]

        # Check for magic shield
        if user_id in self.magic_shield:
            # If user has magic shield, remove it after first use
            del self.magic_shield[user_id]
            await message.channel.send(f"✨ {message.author.mention} used magic shield!", delete_after=5)

        # Check for random emoji effect
        if user_id in self.random_emojis and self.random_emojis[user_id]["count"] > 0:
            emoji = random.choice(self.random_emojis[user_id]["emojis"])
            await message.add_reaction(emoji)
            self.random_emojis[user_id]["count"] -= 1
            if self.random_emojis[user_id]["count"] == 0:
                del self.random_emojis[user_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.apply_magic_effects(message)

    @app_commands.command(name="help", description="Show available commands")
    async def help(self, interaction: discord.Interaction):
        try:
            lang = get_bot_language()
            title = "Доступные команды" if lang == "ru" else "Available Commands"
            desc = "Список доступных команд:" if lang == "ru" else "List of available commands:"
            emb = discord.Embed(
                title=title,
                description=desc,
                color=discord.Color.blue()
            )

            # Basic commands for all users
            emb.add_field(
                name="👤 Basic Commands",
                value="""
                `/userinfo` - Get information about a user
                `/serverinfo` - Get information about the server
                `/avatar` - Get user's avatar
                `/ping` - Check bot's latency
                `/generate_password` - Generate a random password
                `/crypto` - Get current price of specified cryptocurrency or top 20 cryptocurrencies
                `/qrcode` - Get QR code on link
                `/cat` - cat
                `/userinfo` - Get information about a user
                `/serverinfo` - Get information about the server
                `/roll` - roll 
                `/magicball` - magic ball
                `/magic` - Cast a magic spell and get random effects
                `/rank` - Shows your current level and XP
                `/leaderboard` - Shows the leaderboard
                `/level` - Shows detailed information about your level
                """,
                inline=False
            )
            if check_permissions(interaction):
                emb.add_field(
                    name="🛡️ Moderator Commands (User Management)",
                    value="""
                    • `/kick` - Kick a user from the server
                    • `/ban` - Ban a user from the server
                    • `/unban` - Unban a user
                    • `/banlist` - Show list of banned users
                    • `/mute` - Mute a user (timeout)
                    • `/unmute` - Remove user's mute
                    """,
                    inline=False
                )
                emb.add_field(
                    name="🛡️ Moderator Commands (Role Management)",
                    value="""
                    • `/add_role` - Add a role to a user
                    • `/remove_role` - Remove a role from a user
                    """,
                    inline=False
                )
                emb.add_field(
                    name="🛡️ Moderator Commands (Channel Management)",
                    value="""
                    • `/clear` - Clear specified number of messages
                    • `/clear_all` - Clear all messages in channel
                    • `/lock_channel` - Lock and hide a channel
                    • `/unlock_channel` - Unlock and show a channel
                    """,
                    inline=False
                )
                emb.add_field(
                    name="🛡️ Moderator Commands (Usage Notes)",
                    value="""
                    • Most commands require a reason parameter
                    • Time format for mute: `1s`, `5m`, `1h`, `1d`, `1w`
                    • Channel commands can target specific channel or use current
                    • All actions are logged and visible to moderators
                    """,
                    inline=False
                )

            emb.set_footer(text=f"Requested by {interaction.user}")
            await send_message(interaction, embed=emb, ephemeral=True)
            log_message(f"Help requested by {interaction.user}")
        except Exception as e:
            log_message(e, "ERROR")


    @app_commands.command(name="userinfo", description="Get information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        roles = [role.mention for role in target.roles[1:]]
        roles.reverse()

        emb = discord.Embed(
            title=f"User Information - {target}",
            color=target.color
        )
        emb.set_thumbnail(url=target.display_avatar.url)
        emb.add_field(name="ID", value=target.id, inline=True)
        emb.add_field(name="Nickname", value=target.nick or "None", inline=True)
        emb.add_field(name="Account Created", value=target.created_at.strftime("%Y-%m-%d"), inline=True)
        emb.add_field(name="Joined Server", value=target.joined_at.strftime("%Y-%m-%d"), inline=True)
        emb.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles) if roles else "None", inline=False)

        await send_message(interaction, embed=emb)
        log_message(f"User info requested for {target} by {interaction.user}")

    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        emb = discord.Embed(
            title=f"Server Information - {guild.name}",
            color=discord.Color.blue()
        )

        if guild.icon:
            emb.set_thumbnail(url=guild.icon.url)

        emb.add_field(name="Server ID", value=guild.id, inline=True)
        emb.add_field(name="Owner", value=guild.owner.mention, inline=True)
        emb.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        emb.add_field(name="Member Count", value=guild.member_count, inline=True)
        emb.add_field(name="Channel Count", value=len(guild.channels), inline=True)
        emb.add_field(name="Role Count", value=len(guild.roles), inline=True)

        await send_message(interaction, emb)
        log_message(f"Server info requested by {interaction.user}")

    @app_commands.command(name="avatar", description="Get user's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        emb = discord.Embed(
            title=f"Avatar - {target}",
            color=target.color
        )
        emb.set_image(url=target.display_avatar.url)

        await send_message(interaction, emb)
        log_message(f"Avatar requested for {target} by {interaction.user}")

    @app_commands.command(name="ping", description="Check bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        emb = discord.Embed(
            title="Pong! 🏓",
            description=f"Bot Latency: {latency}ms",
            color=discord.Color.green()
        )
        await send_message(interaction, emb, True)
        log_message(f"Ping checked by {interaction.user}")

    @app_commands.command(name="generate_password", description="Generate a random password")
    async def password(self, interaction: discord.Interaction, length: int):
        try:
            import random
            characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()'
            pwd = ''.join(random.choice(characters) for _ in range(length))
            await send_message(interaction,'password:**```{pwd}```**', True)
        except Exception as e:
            await send_message(interaction, f'Error: **```{e}```**', True)

    @app_commands.command(name="crypto", description="Get current price of specified cryptocurrency or top 20 cryptocurrencies")
    async def crypto(self, interaction: discord.Interaction, currency: str = None):
        def get_crypto_data():
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
            response = requests.get(url)
            data = response.json()
            return data[:20]

        if currency:
            response = requests.get(f'https://api.coinbase.com/v2/prices/{currency.upper()}-USD/spot')
            data = response.json()

            # Format message with current cryptocurrency price
            await send_message(interaction, "Current price of **{currency.upper()}** = **{data['data']['amount']} USD**")
        else:
            data = get_crypto_data()

            # Format message with top 20 cryptocurrencies information
            message_text = "```css\nTop 20 cryptocurrencies by market capitalization:\n\n"
            for i, coin in enumerate(data):
                message_text += f"{i + 1}. {coin['name']} ({coin['symbol'].upper()}): ${coin['current_price']:.2f}\n"
            message_text += "```"

            await send_message(interaction, message_text)

    @app_commands.command(name="userinfo", description="Info in user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        emb = discord.Embed(title=f"**Info in user: {member} **")
        emb.add_field(name="ID", value=member.id, inline=True)
        emb.add_field(name="Name", value=member.name, inline=True)
        emb.add_field(name="Status", value=member.status, inline=True)
        emb.add_field(name="created", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
        emb.add_field(name="Joined", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
        emb.set_thumbnail(url=member.display_avatar.url)
        await send_message(interaction, embed=emb)

    @app_commands.command(name="cat", description="Get cat")
    async def cat(self, interaction: discord.Interaction):
        url = 'https://api.thecatapi.com/v1/images/search'
        headers = {'x-api-key': 'YOUR_API_KEY'}
        response = requests.get(url, headers=headers)
        data = response.json()

        if data:
            cat_data = data[0]
            cat_image_url = cat_data['url']
            rand_color = '0x%06x' % random.randint(0, 0xFFFFFF)

            embed = discord.Embed(title='Котик)', color=int(rand_color, 16))
            embed.set_image(url=cat_image_url)

            await send_message(interaction, embed=embed)
        else:
            await send_message(interaction, "No cat, ERROR")

    @app_commands.command(name="qrcode", description="Get QR code on link")
    async def qrcode(self, interaction: discord.Interaction, url: str):
        import os
        def generate_qrcode(url):
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            # Сохранение QR-кода в BytesIO
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, "PNG")
            buffer.seek(0)

            return buffer

        qrcode_dir = "qrcode"
        if not os.path.exists(qrcode_dir):
            os.makedirs(qrcode_dir)

        qr_code_buffer = generate_qrcode(url)
        file_path = os.path.join(qrcode_dir, "qrcode.png")
        with open(file_path, "wb") as f:
            f.write(qr_code_buffer.getvalue())

        file = discord.File(file_path)
        await send_message(interaction, file=file)

    @app_commands.command(name="roll")
    async def roll(self, interaction: discord.Interaction, number: int = None):
        try:
            if number is None:
                await send_message(interaction, f"**1-100**: ```{random.randint(1, 101)}``` ")
            else:
                await send_message(interaction, f"**1-100**: ```{random.randint(1, number+1)}``` ")
        except Exception as e:
            log_message(e, "ERROR")

    @app_commands.command(name="magicball")
    async def magicball(self, interaction: discord.Interaction, question: str):
        answer = [
        "Yes", "Definitely yes", "Without a doubt", "Probably", "No", "Unlikely", "Doubtful", "Definitely not", "Ask later", "Can't say now", "Possibly", "Answer unclear"
        ]
        an = random.choice(answer)
        emb = discord.Embed(
            title="magicball",
            description=f"Question: **{question}**\nAnswer: **{an}**"
        )
        await send_message(interaction, emb, True)

    @app_commands.command(name="magic", description="Cast a magic spell and get random effects")
    async def magic(self, interaction: discord.Interaction, language: str = "en"):
        # Check cooldown
        can_use, remaining_time = await self.check_cooldown(interaction.user.id)
        if not can_use:
            formatted_time = await self.format_cooldown_time(remaining_time)
            message = {
                "en": f"⏳ You can use magic again in {formatted_time}",
                "ru": f"⏳ Вы сможете использовать магию снова через {formatted_time}"
            }
            await send_message(interaction, message[language], ephemeral=True)
            return

        effects = {
            "en": {
                1: "You are enchanted! Cannot write messages for 5 minutes (just kidding).",
                2: "Magic bonus! You get +10 experience points",
                3: "Magical light surrounds you - all your messages will be highlighted with emoji ✨.",
                4: "You summoned a magic dice - roll again!",
                5: "You received magical emojis - your next messages will be decorated with random emojis!"
            },
            "ru": {
                1: "Ты заколдован! На 5 минут не можешь писать сообщения (шутка).",
                2: "Волшебный бонус! Получаешь +10 очков опыта",
                3: "Магический свет вокруг тебя - все твои сообщения будут подсвечены эмодзи ✨.",
                4: "Ты вызвал магический кубик - бросай ещё раз!",
                5: "Ты получил волшебные эмодзи - твои следующие сообщения будут украшены случайными эмодзи!"
            }
        }

        effect_number = random.randint(1, len(effects["en"]))
        effect = effects[language][effect_number]

        embed = discord.Embed(
            title="✨ Magic Effect ✨" if language == "en" else "✨ Магический эффект ✨",
            description=f"{interaction.user.mention}, {effect}",
            color=discord.Color.purple()
        )

        user_id = str(interaction.user.id)

        # Add special handling for each effect
        if effect_number == 2:  # XP bonus
            try:
                # Add 10 XP to the user
                leveled_up, new_level = await self.bot.update_user_xp(interaction.user.id, 10)
                xp_message = {
                    "en": "+10 XP added to your score!" + (f"\n🎉 Congratulations! You reached level {new_level}!" if leveled_up else ""),
                    "ru": "+10 XP добавлено к вашему счету!" + (f"\n🎉 Поздравляем! Вы достигли уровня {new_level}!" if leveled_up else "")
                }
                embed.add_field(
                    name="🎯 Experience" if language == "en" else "🎯 Опыт",
                    value=xp_message[language],
                    inline=False
                )
            except Exception as e:
                error_message = {
                    "en": "Failed to add experience. Please try again later.",
                    "ru": "Не удалось добавить опыт. Пожалуйста, попробуйте позже."
                }
                embed.add_field(
                    name="❌ Error" if language == "en" else "❌ Ошибка",
                    value=error_message[language],
                    inline=False
                )
        elif effect_number == 3:  # Sparkle effect
            # Add sparkle emoji to the next 5 messages
            self.message_count[user_id] = 5
            effect_message = {
                "en": "Your next 5 messages will be highlighted with ✨ emoji",
                "ru": "Ваши следующие 5 сообщений будут подсвечены эмодзи ✨"
            }
            embed.add_field(
                name="✨ Effect" if language == "en" else "✨ Эффект",
                value=effect_message[language],
                inline=False
            )
        elif effect_number == 4:  # Magic dice
            number = random.randint(1, 6)
            result_message = {
                "en": f"Rolled: {number}",
                "ru": f"Выпало: {number}"
            }
            embed.add_field(
                name="🎲 Result" if language == "en" else "🎲 Результат",
                value=result_message[language],
                inline=False
            )
        elif effect_number == 5:  # Random emoji effect
            # Add random emojis to the next 5 messages
            emojis = ["🌟", "💫", "⭐", "🎉", "🎊", "🎈", "🎁", "🎀", "💝", "💖", "💕", "💞", "💓", "💗", "💘"]
            self.random_emojis[user_id] = {
                "count": 5,
                "emojis": emojis
            }
            gift_message = {
                "en": "Your next 5 messages will be decorated with random emojis!",
                "ru": "Ваши следующие 5 сообщения будут украшены случайными эмодзи!"
            }
            embed.add_field(
                name="🎁 Gift" if language == "en" else "🎁 Подарок",
                value=gift_message[language],
                inline=False
            )

        # Add cooldown information to the embed
        footer_text = {
            "en": "⏳ Next magic use will be available in 30 minutes",
            "ru": "⏳ Следующее использование магии будет доступно через 30 минут"
        }
        embed.set_footer(text=footer_text[language])

        await send_message(interaction, embed=embed)


async def setup(bot):
    await bot.add_cog(AllHuman(bot))

