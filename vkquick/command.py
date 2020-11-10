from __future__ import annotations
import re
import time
import inspect
import typing as ty

from vkquick.utils import AttrDict, sync_async_run, sync_async_callable
from vkquick.context import Context
from vkquick.base.handling_status import HandlingStatus
from vkquick.base.filter import Filter, Decision
from vkquick.events_generators.event import Event
from vkquick.base.text_cutter import TextCutter, UnmatchedArgument
from vkquick.message import Message, ClientInfo


# TODO: payload
class Command(Filter):
    def __init__(
        self,
        *,
        prefixes: ty.Iterable[str] = (),
        names: ty.Iterable[str] = (),
        title: ty.Optional[str] = None,
        description: ty.Optional[str] = None,
        routing_command_re_flags: re.RegexFlag = re.IGNORECASE,
        on_invalid_argument: ty.Optional[
            ty.Dict[str, sync_async_callable([Context], ...), ty.Any]
        ] = None,
        on_invalid_filter: ty.Optional[
            ty.Dict[Filter, sync_async_callable([Context], ...), ty.Any]
        ] = None,
        extra: ty.Optional[dict] = None,
    ):
        self._prefixes = tuple(prefixes)
        self._names = tuple(names)
        self._description = description
        self._routing_command_re_flags = routing_command_re_flags
        self._extra = AttrDict(extra or {})
        self._description = description
        self._title = title

        self.filters: ty.List[Filter] = [self]
        self._reaction_arguments: ty.List[ty.Tuple[str, ty.Any]] = []
        self._reaction_context_argument_name = None

        self._invalid_filter_handlers = on_invalid_filter or {}
        # TODO: available for help_ command
        self._invalid_argument_handlers = on_invalid_argument or {}

        self._build_routing_regex()
        
    @property
    def reaction_arguments(self):
        return self._reaction_arguments

    @property
    def title(self):
        return self._title

    @property
    def description(self) -> str:
        if self._description is None:
            return "Описание отсутствует"
        return self._description

    @property
    def extra(self) -> AttrDict:
        """
        Extra values
        """
        return self._extra

    @property
    def prefixes(self) -> ty.Tuple[str]:
        return self._prefixes

    @prefixes.setter
    def prefixes(self, value: ty.Iterable[str]) -> None:
        self._prefixes = tuple(value)
        self._build_routing_regex()

    @property
    def names(self) -> ty.Tuple[str]:
        return self._names

    @names.setter
    def names(self, value: ty.Iterable[str]) -> None:
        self._prefixes = tuple(value)
        self._build_routing_regex()

    def __call__(self, reaction: sync_async_callable(..., None)):
        self.reaction = reaction
        self._resolve_arguments()
        if self._description is None:
            self._description = inspect.getdoc(reaction)
        if self._title is None:
            self._title = reaction.__name__
        return self

    async def handle_event(self, event: Event):
        start_handling_stamp = time.monotonic()
        if event.from_group:
            message = Message.from_group_event(event)
            client_info = ClientInfo.parse_obj(event.object.client_info())
        else:
            message = await Message.from_user_event(event)
            client_info = None
        context = Context(
            source_event=event, message=message, client_info=client_info,
        )
        (
            passed_every_filter,
            filters_decision,
        ) = await self.run_through_filters(context)
        if not passed_every_filter:
            end_handling_stamp = time.monotonic()
            taken_time = end_handling_stamp - start_handling_stamp
            return HandlingStatus(
                reaction_name=self.reaction.__name__,
                all_filters_passed=False,
                filters_response=filters_decision,
                taken_time=taken_time,
            )

        await self.call_reaction(context)

        end_handling_stamp = time.monotonic()
        taken_time = end_handling_stamp - start_handling_stamp
        return HandlingStatus(
            reaction_name=self.reaction.__name__,
            all_filters_passed=True,
            filters_response=filters_decision,
            passed_arguments=context.extra.reaction_arguments(),
            taken_time=taken_time,
        )

    async def run_through_filters(
        self, context: Context
    ) -> ty.Tuple[bool, ty.List[ty.Tuple[str, Decision]]]:
        decisions = []
        for filter_ in self.filters:
            decision = await sync_async_run(filter_.make_decision(context))
            decisions.append((filter_.__class__.__name__, decision))
            if not decision.passed:
                return False, decisions

        return True, decisions

    def on_invalid_filter(
        self, filter_: Filter, /
    ) -> ty.Callable[[sync_async_callable([Context], ...)], ...]:
        def wrapper(handler):
            self._invalid_filter_handlers[filter_] = handler
            handler_parameters = inspect.signature(handler).parameters
            length_parameters = len(handler_parameters)
            if length_parameters != 1:
                raise KeyError(
                    f"Invalid filter handler should "
                    f"have only the one argument for "
                    f"context, got {length_parameters}"
                )
            return handler

        return wrapper

    def on_invalid_argument(
        self, name: str
    ) -> ty.Callable[[sync_async_callable([Context], ...)], ...]:
        def wrapper(handler):
            self._invalid_argument_handlers[name] = handler
            handler_parameters = inspect.signature(handler).parameters
            length_parameters = len(handler_parameters)
            if length_parameters != 1:
                raise KeyError(
                    f"Invalid argument handler should "
                    f"have only the one argument for "
                    f"context, got {length_parameters}"
                )
            return handler

        return wrapper

    async def make_decision(self, context: Context):
        matched = self._command_routing_regex.match(context.message.text)
        if matched:
            arguments_string = context.message.text[matched.end() :]
        else:
            return Decision(
                False,
                f"Команда не подходит под шаблон `{self._command_routing_regex.pattern}`",
            )

        is_parsed, arguments = await self.init_text_arguments(
            arguments_string, context
        )

        if not is_parsed:
            if not arguments:
                return Decision(
                    False,
                    "Команде были переданы аргументы, которые не обозначены",
                )

            unparsed_argument_name, _ = arguments.popitem()

            return Decision(
                False,
                f"Не удалось выявить значение для аргумента `{unparsed_argument_name}`",
            )
        context.extra.reaction_arguments = arguments
        return Decision(True, "Команда полностью подходит")

    async def init_text_arguments(
        self, arguments_string: str, context: Context
    ) -> ty.Tuple[bool, dict]:
        arguments = {}
        if self._reaction_context_argument_name is not None:
            arguments[self._reaction_context_argument_name] = context

        new_arguments_string = arguments_string.lstrip()
        for name, cutter in self._reaction_arguments:
            parsed_value, new_arguments_string = await sync_async_run(
                cutter.cut_part(new_arguments_string)
            )
            new_arguments_string = new_arguments_string.lstrip()
            arguments[name] = parsed_value
            if parsed_value is UnmatchedArgument:
                if name in self._invalid_argument_handlers:
                    response = await sync_async_run(
                        self._invalid_argument_handlers[name](context)
                    )
                    if response is not None:
                        await context.message.reply(response)
                else:
                    for position, arg in enumerate(self._reaction_arguments):
                        if arg[0] == name:
                            await sync_async_run(
                                cutter.invalid_value(
                                    position,
                                    not new_arguments_string,
                                    context,
                                )
                            )
                            break
                return False, arguments

        if new_arguments_string:
            return False, arguments
        return True, arguments

    async def call_reaction(self, context: Context) -> None:
        result = self.reaction(**context.extra["reaction_arguments"])
        result = await sync_async_run(result)
        if result is not None:
            await context.message.reply(message=result)

    def _resolve_arguments(self):
        parameters = inspect.signature(self.reaction).parameters
        parameters = list(parameters.items())
        if not parameters:
            return
        seems_context, *cutters = parameters

        # def foo(ctx: Context): ...
        # def foo(ctx=Context)
        # def foo(ctx): ...
        if (
            seems_context[1].annotation is Context
            or seems_context[1].default is Context
            or (
                seems_context[1].annotation is seems_context[1].empty
                and seems_context[1].default is seems_context[1].empty
            )
        ):
            self._reaction_context_argument_name = seems_context[0]

        else:
            self._resolve_text_cutter(seems_context)

        for argument in cutters:
            self._resolve_text_cutter(argument)

    def _resolve_text_cutter(
        self, argument: ty.Tuple[str, inspect.Parameter]
    ):
        # def foo(arg: int = vq.Integer()): ...
        # def foo(arg: vq.Integer()): ...
        # def foo(arg: int = vq.Integer): ...
        # def foo(arg: vq.Integer): ...
        name, value = argument
        if value.default != value.empty:
            cutter = value.default
        elif value.annotation != value.empty:
            cutter = value.annotation
        else:
            raise TypeError(
                f"The reaction argument `{name}` "
                f"should have a default value or an "
                f"annotation for specific text cutter, "
                f"nothing is now."
            )

        if inspect.isclass(cutter) and issubclass(cutter, TextCutter):
            real_type = cutter()
        elif isinstance(cutter, TextCutter):
            real_type = cutter
        else:
            raise TypeError(
                f"The reaction argument `{name}` should "
                "be `TextCutter` subclass or "
                f"instance, got `{value}`."
            )

        self._reaction_arguments.append((name, real_type))

    def _build_routing_regex(self):
        self._prefixes_regex = "|".join(self._prefixes)
        self._names_regex = "|".join(self._names)
        if len(self._prefixes) > 1:
            self.prefixes_regex = f"(?:{self._prefixes_regex})"
        if len(self._names) > 1:
            self._names_regex = f"(?:{self._names_regex})"
        self._command_routing_regex = re.compile(
            self._prefixes_regex + self._names_regex,
            flags=self._routing_command_re_flags,
        )