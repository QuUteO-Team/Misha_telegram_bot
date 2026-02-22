import datetime
import random

from hammett.conf import settings
from hammett.core import Screen, Button
from hammett.core.constants import SourceTypes
from hammett.core.mixins import StartMixin
from hammett.core.handlers import register_typing_handler, register_button_handler
from hammett.core.permission import ignore_permissions

from permision import PaywallPermission

user_links = {}

MAIN_MENU_DESCRIPTION = "🔗 <b>Link Keeper Bot</b>\n\nПривет! Я помогу тебе сохранять интересные ссылки.\n"

ADD_LINK_MENU_DESCRIPTION = "📥 <b>Добавление ссылки</b>\n\nОтправь мне ссылку (начинается с http:// или https://)\n"

RANDOM_MENU_DESCRIPTION = "🎲 <b>Случайная ссылка</b>"

ALL_LINKS_MENU_DESCRIPTION = "📋 <b>Все ссылки</b>\n\nСписок всех сохраненных ссылок:"

FAKE_PAYMENT_SCREEN_DESCRIPTION = (
    'To continue using the bot, you need to make a <i>fake</i> payment.\n\nDo you want to continue?'
)

PAYMENT_SCREEN_DESCRIPTION = (
    'Welcome to HammettPaywallBot!\n'
    '\n'
    "Now you see the <b>Payment</b> screen, and you <i>won't see any other screens</i> until "
    'you make a <i>fake</i> payment. So, if you type the /start command, '
    "you'll just get this screen again."
)


class Link:
    def __init__(self, url, title=""):
        self.url = url
        self.title = title if title else url[:30] + "..."
        self.id = str(hash(url + str(datetime.datetime.now())))[:8]


class MainMenuScreen(StartMixin, Screen):
    description = MAIN_MENU_DESCRIPTION

    async def add_default_keyboard(self, _update, context):
        return [
            [
                Button('📥 Добавить ссылку', AddLinkScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE),
                Button('🎲 Случайная ссылка', RandomLinkScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE, )
            ],
            [
                Button('📋 Все ссылки', AllLinksScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE),
            ],
        ]


class AddLinkScreen(Screen):
    description = ADD_LINK_MENU_DESCRIPTION

    async def add_default_keyboard(self, _update, context):
        return [
            [Button('◀️ Назад', MainMenuScreen, source_type=SourceTypes.MOVE_SOURCE_TYPE)],
        ]

    async def get_description(self, update, context):
        if context.user_data.get("text_input"):
            return (
                f'✅ Ссылка успешно сохранена!\n'
                f'\n'
                f'{context.user_data["text_input"]}\n'
                f'\n'
                f'Вы можете добавить ещё одну ссылку или вернуться в главное меню.'
            )

        return "📝 Отправьте мне ссылку (должна начинаться с http:// или https://)"

    @register_typing_handler
    async def handle_text_input(self, update, context):
        """Сохранение ссылки в контекст"""
        text_input = update.message.text.strip()

        if link_check(text_input):
            user_id = update.effective_user.id

            if user_id not in user_links:
                user_links[user_id] = []

            new_link = Link(text_input)
            user_links[user_id].append(new_link)

            context.user_data["text_input"] = new_link.url

            return await self.jump(update, context)
        else:
            await update.message.reply_text(
                "❌ Это не похоже на корректную ссылку.\n"
                "Ссылка должна начинаться с http:// или https://"
            )
            return await self.jump(update, context)


def link_check(text_input):
    text = text_input.strip()
    return text.startswith(('http://', 'https://'))


class RandomLinkScreen(Screen):
    description = RANDOM_MENU_DESCRIPTION

    async def add_default_keyboard(self, _update, context):
        keyboard = [
            [Button('🔄 Ещё раз', self.__class__, source_type=SourceTypes.MOVE_SOURCE_TYPE)],
            [Button('◀️ В главное меню', MainMenuScreen, source_type=SourceTypes.MOVE_SOURCE_TYPE)],
        ]

        if context.user_data.get("random_link"):
            keyboard.insert(0, [
                Button('🔗 Открыть ссылку',
                       context.user_data['random_link'].url,
                       source_type=SourceTypes.URL_SOURCE_TYPE)
            ])

        return keyboard

    async def get_description(self, update, context):
        user_id = update.effective_user.id

        if user_id not in user_links or len(user_links[user_id]) == 0:
            return "❌ У вас пока нет сохраненных ссылок"

        random_link = random.choice(user_links[user_id])
        context.user_data["random_link"] = random_link
        return (
            f"🎲 <b>Случайная ссылка</b>\n\n"
            f"<b>Название:</b> {random_link.title}\n"
            f"<b>URL:</b> {random_link.url}\n"
            f"<b>ID:</b> {random_link.id}"
        )


