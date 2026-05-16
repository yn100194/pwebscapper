import os
import random
import sys
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"⚠️ KNOT FOUND file .env at: {ENV_PATH}", file=sys.stderr)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SCRAPER_API_KEY=os.getenv('SCRAPER_API_KEY')

DELAY_MIN = float(os.getenv('DELAY_MIN', 1.0))
DELAY_MAX = float(os.getenv('DELAY_MAX', 3.0))

DOMAIN=os.getenv('AZ_DOMAIN')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Missing config in file .env!", file=sys.stderr)
    sys.exit(1)


async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text=message, 
            parse_mode='HTML', 
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"❌ Error sent Telegram: {e}", file=sys.stderr)


def scrape_url():
    url = DOMAIN
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    try:
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
#        response = requests.get(url, headers=headers, timeout=15)
        response = requests.get(proxy_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error load web: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    trending_videos = []
    trending_section = soup.find('div', class_='section-title', string='Trending Videos')
    
    if trending_section:
        media_list = trending_section.find_next_sibling('div', class_='media-list media-list-five-columns')
        if media_list:
            video_items = media_list.find_all('div', class_='media-list-item video-list-item')
            for item in video_items[:30]:
                video_data = {}
                a_tag = item.find('a')
                if a_tag:
                    video_data['video_url'] = DOMAIN + a_tag['href'] if a_tag.get('href') else '#'
                    video_data['thumbnail_url'] = a_tag['data-thumb'] if a_tag.get('data-thumb') else None

                img_tag = item.find('img')
                video_data['title'] = img_tag['alt'] if img_tag and img_tag.get('alt') else 'Title Unknown'

                timestamp_span = item.find('span', class_='video-timestamp')
                video_data['duration'] = timestamp_span.text.strip() if timestamp_span else 'N/A'

                views_div = item.find('div', class_='video-views')
                video_data['views'] = views_div.text.strip() if views_div else 'N/A'

                celebs_div = item.find('div', class_='video-celebs')
                if celebs_div:
                    celebs_list = []
                    for a in celebs_div.find_all('a'):
                        name = a.text.strip()
                        href = a.get('href', '')
                        link = DOMAIN + href if href else '#'
                        celebs_list.append((name, link))
                    video_data['celebrities'] = celebs_list
                else:
                    video_data['celebrities'] = []

                trending_videos.append(video_data)
    return trending_videos


async def main():
    videos = scrape_url()
    if videos:
        await send_telegram_message(f"🔥 <b>Update {len(videos)} VIDEO TRENDING</b>")
        
        for i, video in enumerate(videos):
            if video['celebrities']:
                celeb_links = [f"<a href='{c[1]}'>{c[0]}</a>" for c in video['celebrities']]
                celeb_text = ", ".join(celeb_links)
            else:
                celeb_text = "N/A"
            
            thumb_action = f" 🎬 <a href='{video['thumbnail_url']}'>[Watch Thumbnail Image]</a>" if video['thumbnail_url'] else ""

            msg = f"📌 <b>{i+1}. <a href='{video['video_url']}'>{video['title']}</a></b>\n"
            msg += f"👤 <b>Actor:</b> {celeb_text}\n"
            msg += f"⏱️ <b>TDuration</b> {video['duration']} | {video['views']}\n"
            msg += f"🚀 <b>Action:</b> <a href='{video['video_url']}'>[Watch Now]</a>{thumb_action}"
            
            await send_telegram_message(msg)
            
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    else:
        print("ℹ️ KNOT FOUND any new video.", file=sys.stdout)


if __name__ == '__main__':
    asyncio.run(main())
