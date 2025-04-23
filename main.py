import discord
import os
import random
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime
from keep_alive import keep_alive

keep_alive()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1363957347298447360
COLOR_ROLE_ID = 1364526866832162846
ANNOUNCE_CH_ID = 1364541188644012033
INTERVAL_SECONDS = 60

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


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


async def color_cycle():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    role = guild.get_role(COLOR_ROLE_ID)
    channel = bot.get_channel(ANNOUNCE_CH_ID)

    next_color = discord.Color.random()

    view = ColorRoleButtons(COLOR_ROLE_ID)
    message = None

    while True:
        for remaining in range(INTERVAL_SECONDS, 0, -1):
            embed = discord.Embed(
                description=
                f"⏰ سيتم تغيير لون الرتبة خلال `{remaining}` ثانية\n\nيمكنك استخدام الأزرار أدناه للحصول أو إزالة الرتبة.",
                color=next_color)
            embed.set_thumbnail(
                url=guild.icon.url if guild.icon else discord.Embed.Empty)
            embed.set_footer(
                text=f"{guild.name} • {datetime.now().strftime('%I:%M:%S %p')}",
                icon_url=guild.icon.url if guild.icon else discord.Embed.Empty)

            
            embed.add_field(name="🌈 اللون التالي",
                            value=f"\u200b",
                            inline=False)
            embed.set_image(
                url=
                f"https://singlecolorimage.com/get/{next_color.value:06x}/50x50"
            )

            try:
                if message is None:
                    message = await channel.send(embed=embed, view=view)
                else:
                    await message.edit(embed=embed, view=view)
            except Exception as e:
                print(f"❌ Error updating message: {e}")
            await asyncio.sleep(1)

        try:
            await role.edit(color=next_color)
            print(f"✅ Changed '{role.name}' color to {next_color}")
        except Exception as e:
            print(f"❌ Error changing role color: {e}")

        next_color = discord.Color.from_rgb(random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))


bot.run(TOKEN)
