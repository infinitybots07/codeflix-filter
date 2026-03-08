import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

PLUGINS_FOLDER = "plugins"


def get_commands_by_plugin():
    plugin_cmds = {}

    if not os.path.isdir(PLUGINS_FOLDER):
        return {}

    for file in sorted(os.listdir(PLUGINS_FOLDER)):
        if not file.endswith(".py"):
            continue

        plugin_name = file[:-3]  # Remove .py
        path = os.path.join(PLUGINS_FOLDER, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all commands in filters.command()
            matches = re.findall(r'filters\.command\s*\((.*?)\)', content, re.DOTALL)
            cmds = set()

            for match in matches:
                clean = match.replace('"', '').replace("'", "").replace("[", "").replace("]", "")
                for cmd in clean.split(","):
                    cmd = cmd.strip()
                    if cmd and re.match(r'^[a-zA-Z0-9_]+$', cmd):
                        cmds.add(cmd)

            if cmds:
                plugin_cmds[plugin_name] = sorted(cmds)

        except Exception as e:
            print(f"[PluginScan] {file} error: {e}")

    return plugin_cmds


def build_text(plugin_data):
    lines = []
    total = 0

    lines.append("📂 **BOT COMMANDS BY PLUGIN**\n")

    for plugin, cmds in plugin_data.items():
        total += len(cmds)
        lines.append(f"🔹 **{plugin.upper()}**")
        for cmd in cmds:
            lines.append(f"   • `/{cmd}`")
        lines.append("")  # empty line between plugins

    lines.append(f"📊 **TOTAL COMMANDS:** `{total}`")

    text = "\n".join(lines)

    if len(text) > 4090:
        text = text[:4090] + "\n\n⚠️ Command list truncated."

    return text


@Client.on_message(filters.command("allcmds") & filters.private)
async def all_commands(client: Client, message: Message):
    msg = await message.reply_text("⏳ **Scanning plugins...**")

    plugin_data = get_commands_by_plugin()

    if not plugin_data:
        await msg.edit_text("❌ **No commands found.**")
        return

    text = build_text(plugin_data)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="cmd_refresh"),
            InlineKeyboardButton("❌ Close", callback_data="cmd_close")
        ]
    ])

    await msg.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("cmd_refresh"))
async def refresh_commands(client, cb):
    await cb.answer("🔄 Refreshing...", show_alert=True)

    plugin_data = get_commands_by_plugin()
    text = build_text(plugin_data) if plugin_data else "❌ **No commands found.**"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="cmd_refresh"),
            InlineKeyboardButton("❌ Close", callback_data="cmd_close")
        ]
    ])

    await cb.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("cmd_close"))
async def close_commands(client, cb):
    await cb.answer("✅ Thanks for closing!", show_alert=True)
    try:
        await cb.message.delete()
    except:
        pass