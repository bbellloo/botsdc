import discord
from discord.ext import commands, tasks
import datetime
import json
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 用來存儲生日資料
eebir = {}

# 用來存儲最後一篇 Instagram 發文的 ID
eeig_id = ""

# 讀取生日資料
def load_eebir():
    global eebir
    try:
        with open("eebir.json", "r") as f:
            eebir = json.load(f)
    except FileNotFoundError:
        eebir = {}

# 儲存生日資料
def save_eebir():
    with open("eebir.json", "w") as f:
        json.dump(eebir, f)

# 讀取最後一篇 Instagram 發文的 ID
def load_eeig_id():
    global eeig_id
    try:
        with open("eeig_id.json", "r") as f:
            eeig_id = json.load(f)
    except FileNotFoundError:
        eeig_id = ""

# 儲存最後一篇 Instagram 發文的 ID
def save_eeig_id(post_id):
    global eeig_id
    eeig_id = post_id
    with open("eeig_id.json", "w") as f:
        json.dump(post_id, f)

@bot.event
async def on_ready():
    load_eebir()
    load_eeig_id()
    birthday_check.start()
    instagram_check.start()
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def set_birthday(ctx, date: str):
    """設定生日格式為 YYYY-MM-DD"""
    try:
        birthday = datetime.datetime.strptime(date, "%Y-%m-%d")
        eebir[str(ctx.author.id)] = date
        save_eebir()
        await ctx.send(f"{ctx.author.mention} 的生日已設定為 {date}")
    except ValueError:
        await ctx.send("日期格式錯誤，請使用 YYYY-MM-DD 格式")

@bot.command()
async def get_birthday(ctx, member: discord.Member = None):
    """查看個人或其他成員的生日"""
    if member is None:
        member = ctx.author
    birthday = eebir.get(str(member.id), None)
    if birthday:
        await ctx.send(f"{member.mention} 的生日是 {birthday}")
    else:
        await ctx.send(f"{member.mention} 尚未設定生日")

@bot.command()
async def get_all_bir(ctx):
    """查看所有成員的生日"""
    if not eebir:
        await ctx.send("目前沒有任何成員設定生日")
        return

    message = "以下是所有設定過生日的成員：\n"
    for user_id, birthday in eebir.items():
        try:
            user = await bot.fetch_user(user_id)
            message += f"{user.name}: {birthday}\n"
        except discord.NotFound:
            message += f"使用者 ID {user_id}: 無法取得該使用者資訊\n"
        except discord.HTTPException as e:
            if e.status == 429:  # 處理速率限制
                retry_after = e.retry_after
                await asyncio.sleep(retry_after)
                user = await bot.fetch_user(user_id)
                message += f"{user.name}: {birthday}\n"
        await asyncio.sleep(1)  # 添加延遲避免觸發速率限制

    await ctx.send(message)



@bot.command()
async def time(ctx):
    """檢查機器人伺服器的當前時間"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await ctx.send(f"伺服器當前時間為：{now}")

@bot.command()
async def test_birthday(ctx):
    """手動觸發今日生日提醒"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    channel = bot.get_channel(1267389055478403143)  # 替換為你的頻道 ID
    for user_id, birthday in eebir.items():
        if birthday == today:
            user = await bot.fetch_user(user_id)
            await channel.send(f"🎉 祝 <@{ctx.author.id}>生日快樂！ (test)")
    await ctx.send("生日機器人已測試完畢")

@tasks.loop(minutes=1)
async def birthday_check():
    await bot.wait_until_ready()
    
    now = datetime.datetime.now()
    if now.hour == 13 and now.minute == 19:
        today = now.strftime("%m-%d")
        channel = bot.get_channel(1267389055478403143)  # 替換為你的頻道 ID
        for user_id, birthday in eebir.items():
            if birthday[5:] == today:
                user = await bot.fetch_user(user_id)
                await channel.send(f"🎉 今天是 {user.mention} ㄉ生日！ 🎂")

@tasks.loop(hours=12)
async def instagram_check():
    await bot.wait_until_ready()
    instagram_username = "chloelancemay"  # 替換為你要檢查的 Instagram 使用者名稱
    url = f"https://www.instagram.com/{instagram_username}/"
    
    # 設置 Selenium 驅動
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 無頭模式，不打開瀏覽器
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(url)
    await asyncio.sleep(5)  # 等待頁面加載

    try:
        # 找到最新發文的鏈接
        post = driver.find_element(By.XPATH, "//article//a")
        post_id = post.get_attribute("href").split("/")[-2]
        channel = bot.get_channel(1265229761983283282)  # 替換為你的頻道 ID
        share_url = f" https://www.instagram.com/p/{post_id}?utm_source=ig_web_button_share_sheet&igsh=MzRlODBiNWFlZA=="
        
        if post_id != eeig_id:
            save_eeig_id(post_id)
            await channel.send(f"<@&{1267472821190262928}>依依的IG發文啦~ {share_url}")
    except Exception as e:
        print(f"無法從 Instagram 獲取數據: {e}")
    finally:
        driver.quit()

bot.run("MTI2NjM0Nzg2MzI5NDYwNzUxMg.GoDEp1.UtLwCK58esXTST5f4W-FKommT8LsSKjTWvU2VA")  # 替換為你的機器人 token
