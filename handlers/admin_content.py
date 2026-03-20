import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import settings
from database.content import (
    get_categories, get_levels, get_lessons,
    add_category, add_level, add_lesson,
    delete_category, delete_level, delete_lesson
)
from keyboards.admin import admin_content_kb, back_admin_kb
from keyboards.user import confirm_kb, cancel_kb

router = Router()
logger = logging.getLogger(__name__)


def is_admin(uid): return uid in settings.admin_id_list


class ContentState(StatesGroup):
    # Category
    cat_name = State()
    cat_emoji = State()
    cat_is_vip = State()
    # Level
    lvl_cat_id = State()
    lvl_name = State()
    lvl_is_vip = State()
    # Lesson
    les_level_id = State()
    les_title = State()
    les_description = State()
    les_code = State()
    les_is_free = State()
    les_is_vip = State()
    les_content = State()


# ─── ADD CATEGORY ─────────────────────────────────────────────

@router.callback_query(F.data == "adm:add_cat")
async def adm_add_cat(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await state.set_state(ContentState.cat_name)
    await call.message.edit_text(
        "📚 <b>Add Category</b>\n\nEnter category name:",
        reply_markup=cancel_kb()
    )
    await call.answer()


@router.message(ContentState.cat_name)
async def cat_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(ContentState.cat_emoji)
    await message.answer("Enter emoji for this category (or send '-' to skip):", reply_markup=cancel_kb())


@router.message(ContentState.cat_emoji)
async def cat_emoji_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    emoji = message.text.strip() if message.text.strip() != "-" else "📚"
    await state.update_data(cat_emoji=emoji)
    await state.set_state(ContentState.cat_is_vip)
    await message.answer("Is this a VIP category? (yes/no):", reply_markup=cancel_kb())


@router.message(ContentState.cat_is_vip)
async def cat_vip_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    is_vip = 1 if message.text.strip().lower() in ("yes", "y", "1") else 0
    data = await state.get_data()
    await state.clear()
    cat_id = await add_category(data["cat_name"], emoji=data["cat_emoji"], is_vip=is_vip)
    await message.answer(
        f"✅ <b>Category created!</b>\n\n"
        f"ID: <code>{cat_id}</code>\n"
        f"Name: {data['cat_name']}\n"
        f"VIP: {'Yes 👑' if is_vip else 'No'}",
        reply_markup=admin_content_kb()
    )


# ─── LIST CATEGORIES ──────────────────────────────────────────

@router.callback_query(F.data == "adm:list_cats")
async def adm_list_cats(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    cats = await get_categories()
    if not cats:
        await call.answer("No categories yet.", show_alert=True)
        return
    text = "📚 <b>Categories:</b>\n\n"
    for c in cats:
        text += f"• <code>{c['id']}</code> {c['emoji']} <b>{c['name']}</b>{'  👑' if c['is_vip'] else ''}\n"
    text += "\n<i>To delete: /del_cat &lt;id&gt;</i>"
    await call.message.edit_text(text, reply_markup=admin_content_kb())
    await call.answer()


@router.message(F.text.startswith("/del_cat"))
async def del_cat(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /del_cat <id>")
        return
    await delete_category(int(parts[1]))
    await message.answer(f"✅ Category {parts[1]} deleted.")


# ─── ADD LEVEL ────────────────────────────────────────────────

@router.callback_query(F.data == "adm:add_lvl")
async def adm_add_lvl(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    cats = await get_categories()
    if not cats:
        await call.answer("No categories yet. Add a category first.", show_alert=True)
        return
    text = "📖 <b>Add Level</b>\n\nEnter the category ID:\n\n"
    for c in cats:
        text += f"• <code>{c['id']}</code> — {c['name']}\n"
    await state.set_state(ContentState.lvl_cat_id)
    await call.message.edit_text(text, reply_markup=cancel_kb())
    await call.answer()


@router.message(ContentState.lvl_cat_id)
async def lvl_cat_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        cat_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid ID. Enter a number:")
        return
    await state.update_data(lvl_cat_id=cat_id)
    await state.set_state(ContentState.lvl_name)
    await message.answer("Enter level name:", reply_markup=cancel_kb())


@router.message(ContentState.lvl_name)
async def lvl_name_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(lvl_name=message.text.strip())
    await state.set_state(ContentState.lvl_is_vip)
    await message.answer("Is this a VIP level? (yes/no):", reply_markup=cancel_kb())


@router.message(ContentState.lvl_is_vip)
async def lvl_vip_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    is_vip = 1 if message.text.strip().lower() in ("yes", "y", "1") else 0
    data = await state.get_data()
    await state.clear()
    lvl_id = await add_level(data["lvl_cat_id"], data["lvl_name"], is_vip=is_vip)
    await message.answer(
        f"✅ <b>Level created!</b> ID: <code>{lvl_id}</code>",
        reply_markup=admin_content_kb()
    )


@router.callback_query(F.data == "adm:list_lvls")
async def adm_list_lvls(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    cats = await get_categories()
    text = "📖 <b>Levels:</b>\n\n"
    found = False
    for c in cats:
        lvls = await get_levels(c["id"])
        if lvls:
            found = True
            text += f"<b>{c['name']}</b>:\n"
            for lv in lvls:
                text += f"  • <code>{lv['id']}</code> {lv['emoji']} {lv['name']}{'  👑' if lv['is_vip'] else ''}\n"
    if not found:
        await call.answer("No levels yet.", show_alert=True)
        return
    text += "\n<i>To delete: /del_lvl &lt;id&gt;</i>"
    await call.message.edit_text(text, reply_markup=admin_content_kb())
    await call.answer()


@router.message(F.text.startswith("/del_lvl"))
async def del_lvl(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /del_lvl <id>")
        return
    await delete_level(int(parts[1]))
    await message.answer(f"✅ Level {parts[1]} deleted.")


# ─── ADD LESSON ───────────────────────────────────────────────

@router.callback_query(F.data == "adm:add_les")
async def adm_add_les(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await state.set_state(ContentState.les_level_id)
    await call.message.edit_text(
        "📝 <b>Add Lesson</b>\n\nEnter the Level ID (use /adm:list_lvls to find IDs):",
        reply_markup=cancel_kb()
    )
    await call.answer()


@router.message(ContentState.les_level_id)
async def les_level_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        level_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid ID.")
        return
    await state.update_data(les_level_id=level_id)
    await state.set_state(ContentState.les_title)
    await message.answer("Enter lesson title:", reply_markup=cancel_kb())


@router.message(ContentState.les_title)
async def les_title_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(les_title=message.text.strip())
    await state.set_state(ContentState.les_description)
    await message.answer("Enter lesson description (or '-' to skip):", reply_markup=cancel_kb())


@router.message(ContentState.les_description)
async def les_desc_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    desc = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(les_description=desc)
    await state.set_state(ContentState.les_code)
    await message.answer("Enter unlock code (or '-' for none):", reply_markup=cancel_kb())


@router.message(ContentState.les_code)
async def les_code_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    code = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(les_code=code)
    await state.set_state(ContentState.les_is_free)
    await message.answer("Is this lesson free? (yes/no):", reply_markup=cancel_kb())


@router.message(ContentState.les_is_free)
async def les_free_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    is_free = 1 if message.text.strip().lower() in ("yes", "y", "1") else 0
    await state.update_data(les_is_free=is_free)
    await state.set_state(ContentState.les_is_vip)
    await message.answer("Is this a VIP lesson? (yes/no):", reply_markup=cancel_kb())


@router.message(ContentState.les_is_vip)
async def les_vip_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    is_vip = 1 if message.text.strip().lower() in ("yes", "y", "1") else 0
    await state.update_data(les_is_vip=is_vip)
    await state.set_state(ContentState.les_content)
    await message.answer(
        "📎 Now send the lesson content:\n\n"
        "• Forward a message from your private channel, OR\n"
        "• Upload a file directly (video, doc, photo, etc.)",
        reply_markup=cancel_kb()
    )


@router.message(ContentState.les_content)
async def les_content_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    await state.clear()

    content_type = "forward"
    file_id = None
    msg_id = None
    channel_id = None

    if message.forward_from_chat:
        content_type = "forward"
        msg_id = message.forward_from_message_id
        channel_id = str(message.forward_from_chat.id)
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
    elif message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.audio:
        content_type = "audio"
        file_id = message.audio.file_id
    elif message.voice:
        content_type = "voice"
        file_id = message.voice.file_id
    elif message.video_note:
        content_type = "video_note"
        file_id = message.video_note.file_id
    elif message.animation:
        content_type = "animation"
        file_id = message.animation.file_id
    else:
        await message.answer("⚠️ Unsupported content type. Lesson not saved.")
        return

    les_id = await add_lesson(
        level_id=data["les_level_id"],
        title=data["les_title"],
        description=data.get("les_description"),
        content_type=content_type,
        file_id=file_id,
        message_id=msg_id,
        channel_id=channel_id,
        unlock_code=data.get("les_code"),
        is_free=data.get("les_is_free", 0),
        is_vip=data.get("les_is_vip", 0),
    )
    await message.answer(
        f"✅ <b>Lesson created!</b>\n\n"
        f"ID: <code>{les_id}</code>\n"
        f"Title: {data['les_title']}\n"
        f"Type: {content_type}",
        reply_markup=admin_content_kb()
    )


@router.callback_query(F.data == "adm:list_les")
async def adm_list_les(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    cats = await get_categories()
    text = "📝 <b>Lessons:</b>\n\n"
    found = False
    for c in cats:
        for lv in await get_levels(c["id"]):
            lessons = await get_lessons(lv["id"])
            if lessons:
                found = True
                text += f"<b>{c['name']} → {lv['name']}</b>\n"
                for les in lessons:
                    lock = "✅" if les["is_free"] else ("👑" if les["is_vip"] else "🔒")
                    text += f"  {lock} <code>{les['id']}</code> {les['title']}\n"
    if not found:
        await call.answer("No lessons yet.", show_alert=True)
        return
    text += "\n<i>To delete: /del_les &lt;id&gt;</i>"
    await call.message.edit_text(text[:4000], reply_markup=admin_content_kb())
    await call.answer()


@router.message(F.text.startswith("/del_les"))
async def del_les(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /del_les <id>")
        return
    await delete_lesson(int(parts[1]))
    await message.answer(f"✅ Lesson {parts[1]} deleted.")
