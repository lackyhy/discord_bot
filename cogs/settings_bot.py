import discord
import os
import json
from discord import app_commands
from discord.ext import commands
from libs.lbs import *
from config.settings import ALLOWED_ROLE

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '../config/settings.py')

# def load_settings():
#     import importlib.util
#     spec = importlib.util.spec_from_file_location("settings", SETTINGS_PATH)
#     settings = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(settings)
#     return settings.SETTINGS

def save_settings(settings_dict):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write("SETTINGS = " + json.dumps(settings_dict, ensure_ascii=False, indent=4))

def set_logs_language(lang):
    import json
    path = os.path.join(os.path.dirname(__file__), '../data/logs_config.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    config['lang'] = lang
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def set_allowed_roles(new_ids):
    settings_path = os.path.join(os.path.dirname(__file__), '../config/settings.py')
    with open(settings_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(settings_path, "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip().startswith("ALLOWED_ROLE"):
                f.write(f'ALLOWED_ROLE = {new_ids}\n')
            else:
                f.write(line)

class SettingsView(discord.ui.View):
    def __init__(self, bot, interaction):
        super().__init__(timeout=120)
        self.bot: commands.Bot = bot
        self.interaction = interaction
        # self.settings = load_settings()

    @discord.ui.button(label='Показать язык', style=discord.ButtonStyle.blurple, row=0)
    async def show_language(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = get_bot_language()
        await interaction.response.send_message(f"Текущий язык: `{lang}`", ephemeral=True)

    @discord.ui.button(label='Сменить на RU', style=discord.ButtonStyle.green, row=0)
    async def set_ru(self, interaction: discord.Interaction, button: discord.ui.Button):
        set_bot_language('ru')
        set_logs_language('ru')
        await interaction.response.send_message("Язык изменён на RU", ephemeral=True)

    @discord.ui.button(label='Сменить на EN', style=discord.ButtonStyle.green, row=0)
    async def set_en(self, interaction: discord.Interaction, button: discord.ui.Button):
        set_bot_language('en')
        set_logs_language('en')
        await interaction.response.send_message("Language set to EN", ephemeral=True)

    @discord.ui.button(label='Показать id ролей доступа', style=discord.ButtonStyle.blurple, row=1)
    async def show_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"ID ролей доступа: `{ALLOWED_ROLE}`", ephemeral=True)

    @discord.ui.button(label='Изменить id ролей', style=discord.ButtonStyle.red, row=1)
    async def change_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeRolesModal(self))

class ChangeRolesModal(discord.ui.Modal, title="Изменить id ролей доступа"):
    ids = discord.ui.TextInput(label="ID ролей (через запятую)", style=discord.TextStyle.short, required=True)
    def __init__(self, view):
        super().__init__()
        self.view = view
    async def on_submit(self, interaction: discord.Interaction):
        try:
            ids = [int(x.strip()) for x in self.ids.value.split(',') if x.strip().isdigit()]
            set_allowed_roles(ids)
            await interaction.response.send_message(f"ID ролей доступа обновлены: {ids}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка: {e}", ephemeral=True)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='settings', description='Интерактивные настройки бота')
    async def settings(self, interaction: discord.Interaction):
        allowed_roles = ALLOWED_ROLE
        if not any(role.id in allowed_roles for role in interaction.user.roles):
            await send_message(interaction, "Нет прав для просмотра/изменения настроек", ephemeral=True)
            return
        emb = discord.Embed(
            title='Настройки бота',
            description='Используйте кнопки ниже для просмотра и изменения настроек.',
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=emb, view=SettingsView(self.bot, interaction), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot))