class AllLinksScreen(Screen):
    description = ALL_LINKS_MENU_DESCRIPTION

    async def add_default_keyboard(self, update, context):
        keyboard = []

        if context.user_data.get('all_links'):
            links = context.user_data['all_links']
            for i, link in enumerate(links[:10], 1):
                title = link.title[:15] + "..." if len(link.title) > 15 else link.title
                keyboard.append([
                    Button(f'{i}. {title}', url=link.url, source_type=SourceTypes.URL_SOURCE_TYPE)
                ])

            if len(links) > 10:
                keyboard.append([
                    Button('📚 Показать все (следующие 10)', self.show_next_links,
                           source_type=SourceTypes.CALLBACK_SOURCE_TYPE)
                ])

        keyboard.extend([
            [Button('🔄 Обновить', self.__class__, source_type=SourceTypes.JUMP_SOURCE_TYPE)],
            [Button('🎲 Случайная ссылка', RandomLinkScreen, source_type=SourceTypes.JUMP_SOURCE_TYPE)],
            [Button('◀️ В главное меню', MainMenuScreen, source_type=SourceTypes.MOVE_SOURCE_TYPE)],
        ])

        return keyboard

    async def get_description(self, update, context):
        user_id = update.effective_user.id

        if user_id not in user_links or len(user_links[user_id]) == 0:
            return "📭 У вас пока нет сохраненных ссылок"

        links = user_links[user_id]

        links_list = []
        for i, link in enumerate(links, 1):
            links_list.append(f"{i}. <b>{link.title}</b>\n   🔗 {link.url}\n   🆔 {link.id}")

        context.user_data['all_links'] = links

        return (
            f"{self.description}\n\n"
            f"Всего ссылок: {len(links)}\n\n"
            f"{chr(10).join(links_list)}"
        )

    async def show_next_links(self, update, context):
        """Показывает следующие 10 ссылок"""
        user_id = update.effective_user.id

        if user_id not in user_links:
            return await MainMenuScreen().jump(update, context)

        page = context.user_data.get('links_page', 1)
        next_page = page + 1

        links = user_links[user_id]
        start_idx = (next_page - 1) * 10
        end_idx = start_idx + 10
        page_links = links[start_idx:end_idx]

        if not page_links:
            context.user_data['links_page'] = 1
            return await self.jump(update, context)

        links_list = []
        for i, link in enumerate(page_links, start_idx + 1):
            links_list.append(f"{i}. <b>{link.title}</b>\n   🔗 {link.url}\n   🆔 {link.id}")

        context.user_data['links_page'] = next_page
        context.user_data['page_links'] = page_links

        await update.callback_query.edit_message_text(
            f"📋 <b>Все ссылки (страница {next_page})</b>\n\n"
            f"Ссылки {start_idx + 1}-{min(end_idx, len(links))} из {len(links)}\n\n"
            f"{chr(10).join(links_list)}",
            reply_markup=await self.get_page_keyboard(update, context, next_page, len(links)),
            parse_mode='HTML'
        )

        return None

    async def get_page_keyboard(self, update, context, current_page, total_links):
        """Создает клавиатуру для страницы со ссылками"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        if context.user_data.get('page_links'):
            for i, link in enumerate(context.user_data['page_links']):
                title = link.title[:15] + "..." if len(link.title) > 15 else link.title
                keyboard.append([
                    InlineKeyboardButton(f'{i + 1 + (current_page - 1) * 10}. {title}', url=link.url)
                ])

        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton('⬅️ Предыдущая', callback_data='prev_page'))
        if current_page * 10 < total_links:
            nav_buttons.append(InlineKeyboardButton('Следующая ➡️', callback_data='next_page'))

        if nav_buttons:
            keyboard.append(nav_buttons)

        # Добавляем кнопки действий
        keyboard.extend([
            [InlineKeyboardButton('🔄 Обновить', callback_data='refresh_links')],
            [InlineKeyboardButton('🎲 Случайная ссылка', callback_data='random_link')],
            [InlineKeyboardButton('◀️ Главное меню', callback_data='main_menu')],
        ])

        return InlineKeyboardMarkup(keyboard)


class FakePaymentScreen(Screen):
    """The class implements FakePaymentScreen."""

    description = FAKE_PAYMENT_SCREEN_DESCRIPTION

    async def add_default_keyboard(self, _update, _context):
        """Set up the keyboard for the screen."""
        return [
            [
                Button('❌ No', PaymentScreen, source_type=SourceTypes.MOVE_SOURCE_TYPE),
                Button(
                    '✅ Yes',
                    self.handle_fake_payment,
                    source_type=SourceTypes.HANDLER_SOURCE_TYPE,
                ),
            ],
        ]

    @ignore_permissions([PaywallPermission])
    @register_button_handler
    async def handle_fake_payment(self, update, context):
        """Handle a button click and process a fake payment.

        Please note that this handler ignores `PaywallPermission`,
        which means that `has_permission` of `PaywallPermission`
        is not called before it is invoked.
        """
        user = update.effective_user
        settings.PAID_USERS.append(user.id)

        return await MainMenuScreen().move(update, context)

    @ignore_permissions([PaywallPermission])
    async def move(self, update, context, **kwargs):
        """Switch to the screen re-rendering the previous message.

        Please note that this handler ignores `PaywallPermission`,
        which means that `has_permission` of `PaywallPermission`
        is not called before it is invoked.
        """
        return await super().move(update, context, **kwargs)


class PaymentScreen(Screen):
    """The class implements PaymentScreen, which appears when the user hasn't made a payment."""

    description = PAYMENT_SCREEN_DESCRIPTION

    async def add_default_keyboard(self, _update, _context):
        """Set up the keyboard for the screen."""
        return [
            [
                Button('💳 Fake Pay', FakePaymentScreen, source_type=SourceTypes.MOVE_SOURCE_TYPE),
            ],
        ]

    @ignore_permissions([PaywallPermission])
    async def move(self, update, context, **kwargs):
        """Switch to the screen re-rendering the previous message.

        Please note that this handler ignores `PaywallPermission`,
        which means that `has_permission` of `PaywallPermission`
        is not called before it is invoked.
        """
        return await super().move(update, context, **kwargs)
