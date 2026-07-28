"""
AshJob bot — Telegram approval interface.
Sends good-fit jobs with buttons. Listens only to Uwem's chat.
No cover letters or sending yet — just the approval loop.
"""
import os, sys, asyncio, csv, html, openpyxl
from aiogram.types import FSInputFile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import (Message, CallbackQuery, BotCommand,
                           InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton)

from tracker import filter_new, CSV_PATH, job_id
from matcher import seniority_bucket
import remotive, remoteok, weworkremotely
import drafter

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

SOURCES = [remotive.fetch_relevant, remoteok.fetch_relevant,
           weworkremotely.fetch_relevant]


def gather_good_jobs():
    all_jobs = []
    for fn in SOURCES:
        try:
            all_jobs.extend(fn())
        except Exception:
            pass
    new = filter_new(all_jobs)
    return [j for j in new if seniority_bucket(j["title"]) == "good"]


def set_status_by_id(jid, status):
    """Update a job's status in the CSV by its id."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = rows[0].keys() if rows else []
    for r in rows:
        if r["id"] == jid:
            r["status"] = status
    if rows:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(fields))
            w.writeheader(); w.writerows(rows)



def get_job_by_id(jid):
    """Return (title, company, url) for a job id from the CSV."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id"] == jid:
                return r["title"], r["company"], r["url"]
    return None, None, None


def job_buttons(url):
    jid = job_id({"url": url})
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Interested", callback_data=f"yes|{jid}"),
        InlineKeyboardButton(text="❌ Skip", callback_data=f"no|{jid}"),
        InlineKeyboardButton(text="🔍 Verify", url=url),
    ], [
        InlineKeyboardButton(text="📝 Draft Letter", callback_data=f"draft|{jid}"),
    ], [
        InlineKeyboardButton(text="✅ Applied", callback_data=f"applied|{jid}"),
    ]])


MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔍 Find Jobs")]],
    resize_keyboard=True, is_persistent=True,
    input_field_placeholder="Tap Find Jobs",
)


MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔍 Find Jobs")]],
    resize_keyboard=True, is_persistent=True,
    input_field_placeholder="Tap Find Jobs",
)


@dp.message(Command("start"))
async def start(msg: Message):
    if msg.chat.id != MY_CHAT_ID:
        return
    await msg.answer("AshJob bot online. Tap Find Jobs below.", reply_markup=MAIN_KB)


@dp.message(F.text == "🔍 Find Jobs")
@dp.message(F.text == "🔍 Find Jobs")
@dp.message(F.text == "🔍 Find Jobs")
@dp.message(Command("findjobs"))
@dp.message(Command("jobs"))
async def jobs(msg: Message):
    if msg.chat.id != MY_CHAT_ID:
        return
    await msg.answer("Scanning sources...")
    good = gather_good_jobs()
    if not good:
        await msg.answer("No new good-fit jobs right now. Try again later.")
        return
    await msg.answer(f"Found {len(good)} good-fit job(s):")
    sent, failed = 0, 0
    for j in good:
        title = html.escape(j.get("title", ""))
        company = html.escape(j.get("company", ""))
        location = html.escape(j.get("location", ""))
        source = html.escape(j.get("source", ""))
        text = (f"<b>{title}</b>\n"
                f"{company}  |  {location}\n"
                f"Source: {source}")
        try:
            await bot.send_message(MY_CHAT_ID, text, parse_mode="HTML",
                                   reply_markup=job_buttons(j["url"]))
            sent += 1
        except Exception as e:
            failed += 1
            print(f"[SEND FAIL] {j.get('title','?')} -> {type(e).__name__}: {e}")
    print(f"[jobs] sent={sent} failed={failed}")
    if failed:
        await msg.answer(f"({failed} card(s) failed to send — check terminal)")


@dp.callback_query(F.data.startswith("yes|"))
async def cb_yes(cb: CallbackQuery):
    jid = cb.data.split("|", 1)[1]
    set_status_by_id(jid, "interested")
    await cb.answer("Marked interested ✅")
    await cb.message.edit_reply_markup(reply_markup=None)


