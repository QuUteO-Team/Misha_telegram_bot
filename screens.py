import datetime
import random

from hammett.core import Screen, Button
from hammett.core.constants import SourceTypes
from hammett.core.mixins import StartMixin
from hammett.core.handlers import register_button_handler, register_typing_handler

user_links = {}


MAIN_MENU_DESCRIPTION =  "🔗 <b>Link Keeper Bot</b>\n\nПривет! Я помогу тебе сохранять интересные ссылки.\n"

ADD_LINK_MENU_DESCRIPTION = "📥 <b>Добавление ссылки</b>\n\nОтправь мне ссылку (начинается с http:// или https://)\n"

RANDOM_MENU_DESCRIPTION = "🎲 <b>Случайная ссылка</b>"

class Link:
    def __init__(self, url, title=""):
        self.url = url
        self.title = title if title else url[:30] + "..."
        self.id = str(hash(url + str(datetime.datetime.now())))[:8]


"""Main Screen"""
class MainMenuScreen(StartMixin, Screen):

    description = MAIN_MENU_DESCRIPTION

    async def add_default_keyboard(self, _update, context):
        """get user id from telegram and """
        return [
            [
                Button('📥 Добавить ссылку', AddLinkScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE,),
                Button('🎲 Случайная ссылка', RandomLinkScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE,)
            ],
            [
                Button('📋 Все ссылки', AllLinksScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE),
            ],
        ]

class AddLinkScreen(Screen):
    """Add Link Keyboard Screen"""

    description = MAIN_MENU_DESCRIPTION

    async def add_default_keyboard(self, _update, context):
        return [
            [
                Button('◀️ Назад', MainMenuScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE),
            ]
        ]

    @register_typing_handler
    async def handle_message(self, update, context):
        text = update.message.text

        if text.startswith(('http://', 'https://')):
            user_id = update.effective_user.id

            if user_id not in user_links:
                user_links[user_id] = []

            new_link = Link(text)
            user_links[user_id].append(new_link)

            if 'links' not in context.user_data:
                context.user_data['links'] = []
            context.user_data['links'].append(new_link.__dict__)

            await update.message.reply_text(
                f"✅ Ссылка сохранена!\n\n"
                f"<b>{new_link.title}</b>\n"
                f"ID: {new_link.id}",
                parse_mode='HTML'
            )

            return await MainMenuScreen().jump(update, context)
        else:
            await update.message.reply_text(
                "❌ Это не похоже на ссылку. Отправь URL, начинающийся с http:// или https://"
            )
            return None

class RandomLinkScreen(Screen):

    description = RANDOM_MENU_DESCRIPTION

    async def get_description(self, update, context):
        user_id = update.effective_user.id
        links = user_links.get(user_id, [])

        if not links:
            return (
                "🎲 <b>Случайная ссылка</b>\n\n"
                "У вас пока нет сохраненных ссылок.\n"
                "Добавьте первую!"
            )

        random_link = random.choice(links)
        context.user_data["current_link"] = random_link.__dict__

        return (
            f"🎲 <b>Случайная ссылка</b>\n\n"
            f"<b>{random_link.title}</b>\n"
            f"ID: {random_link.id}\n"
            f"Добавлено: {random_link.date}\n\n"
            f"{random_link.url}"
        )

    async def add_default_keyboard(self, _update, context):
        buttons = [
            [Button('🎲 Еще раз', RandomLinkScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE)],
            [Button('📋 Все ссылки', AllLinksScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE)],
            [Button('◀️ Главное меню', MainMenuScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE)],
        ]

        if context.user_data.get('current_link'):
            buttons.insert(0, [
                Button('❌ Удалить эту ссылку', self.delete_current_link,
                       source_type=SourceTypes.HANDLER_SOURCE_TYPE)
            ])

        return buttons

    @register_button_handler
    async def delete_current_link(self, update, context):
        """Удалить текущую ссылку"""
        user_id = update.effective_user.id
        current_link = context.user_data.get('current_link')

        if current_link and user_id in user_links:
            user_links[user_id] = [link for link in user_links[user_id]
                                   if link.id != current_link['id']]

            await update.effective_message.reply_text(
                f"✅ Ссылка удалена: {current_link['title']}"
            )

            context.user_data['current_link'] = None

        return await RandomLinkScreen().jump(update, context)


class AllLinksScreen(Screen):
    """Экран со списком всех ссылок"""

    async def get_description(self, update, context):
        user_id = update.effective_user.id
        links = user_links.get(user_id, [])

        if not links:
            return (
                "📋 <b>Все сохраненные ссылки</b>\n\n"
                "У вас пока нет ссылок. Добавьте первую!"
            )

        return f"📋 <b>Все ссылки ({len(links)})</b>\n\nВыберите ссылку для просмотра:"


