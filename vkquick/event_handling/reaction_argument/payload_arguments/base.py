import abc
import typing as ty

import vkquick.event_handling.reaction_argument.base


class PayloadArgument(
    vkquick.event_handling.reaction_argument.base.ReactionArgument, abc.ABC
):
    """
    Тайпинг к аргументу для реакции у `EventHandler`
    """

    @abc.abstractmethod
    def init_value(
        self, event: "vkquick.events_generators.event.Event"  # noqa
    ) -> ty.Any:
        """
        Возвращает значение аргумента для рекакции. Принимает объект события
        """