import discord
import os
import random
import asyncio
import colorsys
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1363957347298447360
COLOR_ROLE_ID = 1364526866832162846
ANNOUNCE_CH_ID = 1364541188644012033
INFO_CHANNEL_ID = 1364731786168500335
COUNTDOWN_CH_ID = 1364747941532667987
INTERVAL_SECONDS = 30
MESSAGE_ID_FILE = "message_id.txt"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def generate_random_color():
    h = random.random()
    s = random.uniform(0.5, 1)
    v = random.uniform(0.7, 1)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return discord.Color.from_rgb(int(r * 255), int(g * 255), int(b * 255))


def read_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, "r") as file:
            try:
                return int(file.read().strip())
            except ValueError:
                return None
    return None


def save_message_id(message_id):
    with open(MESSAGE_ID_FILE, "w") as file:
        file.write(str(message_id))


class EditButton(View):

    def __init__(self, message, user):
        super().__init__(timeout=None)
        self.message = message
        self.user = user

    @discord.ui.button(label="✍️ تعديل النص",
                       style=discord.ButtonStyle.primary)
    async def edit_text(self, interaction: discord.Interaction,
                        button: Button):
        if interaction.user == self.user:
            modal = discord.ui.Modal(title="تعديل النص")
            modal.add_item(discord.ui.InputText(label="أدخل النص الجديد"))

            await interaction.response.send_modal(modal)

            def check(m):
                return m.author == self.user and isinstance(
                    m.channel,
                    discord.TextChannel) and m.channel.id == INFO_CHANNEL_ID

            try:
                msg = await bot.wait_for("message", check=check, timeout=300)
                new_embed = discord.Embed(title="INFO",
                                          description=msg.content,
                                          color=discord.Color.pink(),
                                          timestamp=datetime.utcnow())
                new_embed.set_footer(
                    text=f"{interaction.guild.name}",
                    icon_url=interaction.guild.icon.url
                    if interaction.guild.icon else discord.Embed.Empty)

                await self.message.edit(embed=new_embed)
                await interaction.response.send_message(
                    "✅ تم تعديل النص بنجاح!", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ حدث خطأ أثناء تعديل النص: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ هذا الزر مخصص لك فقط.",
                                                    ephemeral=True)


