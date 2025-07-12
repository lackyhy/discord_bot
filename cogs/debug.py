import traceback
import psutil
import subprocess
import os
import json
import time
import platform

from typing import Optional, Dict, Any
from discord.ext import commands
from discord import app_commands

from libs.lbs import *
from libs.lbs import get_bot_language

# Error messages
class ErrorMessages:
    NO_PERMISSION = "You don't have permission to use this command!"

# Our own utility functions
def format_bytes(bytes: int, total: bool = False) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}PB"

def format_time(seconds: int) -> str:
    """Format seconds to human readable time"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def update_json(filename: str, data: Any) -> None:
    """Update JSON file with data"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Simple Node class to replace voicelink.Node
class Node:
    def __init__(self, host: str, port: int, password: str, secure: bool, identifier: str):
        self._host = host
        self._port = port
        self._password = password
        self._secure = secure
        self._identifier = identifier
        self._available = False
        self._players = {}
        self._stats = NodeStats()
        self._latency = 0

    @property
    def is_connected(self) -> bool:
        return self._available

    @property
    def player_count(self) -> int:
        return len(self._players)

    @property
    def latency(self) -> float:
        return self._latency

    async def connect(self):
        # Implement connection logic here
        self._available = True
        self._latency = 50  # Simulated latency
        self._stats.uptime = int(time.time())

    async def disconnect(self):
        self._available = False

class NodeStats:
    def __init__(self):
        self.cpu_process_load = 0
        self.used = 0
        self.free = 0
        self.uptime = 0

# NodePool to replace voicelink.NodePool
class NodePool:
    _nodes: Dict[str, Node] = {}

    @classmethod
    async def create_node(cls, bot, **kwargs) -> Node:
        node = Node(**kwargs)
        cls._nodes[kwargs['identifier']] = node
        await node.connect()
        return node

