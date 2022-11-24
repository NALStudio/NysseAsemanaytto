from abc import abstractmethod
from datetime import datetime
from core import elements, logging
import digitransit.routing

class StoptimeBaseRenderer(elements.ElementRenderer):
    def __init__(self, stoptime_index: int) -> None:
        self.stoptime_index: int = stoptime_index
        self.value: str = "<error>"

    def get_font_height(self, full_height: int) -> int:
        return round((2 / 3) * full_height)

    def _get_stoptime(self, context: elements.UpdateContext) -> digitransit.routing.Stoptime:
        assert context.stopinfo.stoptimes is not None
        return context.stopinfo.stoptimes[self.stoptime_index]

    @abstractmethod
    def get_value(self, stoptime: digitransit.routing.Stoptime, current_time: datetime) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_error_value(self) -> str:
        raise NotImplementedError()

    def update(self, context: elements.UpdateContext) -> bool:
        changes: bool = False

        new_value: str
        try:
            new_value = self.get_value(self._get_stoptime(context), context.time)
        except Exception as e:
            logging.error(e)
            new_value = self.get_error_value()

        if self.value != new_value:
            self.value = new_value
            changes = True

        return changes
