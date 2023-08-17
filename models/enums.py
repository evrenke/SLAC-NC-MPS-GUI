from enum import Enum
from qtpy.QtGui import (QBrush, QColor)


class Statuses(Enum):
    """
    author: Zach Domke, Evren Keskin
    Statuses for the data values of given UI tables, used for sorting in some cases
    Copied over from sc_mps_gui
    """
    RED = (3, (255, 0, 0))          # Red:          Major Alarm
    YEL = (2, (235, 235, 0))        # Yellow:       Minor Alarm
    MAG = (1, (235, 0, 235))        # Magenta:      Error
    GRN = (0, (0, 235, 0))          # Green:        No Alarm
    WHT = (-1, (255, 255, 255))     # White:        Disconnected
    BGD = (-2, (0, 0, 0, 165))      # Background:   Table Background
    CYN = (-3, (0, 255, 255))       # Cyan:         Color to Never Use
    BLU = (-4, (20, 80, 180))       # Blue:         Used to highlight important messages

    def num(self) -> int:
        return self.value[0]

    def rgb(self) -> tuple:
        return self.value[1]

    def brush(self) -> QBrush:
        return QBrush(QColor(*self.rgb()))

    def faulted(self) -> bool:
        return self.num() > 0

    def error(self) -> bool:
        return abs(self.num()) == 1

    @classmethod
    def max(cls) -> int:
        return cls.RED.num()