class ExecuteModal(discord.ui.Modal):
    def __init__(self, code: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.code: str = code

        self.add_item(
            discord.ui.TextInput(
                label="Code Runner",
                placeholder="Input Your Code",
                style=discord.TextStyle.long,
                default=self.code
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.code = self.children[0].value
        self.stop()

class AddNodeModal(discord.ui.Modal):
    def __init__(self, view, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.view: NodesPanel = view
        
        self.add_item(
            discord.ui.TextInput(
                label="Host",
                placeholder="Enter the lavalink host e.g 0.0.0.0"
            )
        )
        self.add_item(
            discord.ui.TextInput(
                label="Port",
                placeholder="Enter the lavalink port e.g 2333"
            )
        )
        self.add_item(
            discord.ui.TextInput(
                label="Password",
                placeholder="Enter the lavalink password"
            )
        )
        self.add_item(
            discord.ui.TextInput(
                label="Secure",
                placeholder="Specify if your Lavalink uses SSL. Enter 'true' or 'false'"
            )
        )
        self.add_item(
            discord.ui.TextInput(
                label="Identifier",
                placeholder="Enter a name for your lavalink server"
            )
        )
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            config = {
                "host": self.children[0].value,
                "port": int(self.children[1].value),
                "password": self.children[2].value,
                "secure": self.children[3].value.lower() == "true",
                "identifier": self.children[4].value
            }
        except Exception:
            return await interaction.response.send_message("Some of your input is invalid! Please try again.", ephemeral=True)
        
        await interaction.response.defer()
        try:
            await NodePool.create_node(
                bot=interaction.client,
                **config
            )
            await interaction.followup.send(f"Node {self.children[4].value} is connected!", ephemeral=True)
            await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
            
        except Exception as e:
            return await interaction.followup.send(str(e), ephemeral=True)

class NodesDropdown(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.view: NodesPanel
    
        super().__init__(
            placeholder="Select a node to edit...",
            options=self.get_nodes()
        )
    
    def get_nodes(self) -> list[discord.SelectOption]:
        nodes = [
            discord.SelectOption(
                label=name,
                description=("🟢 Connected" if node._available else "🔴 Disconnected") + f" - Players: {node.player_count} ({node.latency if node._available else 0:.2f}ms)")
            for name, node in NodePool._nodes.items()
        ]
        
        if not nodes:
            nodes = [discord.SelectOption(label="The node could not be found!")]
            
        return nodes
    
    def update(self) -> None:
        self.options = self.get_nodes()
        
    async def callback(self, interaction: discord.Interaction) -> None:
        selected_node = self.values[0]
        node = NodePool._nodes.get(selected_node, None)
        if not node:
            return await interaction.response.send_message("The node could not be found!", ephemeral=True)
        
        self.view.selected_node = node
        await interaction.response.defer()
        await self.view.message.edit(embed=self.view.build_embed(), view=self.view)

class NodesPanel(discord.ui.View):
    def __init__(self, bot, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.message: Optional[discord.Message] = None
        self.selected_node: Optional[Node] = None
        
        self.add_item(NodesDropdown(bot))
    
    def update_btn_status(self) -> None:
        for child in self._children:
            if isinstance(child, discord.ui.Button) and child.label != "Add":
                child.disabled = self.selected_node is None
            
            if isinstance(child, discord.ui.Select):
                child.update()
        
    def build_embed(self) -> discord.Embed:
        self.update_btn_status()
        embed = discord.Embed(title="📡 Nodes Panel", color=0x36393F)
        
        if not NodePool._nodes:
            embed.description = "```There are no nodes are connected!```"
        
        else:
            for name, node in NodePool._nodes.items():
                if self.selected_node and self.selected_node._identifier != node._identifier:
                    continue
                
                if node._available:
                    total_memory = node._stats.used + node._stats.free
                    embed.add_field(
                        name=f"{name} Node - 🟢 Connected",
                        value=f"```• ADDRESS: {node._host}:{node._port}\n" \
                            f"• PLAYERS: {len(node._players)}\n" \
                            f"• CPU:     {node._stats.cpu_process_load:.1f}%\n" \
                            f"• RAM:     {format_bytes(node._stats.free)}/{format_bytes(total_memory, True)} ({(node._stats.free/total_memory) * 100:.1f}%)\n" \
                            f"• LATENCY: {node.latency:.2f}ms\n" \
                            f"• UPTIME:  {format_time(node._stats.uptime)}```"
                    )
                else:
                    embed.add_field(
                        name=f"{name} Node - 🔴 Disconnected",
                        value=f"```• ADDRESS: {node._host}:{node._port}\n" \
                            f"• PLAYERS: {len(node._players)}\nNo extra data is available for display```",
                    )
                    
        return embed
    
    async def on_error(self, interaction: discord.Interaction, error, item) -> None:
        return await interaction.followup.send(str(error), ephemeral=True)
    
    @discord.ui.button(label="Add", emoji="➕", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddNodeModal(self, title="Create Node")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Remove", emoji="➖", style=discord.ButtonStyle.red, disabled=True)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_node:
            return await interaction.response.send_message("Please ensure that you have selected a node!", ephemeral=True)

        identifier = self.selected_node._identifier
        await self.selected_node.disconnect()
        del NodePool._nodes[identifier]
        
        self.selected_node = None
        
        await self.message.edit(embed=self.build_embed(), view=self)
        await interaction.response.send_message(f"Removed {identifier} Node from the bot.", ephemeral=True)
        
    @discord.ui.button(label="Reconnect", disabled=True, row=1)
    async def reconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.selected_node.is_connected:
            await self.selected_node.disconnect()
            await self.selected_node.connect()
            await self.message.edit(embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="Connect", disabled=True, row=1)
    async def connect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not self.selected_node.is_connected:
            await self.selected_node.connect()
            await self.message.edit(embed=self.build_embed(), view=self)
        
    @discord.ui.button(label="Disconnect", style=discord.ButtonStyle.red, disabled=True, row=1)
    async def disconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.selected_node.is_connected:
            await self.selected_node.disconnect()
            await self.message.edit(embed=self.build_embed(), view=self)

class DebugView(discord.ui.View):
    def __init__(self, bot, *, timeout: float | None = 180):
        self.bot: commands.Bot = bot
        super().__init__(timeout=timeout)

    async def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Debug Panel", color=0x36393F)
        
        # System Info
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        embed.add_field(
            name="<:system:1234567890> System Info",
            value=f"""```\n• SYSTEM: {platform.release()}\n
    • RAM: {format_bytes(ram.used)}/{format_bytes(ram.total)} ({ram.percent:.1f}%)\n 
    • DISK: {format_bytes(disk.used)}/{format_bytes(disk.total)} ({disk.percent:.1f}%)\n                 
    • CPU: {psutil.cpu_freq().current:.2f}Mhz ({cpu_percent:.1f}%)```
                  """,
            inline=False
        )

        # Bot Information
        latency = round(self.bot.latency * 1000, 2)
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        player_count = sum(node.player_count for node in NodePool._nodes.values())

        embed.add_field(
            name="<:bot:1234567890> Bot Information",
            value=f"""```\n• VERSION: v422FR\n \
    • LATENCY: {latency}ms\n \
    • GUILDS: {guild_count}\n \
    • USERS: {user_count}\n \
    • PLAYERS: {player_count}```""",
            inline=False
        )

        # Nodes Information
        nodes_panel_embed = NodesPanel(self.bot).build_embed()
        for field in nodes_panel_embed.fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)

        return embed

    @discord.ui.button(label='Code Runner', emoji="▶️", style=discord.ButtonStyle.green)
    async def run_command(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ExecuteModal("", title="Code Runner")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if not modal.code:
            return
            
        try:
            result = subprocess.run(modal.code, shell=True, capture_output=True, text=True, check=True)
            output = result.stdout
            error_output = result.stderr

            if output:
                text = output
            if error_output:
                if text:
                    text += "\n\n" + "--- STDERR ---\n" + error_output
                else:
                    text = "--- STDERR ---\n" + error_output

            if not text:
                text = "Command executed successfully with no output."

        except subprocess.CalledProcessError as e:
            text = f"Command failed with exit code {e.returncode}:\n" \
                   f"--- STDOUT ---\n{e.stdout}" \
                   f"--- STDERR ---\n{e.stderr}"
        except Exception as e:
            text = f"Error executing command: {e}"

        text = "\n".join([f"{'%03d' % index} | {i}" for index, i in enumerate(text.split("\n"), start=1)])
        await interaction.followup.send(f"```{text}```", ephemeral=True)
    
    @discord.ui.button(label="Re-Sync", emoji="🔄")
    async def sync(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 Synchronizing all your commands and language settings!", ephemeral=True)
        await self.bot.tree.sync()
        await interaction.edit_original_response(content="✅ All commands and settings have been successfully synchronized!")
    
    @discord.ui.button(label="Nodes", emoji="📡")
    async def nodes(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = NodesPanel(self.bot)
        await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)
        view.message = await interaction.original_response()
    
    @discord.ui.button(label="Stop-Bot", emoji="🔴")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        for name in self.bot.cogs.copy().keys():
            try:
                await self.bot.unload_extension(name)
            except:
                pass

        player_data = []
        for identifier, node in NodePool._nodes.items():
            for guild_id, player in node._players.copy().items():
                if player.guild.me is None or player.guild.me.voice or not player.current:
                    continue

                player_data.append(player.data)
                try:
                    await player.teardown()
                except:
                    pass

        await interaction.client.close()

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="debug", description="Open debug panel")
    async def debug(self, interaction: discord.Interaction):
        lang = get_bot_language()
        if interaction.user.id in [966009647871983701, 568657618185355278]:
            view = DebugView(self.bot)
            embed = await view.build_embed()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(ErrorMessages.NO_PERMISSION, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Debug(bot)) 
