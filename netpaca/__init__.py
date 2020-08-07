#     Copyright 2020, Jeremy Schulman
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

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
