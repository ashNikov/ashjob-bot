with open("bot.py") as f:
    code = f.read()

# After the draft letter is sent, add an apply-link + copy-hint message
old = '''        letter = drafter.draft(title, company, "")
        # send as plain text so it's easy to copy; chunk if long
        for i in range(0, len(letter), 3500):
            await bot.send_message(MY_CHAT_ID, letter[i:i+3500])'''

new = '''        letter = drafter.draft(title, company, "")
        # send the letter as its own message: tap-hold to copy on mobile
        for i in range(0, len(letter), 3500):
            await bot.send_message(MY_CHAT_ID, letter[i:i+3500])
        # companion: apply button + reminder, positioned right after the letter
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚀 Open apply page", url=url),
        ]])
        await bot.send_message(
            MY_CHAT_ID,
            "☝️ Tap-hold the letter above to copy it, then open the "
            "apply page, paste, attach your CV, and submit.",
            reply_markup=kb)'''

code = code.replace(old, new)
with open("bot.py", "w") as f:
    f.write(code)
print("PATCHED OK" if new in code else "CHECK - pattern not matched")
