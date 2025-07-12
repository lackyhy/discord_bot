from enum import Enum
from discord import Color

# Каналы для логов
class LogChannels:
    MAIN = 1228715024957308960
    WARNINGS = 1245073655982194752
    SUGGESTIONS = 1244953316232790046

# Цвета для эмбедов
class Colors:
    SUCCESS = Color.green()
    ERROR = Color.red()
    WARNING = Color.yellow()
    INFO = Color.blue()

# Роли
class Roles:
    ADMIN = 1223280335454867476
    MODERATOR = 1077154622835273758
    HELPER = 1072941217937109014
    
# Максимальные значения
class Limits:
    MAX_WARNS = 5
    MAX_NICKNAME_LENGTH = 32
    MAX_CHANNEL_NAME_LENGTH = 100
    CLEAR_MESSAGE_LIMIT = 1000

# Временные интервалы (в секундах)
class TimeIntervals:
    RESTART_INTERVAL = 2400  # 40 минут
    MUTE_COOLDOWN = 300     # 5 минут
    WARN_COOLDOWN = 3600    # 1 час

# Сообщения ошибок
class ErrorMessages:
    NO_PERMISSION = "У вас недостаточно прав для использования этой команды!"
    INVALID_USER = "Указан неверный пользователь!"
    CHANNEL_NOT_FOUND = "Канал не найден!"
    ROLE_NOT_FOUND = "Роль не найдена!"
    BOT_NO_PERMISSION = "У бота недостаточно прав для выполнения этого действия!"

# Сообщения успеха
class SuccessMessages:
    WARN_ADDED = "Предупреждение успешно выдано!"
    CHANNEL_LOCKED = "Канал успешно заблокирован!"
    CHANNEL_UNLOCKED = "Канал успешно разблокирован!"
    ROLE_ADDED = "Роль успешно выдана!"
    ROLE_REMOVED = "Роль успешно снята!"

# Эмодзи
class Emojis:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    LOADING = "⏳"
    STAR = "⭐"
    CROWN = "👑"