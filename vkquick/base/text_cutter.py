import abc
import typing as ty

import vkquick.events_generators.event
import vkquick.event_handling.message
from vkquick.current import fetch
import vkquick.wrappers.user
import vkquick.api
from vkquick.context import Context


class UnmatchedArgument:
    """
    Пустышка для значения аргумента, не прошедшего матчинг
    """


class TextCutter(abc.ABC):

    api = fetch(
        "api_invalid_argument", "api"
    )

    @abc.abstractmethod
    def cut_part(self, arguments_string: str) -> ty.Tuple[ty.Any, str]:
        """
        "Отрезает" аргумент с начала строки `arguments_string`,
        если его можно достать.

        Возвращает кортеж из:
        * Вытащенного значения аргумента текстовой команды. Если аргумент
        вытащить нельзя, первым значением кортежа возвращается `UnmatchedArgument`
        * Оставшаяся строка. Если аргумент не прошел, вернуть переданную строку
        """

    @staticmethod
    def cut_part_lite(
        regex: ty.Pattern,
        arguments_string: str,
        factory: ty.Callable[[ty.Match], ty.Any] = lambda match: match,
    ) -> ty.Tuple[ty.Any, str]:
        """
        Инкапсулирует логику, часто применяющуюся к `cut_part`
        """
        matched = regex.match(arguments_string)
        if matched:
            new_arguments_string = arguments_string[matched.end() :]
            return factory(matched), new_arguments_string

        return UnmatchedArgument, arguments_string

    async def invalid_value(
        self, argument_position: int, seems_missing: bool, context: Context,
    ) -> None:
        """
        Дефолтный текст для некорректных аргументов
        """
        seems_missing_text = ""
        if seems_missing:
            seems_missing_text = (
                "Вероятно, при вызове команды был пропущен аргумент."
            )

        extra_info = self.usage_description()
        if extra_info:
            extra_info = f"💡 {extra_info}"

        user = await self.api.users.get(
            allow_cache_=True,
            user_ids=event.get_message_object().from_id
        )
        user = vkquick.wrappers.user.User(user[0])
        mention = user.mention("{fn}")
        response = (
            f"💥 {mention}, команда вызвана с некорректным по значению аргументом "
        )
        response = (
            f"💥 {mention}, при попытке достать аргумент №[id0|{argument_position}]"
            f" ({argument_name}) получено некорректное значение "
            f"`{argument_string}`. {seems_missing_text}\n\n{extra_info}"
        )
        await context.message.reply(
            response, disable_mentions=True
        )

    @staticmethod
    def usage_description() -> str:
        return ""
