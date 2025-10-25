from playwright.async_api import async_playwright
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

BOT_TOKEN = ""
bot = Bot(BOT_TOKEN)
dp = Dispatcher()
MAX_MESSAGE_LEN = 4000

async def get_page_context(browser):
    context = await browser.new_context()
    page = await context.new_page()
    return page, context

async def parse_weblancer(browser):
    info = []
    page, context = await get_page_context(browser)
    try:
        await page.goto("https://www.weblancer.net/freelance/", wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_selector("div.space-y-3", timeout=30000)
        elements = await page.query_selector_all("div.space-y-3 article")
        for el in elements:
            title = await el.query_selector("h2")
            desc = await el.query_selector("p")
            price = await el.query_selector("span")
            link = await el.query_selector("a")
            info.append(
                f"Название: {(await title.text_content()).strip() if title else 'Без названия'}\n"
                f"Описание: {(await desc.text_content()).strip() if desc else 'Описание отсутствует'}\n"
                f"Цена: {(await price.text_content()).strip() if price else 'Цена не указана'}\n"
                f"Ссылка: https://www.weblancer.net{await link.get_attribute('href') if link else '#'}"
            )
    except Exception as e:
        print(f"Ошибка Weblancer: {e}")
    await context.close()
    return info

async def parse_kwork(browser):
    info = []
    page, context = await get_page_context(browser)
    urls = [
        "https://kwork.ru/projects?c=15",
        "https://kwork.ru/projects?c=11",
        "https://kwork.ru/projects?c=17"
    ]
    for url in urls:
        for _ in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector(".wants-content", timeout=30000)
                break
            except Exception as e:
                print(f"Попытка загрузки {url} не удалась: {e}")
                await asyncio.sleep(5)
        try:
            cards = await page.query_selector_all(".wants-content .want-card")
            for card in cards:
                title_el = await card.query_selector("a")
                title_text = await title_el.text_content() if title_el else "Без названия"
                link_text = await title_el.get_attribute("href") if title_el else "#"
                info.append(f"Название: {title_text}\nСсылка: https://kwork.ru/{link_text}")
        except Exception as e:
            print(f"Ошибка парсинга Kwork: {e}")
    await context.close()
    return info

async def parse_youda(browser):
    info = []
    page, context = await get_page_context(browser)
    try:
        await page.goto("https://youdo.com/tasks-all-opened-all", wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_selector("ul.TasksList_list__MrMru.TasksList_allTasks__IJkwe", timeout=30000)
        cards = await page.query_selector_all("ul.TasksList_list__MrMru.TasksList_allTasks__IJkwe li")
        for i, card in enumerate(cards, 1):
            text = await card.inner_text()
            link_el = await card.query_selector("a")
            raw_link = await link_el.get_attribute("href") if link_el else None
            link = f"https://youdo.com{raw_link}" if raw_link and raw_link.startswith("/") else (raw_link or "Ссылка не найдена")
            info.append(f"Карточка {i}:\n{text}\nСсылка: {link}")
    except Exception as e:
        print(f"Ошибка YouDo: {e}")
    await context.close()
    return info

async def parse_fl(browser):
    info = []
    page, context = await get_page_context(browser)
    try:
        await page.goto("https://www.fl.ru/projects/", wait_until="networkidle", timeout=90000)
        await page.wait_for_selector("div#projects-list", timeout=30000)
        container = await page.query_selector("div#projects-list")
        if container:
            projects = await container.query_selector_all("div.b-post__grid")
            for project in projects:
                title_el = await project.query_selector("h2 a")
                title_text = (await title_el.text_content()).strip() if title_el else "Нет названия"
                link_text = await title_el.get_attribute("href") if title_el else "#"
                desc_el = await project.query_selector("div.b-post__body")
                desc_text = (await desc_el.text_content()).strip() if desc_el else "Описание отсутствует"
                price_el = await project.query_selector("div.b-post__price")
                price_text = (await price_el.text_content()).strip() if price_el else "Не указано"
                info.append(
                    f"Название: {title_text}\nСсылка: https://www.fl.ru{link_text}\nЦена: {price_text}\nОписание: {desc_text}"
                )
    except Exception as e:
        print(f"Ошибка FL: {e}")
    await context.close()
    return info

async def parse_freelancer(browser):
    info = []
    page, context = await get_page_context(browser)
    try:
        await page.goto("https://www.freelancer.com/job-search/projects/", wait_until="networkidle", timeout=90000)
        await page.wait_for_selector("div.JobSearchCard-item", timeout=30000)
        projects = await page.query_selector_all("div.JobSearchCard-item")
        for project in projects:
            title_el = await project.query_selector("a.JobSearchCard-primary-heading-link")
            title_text = (await title_el.text_content()).strip() if title_el else "Нет названия"
            link_text = await title_el.get_attribute("href") if title_el else None
            link = f"https://www.freelancer.com{link_text}" if link_text else "Ссылка не найдена"
            desc_el = await project.query_selector("p.JobSearchCard-primary-description")
            desc_text = (await desc_el.text_content()).strip() if desc_el else "Описание отсутствует"
            price_el = await project.query_selector("div.JobSearchCard-secondary-price")
            price_text = (await price_el.text_content()).strip() if price_el else "Не указано"
            info.append(f"Название: {title_text}\nОписание: {desc_text}\nЦена: {price_text}\nСсылка: {link}")
    except Exception as e:
        print(f"Ошибка Freelancer: {e}")
    await context.close()
    return info

async def send_periodically(chat_id: int):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        while True:
            all_tasks = []
            all_tasks += await parse_weblancer(browser)
            all_tasks += await parse_kwork(browser)
            all_tasks += await parse_youda(browser)
            all_tasks += await parse_fl(browser)
            all_tasks += await parse_freelancer(browser)

            if not all_tasks:
                await bot.send_message(chat_id, "За последний час новые заказы не найдены")
            else:
                message_text = ""
                for task in all_tasks:
                    if len(message_text) + len(task) + 2 > MAX_MESSAGE_LEN:
                        await bot.send_message(chat_id, message_text)
                        message_text = task + "\n\n"
                    else:
                        message_text += task + "\n\n"
                if message_text:
                    await bot.send_message(chat_id, message_text)

            await asyncio.sleep(3600)
        await browser.close()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Вы подписаны на обновления Weblancer, Kwork, Youda, FL, Freelancer!")
    asyncio.create_task(send_periodically(message.chat.id))

async def main():
    try:
        print("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