class ColorRoleButtons(View):

    def __init__(self, role_id):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="🎨 الحصول على الرتبة",
                       style=discord.ButtonStyle.success,
                       custom_id="get_rgb")
    async def get_rgb(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message(
                "❌ لم يتم العثور على الرتبة.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("🔔 لديك الرتبة بالفعل!",
                                                    ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ تم منحك رتبة RGB!",
                                                    ephemeral=True)

    @discord.ui.button(label="❌ إزالة الرتبة",
                       style=discord.ButtonStyle.danger,
                       custom_id="remove_rgb")
    async def remove_rgb(self, interaction: discord.Interaction,
                         button: Button):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message(
                "❌ لم يتم العثور على الرتبة.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("❎ تمت إزالة رتبة RGB.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("🔕 لا تملك الرتبة حالياً.",
                                                    ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.loop.create_task(color_cycle())

    # إرسال إيمبد تعليمات الكتابة في القناة عند التشغيل
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("❌ القناة غير موجودة.")
        return

    embed = discord.Embed(
        title="INFO",
        description="اكتب النص الذي تريده لتحويله إلى إيمبد، وسوف يظهر هنا.",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow())
    embed.set_footer(text=f"{bot.guilds[0].name}",
                     icon_url=bot.guilds[0].icon.url
                     if bot.guilds[0].icon else discord.Embed.Empty)
    message = await channel.send(embed=embed)
    await message.add_reaction("✍️")

    # إرسال رسالة بدء العد
    countdown_channel = bot.get_channel(COUNTDOWN_CH_ID)
    if countdown_channel:
        ask_msg = await countdown_channel.send(
            embed=discord.Embed(title="هل تريد بدء العد؟",
                                description="اضغط ✅ لبدء العد من 1 إلى مليون!",
                                color=discord.Color.orange()))
        await ask_msg.add_reaction("✅")


@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    if reaction.emoji == "✍️":
        await user.send(
            "يرجى كتابة النص الذي تريد تحويله إلى إيمبد، ثم أرسله هنا.")
        try:
            msg = await bot.wait_for('message',
                                     timeout=60.0,
                                     check=lambda m: m.author == user)
            await user.send("يرجى إدخال عنوان الإيمبد:")
            title_msg = await bot.wait_for('message',
                                           timeout=60.0,
                                           check=lambda m: m.author == user)
            await user.send(
                "يرجى إدخال اللون (كود اللون الست عشري مثل #FF5733):")
            color_msg = await bot.wait_for('message',
                                           timeout=60.0,
                                           check=lambda m: m.author == user)

            try:
                embed_color = discord.Color(
                    int(color_msg.content.strip()[1:], 16))
            except ValueError:
                embed_color = discord.Color.green()

            await user.send("يرجى إدخال ID الروم الذي تريد إرسال الإيمبد إليه:"
                            )
            channel_id_msg = await bot.wait_for(
                'message', timeout=60.0, check=lambda m: m.author == user)
            try:
                channel_id = int(channel_id_msg.content.strip())
                channel = bot.get_channel(channel_id)
                if not channel:
                    await user.send("❌ القناة غير موجودة.")
                    return
            except ValueError:
                await user.send("❌ ID القناة غير صحيح.")
                return

            embed = discord.Embed(title=title_msg.content,
                                  description=msg.content,
                                  color=embed_color,
                                  timestamp=datetime.utcnow())
            embed.set_footer(
                text=f"{reaction.message.guild.name}",
                icon_url=reaction.message.guild.icon.url
                if reaction.message.guild.icon else discord.Embed.Empty)

            old_msg_id = 1364732432825454645
            try:
                old_msg = await channel.fetch_message(old_msg_id)
                await old_msg.delete()
            except Exception as e:
                print(f"❌ Error deleting old message: {e}")

            new_message = await channel.send(embed=embed)
            save_message_id(new_message.id)
            await user.send("✅ تم إرسال الإيمبد بنجاح!")

        except asyncio.TimeoutError:
            await user.send("❌ لم تكتب النص أو العنوان في الوقت المحدد.")

    elif str(reaction.emoji
             ) == "✅" and reaction.message.channel.id == COUNTDOWN_CH_ID:
        countdown_channel = reaction.message.channel
        await countdown_channel.send("✅ تم بدء العد من 1 إلى مليون! 🔢")
        for i in range(1, 1000001):
            await countdown_channel.send(f"{i}")
            await asyncio.sleep(2)
        await countdown_channel.send("🚀 تم الانتهاء من العد إلى مليون.")
        await asyncio.sleep(2)
        await countdown_channel.send("🔄 بدأ العد من 0 الآن!")
        count = 0
        while True:
            await countdown_channel.send(f"{count}")
            count += 1
            await asyncio.sleep(2)


async def color_cycle():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    role = guild.get_role(COLOR_ROLE_ID)
    channel = bot.get_channel(ANNOUNCE_CH_ID)

    if not role:
        print(f"❌ لم يتم العثور على الدور ID: {COLOR_ROLE_ID}")
        return

    next_color = generate_random_color()
    view = ColorRoleButtons(COLOR_ROLE_ID)

    old_msg_id = read_message_id()
    if old_msg_id:
        try:
            old_msg = await channel.fetch_message(old_msg_id)
            await old_msg.delete()
        except:
            pass

    embed = discord.Embed(
        description=
        f"⏰ سيتم تغيير لون الرتبة خلال `{INTERVAL_SECONDS}` ثانية\n\nيمكنك استخدام الأزرار أدناه للحصول أو إزالة الرتبة.",
        color=next_color)
    embed.set_thumbnail(
        url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.set_footer(
        text=f"{guild.name} • {datetime.now().strftime('%I:%M:%S %p')}",
        icon_url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="🌈 اللون التالي", value=f"\u200b", inline=False)
    embed.set_image(
        url=f"https://singlecolorimage.com/get/{next_color.value:06x}/50x50")

    message = await channel.send(embed=embed, view=view)
    save_message_id(message.id)

    while True:
        for remaining in range(INTERVAL_SECONDS, 0, -1):
            try:
                embed.description = f"⏰ سيتم تغيير لون الرتبة خلال `{remaining}` ثانية\n\nيمكنك استخدام الأزرار أدناه للحصول أو إزالة الرتبة."
                embed.set_footer(
                    text=
                    f"{guild.name} • {datetime.now().strftime('%I:%M:%S %p')}",
                    icon_url=guild.icon.url
                    if guild.icon else discord.Embed.Empty)
                await message.edit(embed=embed, view=view)
            except Exception as e:
                print(f"❌ Error updating message: {e}")
            await asyncio.sleep(1)

        try:
            if not guild.me.guild_permissions.manage_roles:
                print("❌ البوت ليس لديه صلاحية إدارة الأدوار.")
                return

            await role.edit(color=next_color)
            print(f"✅ Changed '{role.name}' color to {next_color}")
        except Exception as e:
            print(f"❌ Error changing role color: {e}")

        next_color = generate_random_color()
        embed.color = next_color
        embed.set_image(
            url=f"https://singlecolorimage.com/get/{next_color.value:06x}/50x50"
        )


import threading
import requests



bot.run(TOKEN)
