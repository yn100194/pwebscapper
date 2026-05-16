import os
import requests
from bs4 import BeautifulSoup
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # Thêm để làm nút bấm
import asyncio
import random
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, 'config.env')
env_path = os.path.join(BASE_DIR, '.env')

# Load cấu hình từ file .env hoặc config.env
if os.path.exists(config_path):
    load_dotenv(config_path)
else:
    load_dotenv(env_path)

# Lấy các giá trị cấu hình từ biến môi trường
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DOMAIN = os.getenv('DOMAIN', 'https://xxx.com')
CRAWL_PATHS = os.getenv('CRAWL_PATH', '/example/path1').split('|')
MAX_ITEMS = int(os.getenv('MAX_ITEMS', 50))
DELAY_MIN = int(os.getenv('DELAY_MIN', 10))
DELAY_MAX = int(os.getenv('DELAY_MAX', 20))

SCRAPER_API_KEY=os.getenv('SCRAPER_API_KEY')
DOMAIN=os.getenv('AV_DOMAIN')


async def send_telegram_message(bot_token, chat_id, message, image_url=None, action_url=None, action_text="Xem chi tiết 🌐"):
    bot = telegram.Bot(token=bot_token)
    
    # Tạo nút bấm (Inline Keyboard) dưới tin nhắn nếu có link hành động
    reply_markup = None
    if action_url:
        keyboard = [[InlineKeyboardButton(text=action_text, url=action_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
    try:
        if image_url:
            await bot.send_photo(
                chat_id=chat_id, 
                photo=image_url, 
                caption=message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await bot.send_message(
                chat_id=chat_id, 
                text=message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        print(f"Sent message to Telegram successfully.")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")


async def process_path(path):
    target_url = f"{DOMAIN.rstrip('/')}/{path.lstrip('/')}"
    print(f"Starting crawl for path: {target_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
#        response = requests.get(target_url, headers=headers)
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
        response = requests.get(proxy_url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to retrieve {target_url}. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        models_data = []
        models = soup.find_all('a', id=lambda x: x and x.startswith('model-list-item-'))

        for model in models:
            img_elem = model.find('img')
            img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None

            name = None
            if img_elem and 'alt' in img_elem.attrs:
                name = img_elem['alt'].replace(' Show Webcam', '').strip()

            if not name:
                next_sibling = model.next_sibling
                if next_sibling and next_sibling.strip():
                    name = next_sibling.strip()

            if name and img_url:
                idol_path = model.get('href', f"/{name}").lstrip('/')
                idol_url = f"{DOMAIN.rstrip('/')}/{idol_path}"

                models_data.append({
                    'name': name,
                    'image_url': img_url,
                    'profile_url': idol_url
                })

            if len(models_data) >= MAX_ITEMS:
                break

        print(f"Found {len(models_data)} models in {path}.")

        for i, model in enumerate(models_data):
            # Định dạng tin nhắn bằng Markdown cho chuyên nghiệp và gọn gàng hơn
            message = (
                f"🌟 *THÔNG TIN IDOL* 🌟\n"
                f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"👤 *Tên:* `{model['name']}`\n"
                f"📂 *Danh mục:* `{path.strip('/')}`\n"
            )
            
            # Gửi kèm link profile vào nút bấm
            await send_telegram_message(
                bot_token=TELEGRAM_BOT_TOKEN, 
                chat_id=TELEGRAM_CHAT_ID, 
                message=message, 
                image_url=model['image_url'],
                action_url=model['profile_url'],
                action_text="Xem Profile Idol ✨"
            )

            if i < len(models_data) - 1:
                delay = random.randint(DELAY_MIN, DELAY_MAX)
                print(f"[{path}] Waiting {delay}s...")
                await asyncio.sleep(delay)

    except Exception as e:
        print(f"Error in path {path}: {e}")


async def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return

    # Chạy các path đồng thời bằng asyncio.gather
    tasks = [process_path(path.strip()) for path in CRAWL_PATHS]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