@dp.callback_query(F.data.startswith("no|"))
async def cb_no(cb: CallbackQuery):
    jid = cb.data.split("|", 1)[1]
    set_status_by_id(jid, "skipped")
    await cb.answer("Skipped ❌")
    await cb.message.edit_reply_markup(reply_markup=None)



@dp.callback_query(F.data.startswith("draft|"))
async def cb_draft(cb: CallbackQuery):
    jid = cb.data.split("|", 1)[1]
    title, company, url = get_job_by_id(jid)
    if not title:
        await cb.answer("Job not found in log.")
        return
    await cb.answer("Drafting your letter...")
    await bot.send_message(MY_CHAT_ID, f"Drafting for {title} @ {company}...")
    try:
        letter = drafter.draft(title, company, "")
        # send as plain text so it's easy to copy; chunk if long
        for i in range(0, len(letter), 3500):
            await bot.send_message(MY_CHAT_ID, letter[i:i+3500])
    except Exception as e:
        await bot.send_message(MY_CHAT_ID, f"Draft failed: {type(e).__name__}: {e}")



async def push_jobs(reason="Daily scan"):
    """Run the pipeline and push new good-fit jobs to Uwem's chat."""
    good = gather_good_jobs()
    if not good:
        await bot.send_message(MY_CHAT_ID, f"{reason}: no new good-fit jobs.")
        return
    await bot.send_message(MY_CHAT_ID, f"{reason}: {len(good)} new good-fit job(s)!")
    import html as _html
    for j in good:
        text = (f"<b>{_html.escape(j['title'])}</b>\n"
                f"{_html.escape(j['company'])}  |  {_html.escape(j['location'])}\n"
                f"Source: {_html.escape(j['source'])}")
        try:
            await bot.send_message(MY_CHAT_ID, text, parse_mode="HTML",
                                   reply_markup=job_buttons(j["url"]))
        except Exception as e:
            print(f"[push fail] {j.get('title','?')}: {e}")



@dp.callback_query(F.data.startswith("applied|"))
async def cb_applied(cb: CallbackQuery):
    jid = cb.data.split("|", 1)[1]
    set_status_by_id(jid, "applied")
    await cb.answer("Marked as applied ✅")
    await cb.message.edit_reply_markup(reply_markup=None)



@dp.message(Command("log"))
async def log_cmd(msg: Message):
    if msg.chat.id != MY_CHAT_ID:
        return
    if not os.path.exists(CSV_PATH):
        await msg.answer("No jobs logged yet.")
        return
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    counts = {}
    for r in rows:
        s = r.get("status", "new")
        counts[s] = counts.get(s, 0) + 1
    summary = "Application tracker:\n" + "\n".join(
        f"  {k}: {v}" for k, v in sorted(counts.items()))
    await msg.answer(summary)

    # build spreadsheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Applications"
    headers = ["Date Seen", "Company", "Title", "Location",
               "Source", "Status", "URL"]
    ws.append(headers)
    for r in rows:
        ws.append([r.get("first_seen",""), r.get("company",""),
                   r.get("title",""), r.get("location",""),
                   r.get("source",""), r.get("status",""), r.get("url","")])
    for col in ws.columns:
        width = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(width + 2, 50)
    out = os.path.join(os.path.dirname(CSV_PATH), "applications.xlsx")
    wb.save(out)
    await msg.answer_document(FSInputFile(out),
                              caption="Your application log")


async def main():
    await bot.set_my_commands([
        BotCommand(command="findjobs", description="Scan for new jobs"),
        BotCommand(command="log", description="View application tracker"),
        BotCommand(command="start", description="Check bot is online"),
    ])
    scheduler = AsyncIOScheduler(timezone="Africa/Lagos")
    scheduler.add_job(push_jobs, "cron", hour=8, minute=0)
    scheduler.start()
    print("Bot starting... daily scan set for 08:00 WAT. Ctrl+C to stop")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
