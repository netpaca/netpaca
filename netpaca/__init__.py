#  Copyright (C) 2020  Jeremy Schulman
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Any, Mapping
import time
from base64 import encodebytes


from pydantic import dataclasses, PositiveInt, Field, fields

__all__ = ["Metric", "MetricTimestamp", "timestamp_now", "b64encodestr"]


def timestamp_now():
    """ returns the current time since epoch in milli-seconds """
    return int(time.time() * 1000)


def b64encodestr(str_value):
    return encodebytes(bytes(str_value, encoding="utf-8")).replace(b"\n", b"")


MetricTimestamp = PositiveInt


@dataclasses.dataclass
class Metric:
    """
    This base dataclass represents an individual metric that will be consumed by an Exporter.
    A package should subclass Metric for specific collector metrics and in doing so should
    override the `value` field type annotation and default assign the `name`.

    Examples
    --------
    class IFdomRxPowerMetric(Metric):
        name: str = 'ifdom_rxpower'
        value: float = Field(..., description='optic receive power as dBm')
    """

    ts: MetricTimestamp = Field(
        default_factory=timestamp_now,
        description="metric timestamp in milliseconds since epoch",
    )
    tags: Mapping = Field(
        default_factory=lambda: {}, description="tags as key-value mapping"
    )
    value: Any = Field(description="metric value, should be typed by subclass")
    name: str = Field(description="metric name")

    def __post_init__(self):
        # TODO: I cannot determine how to use Field so that the default factory is called
        #       on a subclassed Metric.  The approach below seems to overcome this obstacle.
        if isinstance(self.ts, fields.FieldInfo):
            self.ts = self.ts.default_factory()

        if isinstance(self.tags, fields.FieldInfo):
            self.tags = self.tags.default_factory()
