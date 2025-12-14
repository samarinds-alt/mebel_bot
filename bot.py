import os
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ——— ЗАГРУЗКА НАСТРОЕК ИЗ .env ———
TOKEN = os.getenv("BOT_TOKEN")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID"))

# ——— FSM ———
class Form(StatesGroup):
    fio = State()
    phone = State()
    item_type = State()
    carcass_material = State()
    facade_material = State()
    visible_sides_material = State()
    back_wall = State()
    countertop_and_wall_panel = State()
    canopy_height = State()
    plinth_height = State()
    edge_banding = State()
    bottom_and_top_type = State()
    technical_gaps = State()
    hinges = State()
    supports = State()
    drawers = State()
    additional_info = State()
    
# ——— ИНИЦИАЛИЗАЦИЯ ———
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ——— ВАЛИДАТОР ФИО ———
def validate_fio(text: str) -> bool:
    if not re.fullmatch(r"[а-яА-ЯёЁa-zA-Z\-'\s]{2,50}", text.strip()):
        return False
    return len(text.strip().split()) >= 2

# ——— /start ———
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    sent = await message.answer(
        "Здравствуйте\\! 👋\n\n"
        "Я помогу вам оформить заявку на проектирование мебели\\. "
        "Начнём с простого:\n\n"
        "Как вас зовут\\? Укажите ваше *ФИО*\\.\n"
        "Пример: _Иванов Иван Иванович_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.fio)

# ——— ОБРАБОТКА ФИО ———
@router.message(Form.fio)
async def process_fio(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите текст\\. 📝")
        return

    fio = message.text.strip()
    if not validate_fio(fio):
        await message.answer(
            "❌ Похоже, это не похоже на ФИО\\.\n\n"
            "Введите хотя бы *Фамилию* и *Имя* на русском или английском\\. "
            "Без цифр и лишних символов\\.\n\n"
            "Пример: _Иванов Иван_"
        )
        return

    # Удаляем предыдущее сообщение бота (вопрос)
    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except Exception:
            pass  # Игнорируем ошибку (например, если сообщение уже удалено)

    # Отправляем следующий вопрос
    sent = await message.answer(
        f"Отлично\\! Здравствуйте, {fio}\\! ✨\n\n"
        "Теперь укажите *контактный телефон* \\(привязанный к Telegram, чтобы мы в дальнейшем могли добавить вас в группу по данному проекту\\)"
    )
    
    await state.update_data(fio=fio, prev_bot_message_id=sent.message_id)
    await state.set_state(Form.phone)

# ——— ОБРАБОТКА ТЕЛЕФОНА ———
@router.message(Form.phone)
async def process_phone(message: Message, state: FSMContext):
    # Получаем username или имя из аккаунта Telegram
    telegram_username = message.from_user.username  # может быть None
    telegram_first_name = message.from_user.first_name or ""
    telegram_last_name = message.from_user.last_name or ""
    
    full_name = f"{telegram_first_name} {telegram_last_name}".strip()
    contact_info = f"@{telegram_username}" if telegram_username else full_name

    # Сохраняем контактные данные Telegram
    await state.update_data(
        telegram_contact=contact_info,
        telegram_user_id=message.from_user.id
    )

    # Удаляем предыдущее сообщение бота
    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    # Принимаем любой текст как "телефон" (или пропуск)
    phone_input = message.text.strip() if message.text else ""
    clean_phone = phone_input if phone_input else "—"

    await state.update_data(phone=clean_phone)

    sent = await message.answer(
        "Введите *наименование изделия*\\.\n\n"
        "Пример:\n"
        "_Шкаф Малиновая д15 кв25_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.item_type)

# ——— ОБРАБОТКА НАИМЕНОВАНИЯ ИЗДЕЛИЯ ———
@router.message(Form.item_type)
async def process_item_type(message: Message, state: FSMContext):
    item_name = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(item_type=item_name)

    sent = await message.answer(
        "Введите *толщину* и *материал* корпуса\\.\n\n"
        "Пример:\n"
        "_16мм ЛДСП Платиновый белый гладкий W980 SM Egger_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.carcass_material)
    
# ——— ОБРАБОТКА МАТЕРИАЛА КОРПУСА ———
@router.message(Form.carcass_material)
async def process_carcass_material(message: Message, state: FSMContext):
    material = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(carcass_material=material)

    sent = await message.answer(
        "Введите *тип*, *толщину* и *материал* фасадов\\.\n\n"
        "Пример:\n"
        "_Накладные 16мм ЛДСП Вишня Риверсайд Светлая K077 PW Kronospan_\n\n"
        "Если фасадов нет, поставьте прочерк\\."
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.facade_material)

# ——— ОБРАБОТКА МАТЕРИАЛА ФАСАДОВ ———
@router.message(Form.facade_material)
async def process_facade_material(message: Message, state: FSMContext):
    facade = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(facade_material=facade)

    sent = await message.answer(
        "Введите *материал видимых боковин*\\.\n\n"
        "Примеры:\n"
        "_16мм ЛДСП Дуб сонома светлый U103 ST9 Egger_\n"
        "_Материал фасадов_\n"
        "_Материал корпуса_\n\n"
        "Можете дополнительно более подробно описать нюансы своими словами\\."
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.visible_sides_material)

# ——— ОБРАБОТКА МАТЕРИАЛА ВИДИМЫХ БОКОВИН ———
@router.message(Form.visible_sides_material)
async def process_visible_sides_material(message: Message, state: FSMContext):
    visible_sides = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(visible_sides_material=visible_sides)

    sent = await message.answer(
        "Укажите *материал* и *способ установки задней стенки*\\.\n\n"
        "Примеры:\n"
        "_ХДФ 4мм в паз_\n"
        "_ЛДСП 16мм на конфирматы_\n"
        "_Без задней стенки_\n\n"
        "Если проектируется Кухня напишите: _стандартно_\n"
        "\\(или опишите свой вариант инсполнения\\)"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.back_wall)

# ——— ОБРАБОТКА ЗАДНЕЙ СТЕНКИ ———
@router.message(Form.back_wall)
async def process_back_wall(message: Message, state: FSMContext):
    back_wall = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(back_wall=back_wall)

    sent = await message.answer(
        "Укажите *толщину столешницы* и *толщину стеновой панели* \\(опционально для кухни\\)\\.\n\n"
        "Примеры:\n"
        "_Столешница 38мм, стеновая панель 6мм_\n"
        "_Столешница 38мм, без панели_\n"
        "_Без столешницы, стеновая панель 10мм_\n\n"
        "Если проектируется не Кухня или в изделии нет ни того и другого, поставьте прочерк\\."
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.countertop_and_wall_panel)

# ——— ОБРАБОТКА ТОЛЩИНЫ СТОЛЕШНИЦЫ И СТЕНОВОЙ ПАНЕЛИ ———
@router.message(Form.countertop_and_wall_panel)
async def process_countertop_and_wall_panel(message: Message, state: FSMContext):
    value = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(countertop_and_wall_panel=value)

    sent = await message.answer(
        "Есть ли в изделии козырёк\\?\n"
        "Если да, укажите *высоту козырька*\\.\n\n"
        "Пример:\n"
        "_60мм_\n\n"
        "Если козырёк отсутствует, напишите: _без козырька_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.canopy_height)

# ——— ОБРАБОТКА ВЫСОТЫ КОЗЫРЬКА ———
@router.message(Form.canopy_height)
async def process_canopy_height(message: Message, state: FSMContext):
    canopy = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(canopy_height=canopy)

    sent = await message.answer(
        "Есть ли в изделии цоколь\\?\n"
        "Если да, укажите *высоту* и *матерал цоколя*\\.\n\n"
        "Пример:\n"
        "_100мм материал корпуса_\n\n"
        "Если цоколь отсутствует, напишите: _без цоколя_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.plinth_height)

# ——— ОБРАБОТКА ВЫСОТЫ ЦОКОЛЯ ———
@router.message(Form.plinth_height)
async def process_plinth_height(message: Message, state: FSMContext):
    plinth = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(plinth_height=plinth)

    sent = await message.answer(
        "Укажите *толщину кромки корпуса и фасадов*, а также *вариант нанесения*\\.\n\n"
        "Варианты нанесения:\n"
        "• _Видимые стороны детали_\n"
        "• _Открытые стороны детали_\n"
        "• _Вкруг все детали_\n\n"
        "Пример:\n"
        "_Корпус 1мм вкруг все детали, Фасады 2мм_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.edge_banding)

# ——— ОБРАБОТКА КРОМКИ ———
@router.message(Form.edge_banding)
async def process_edge_banding(message: Message, state: FSMContext):
    edge_info = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(edge_banding=edge_info)

    sent = await message.answer(
        "Укажите *вариант исполнения дна* и *крышки* изделия\\.\n\n"
        "Возможные типы:\n"
        "• _Вкладной_ — деталь вставляется между стенок\n"
        "• _Накладной_ — деталь крепится поверх боковин\n\n"
        "Пример:\n"
        "_Дно вкладное, крышка накладная_\n\n"
        "Если проектируется Кухня напишите: _стандартно_\n"
        "\\(или опишите свой вариант инсполнения\\)"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.bottom_and_top_type)

# ——— ОБРАБОТКА ВАРИАНТА ДНА И КРЫШКИ ———
@router.message(Form.bottom_and_top_type)
async def process_bottom_and_top_type(message: Message, state: FSMContext):
    value = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(bottom_and_top_type=value)

    sent = await message.answer(
        "Укажите *технологические зазоры*:\n"
        "• _по бокам_ \\(суммарно или с каждой стороны\\)\n"
        "• _от потолка_\n\n"
        "Пример:\n"
        "_По бокам 10мм суммарно, от потолка 15мм_\n\n"
        "Если зазоры не нужны, напишите: _без зазоров_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.technical_gaps)

# ——— ОБРАБОТКА ТЕХНИЧЕСКИХ ЗАЗОРОВ ———
@router.message(Form.technical_gaps)
async def process_technical_gaps(message: Message, state: FSMContext):
    gaps = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(technical_gaps=gaps)

    sent = await message.answer(
        "Есть ли в изделии *петли*\\?\n\n"
        "Если да, укажите их *тип* и *способ крепления*\\.\n\n"
        "Типы петель:\n"
        "• _Крестовые_\n"
        "• _Прямые_\n\n"
        "Способ крепления:\n"
        "• _На саморезах_\n"
        "• _На евровинтах_\n\n"
        "Пример:\n"
        "_Крестовые на евровинтах_\n\n"
        "Если петель нет, напишите: _без петель_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.hinges)

# ——— ОБРАБОТКА ПЕТЛЕЙ ———
@router.message(Form.hinges)
async def process_hinges(message: Message, state: FSMContext):
    hinges_info = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(hinges=hinges_info)

    sent = await message.answer(
        "Есть ли в изделии *опоры*\\?\n\n"
        "Если да, укажите их тип:\n"
        "• _Кухонные_\n"
        "• _Подпятники_\n"
        "• _Регулируемые ножки_\n\n"
        "Пример:\n"
        "_Кухонные 60мм_\n\n"
        "Если опор нет \\(например, изделие навесное или на цоколе\\), напишите: _без опор_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.supports)

# ——— ОБРАБОТКА ОПОР ———
@router.message(Form.supports)
async def process_supports(message: Message, state: FSMContext):
    supports_info = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(supports=supports_info)

    sent = await message.answer(
        "Есть ли в изделии *ящики*\\?\n\n"
        "Если да, укажите *тип направляющих*:\n"
        "• _Скрытого монтажа_\n"
        "• _Шариковые направляющие_\n"
        "• _Метабоксы_\n"
        "• _Тандембоксы_\n\n"
        "Пример:\n"
        "_3 ящ скр монт Firmax с доводчиком, 1 ящ на шарик напр Firmax с доводчиком_\n\n"
        "Если ящиков нет, напишите: _без ящиков_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.drawers)

# ——— ОБРАБОТКА ЯЩИКОВ ———
@router.message(Form.drawers)
async def process_drawers(message: Message, state: FSMContext):
    drawers_info = message.text or ""

    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    await state.update_data(drawers=drawers_info)

    sent = await message.answer(
        "Добавьте *дополнительное описание изделия*, если необходимо:\n"
        "• Особенности конструкции\n"
        "• Пожелания по материалам\n"
        "• Примечания по замеру\n\n"
        "Если нет дополнений, напишите: _нет_"
    )
    await state.update_data(prev_bot_message_id=sent.message_id)
    await state.set_state(Form.additional_info)

# ——— ОБРАБОТКА ДОПОЛНИТЕЛЬНОГО ОПИСАНИЯ ———
@router.message(Form.additional_info)
async def process_additional_info(message: Message, state: FSMContext):
    data = await state.get_data()
    prev_id = data.get("prev_bot_message_id")
    if prev_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prev_id)
        except:
            pass

    # Сохраняем только текст
    description = message.text if message.text else "—"
    await state.update_data(additional_description=description)

    # Сразу финализируем
    await finalize_application(message, state)

# ——— ФИНАЛИЗАЦИЯ ———
async def finalize_application(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        "📩 Новая заявка на проектирование мебели\n\n"
        f"ФИО: {data.get('fio', '—')}\n"
        f"Telegram: {data.get('telegram_contact', '—')}\n"
        f"Телефон: {data.get('phone', '—')}\n"
        f"Изделие: {data.get('item_type', '—')}\n\n"
        f"Корпус: {data.get('carcass_material', '—')}\n"
        f"Фасады: {data.get('facade_material', '—')}\n"
        f"Видимые боковины: {data.get('visible_sides_material', '—')}\n"
        f"Задняя стенка: {data.get('back_wall', '—')}\n"
        f"Столешница / панель: {data.get('countertop_and_wall_panel', '—')}\n"
        f"Козырёк: {data.get('canopy_height', '—')}\n"
        f"Цоколь: {data.get('plinth_height', '—')}\n"
        f"Кромка: {data.get('edge_banding', '—')}\n"
        f"Дно / крышка: {data.get('bottom_and_top_type', '—')}\n"
        f"Тех. зазоры: {data.get('technical_gaps', '—')}\n"
        f"Петли: {data.get('hinges', '—')}\n"
        f"Опоры: {data.get('supports', '—')}\n"
        f"Ящики: {data.get('drawers', '—')}\n"
        f"Доп. описание: {data.get('additional_description', '—')}"
    )
    await bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=text, parse_mode=None)

    await state.clear()
    await message.answer(
        "Спасибо за заявку! ✨\n\n"
        "Мы создадим группу в Telegram по данному проекту и добавим в неё вас.\n"
        "В группе можно вести обсуждение и отправлять необходимые материалы.\n\n"
        "Хорошего дня! ✅\n\n"
        "Для новой заявки отправьте /start",
        parse_mode=None
    )

import os
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ——— ОСНОВНОЙ ЗАПУСК НА RENDER (WEBHOOK) ———
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)

    PORT = int(os.getenv("PORT", 8000))
    WEBHOOK_PATH = "/webhook"
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_URL')}{WEBHOOK_PATH}"

    await bot.set_webhook(url=WEBHOOK_URL)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    # Не завершаем программу — ждём соединений
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())