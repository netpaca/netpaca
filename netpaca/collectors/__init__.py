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


from typing import Optional, List, Type
import functools


from pydantic import PositiveInt

from nwkatk.config_model import NoExtraBaseModel
from netpaca import Metric


__all__ = ["CollectorType", "CollectorConfigModel"]


class CollectorConfigModel(NoExtraBaseModel):
    """
    The CollectorConfigModel defines the configuraiton options that the
    collector implements.  By default they must all provide the interval option.
    Each CollectorType can subclass the CollectorConfigModel to add additional
    options.
    """

    interval: Optional[PositiveInt]


@functools.singledispatch
async def collector_start(device, executor, **kwargs):  # noqa

    cls_name = device.__class__.__name__
    raise RuntimeError(f"IFdom: No entry-point registered for device type: {cls_name}")


class CollectorTypeMeta(type):
    def __new__(mcs, name, bases, dct):
        if "start" not in dct:

            @functools.singledispatch
            async def collector_start(device, executor, **kwargs):  # noqa
                mod_name = device.__module__
                cls_name = device.__class__.__name__
                raise RuntimeError(
                    f"Collector {name}: "
                    f"No entry-point registered for device type: {mod_name}.{cls_name}"
                )

            dct["start"] = collector_start

        dct.setdefault("config", CollectorConfigModel)
        return super().__new__(mcs, name, bases, dct)


class CollectorType(metaclass=CollectorTypeMeta):
    """
    The CollectorType is the base type for defining a specific collector
    definition.

    Attributes
    ----------
    name: str
        The name of the collector, use for debug logging

    description: str
        A humanized description of the collector purpose

    start : functools.singledispatch, optional
        Using a "singledispatch" method for driver-specific registration
        purposes. A specific device driver collector package will use this
        function as a decorator to register their specific Driver class. See the
        eapi.py and nxapi.py files to see how this is used.

        If not provided, a default will be created.  If the system attempts to
        execute the start function on an unregistered Device Driver class, then
        this default function will raise a RuntimeError with a helpful message.

    config : CollectorConfigModel, optional
        Used to define the available collector configuration options, using the
        CollectorConfigModel as a base class; which defines the `interval`
        option for collection.  The collector specific options are *in addition
        to* the interval option.

        If not provided, then CollectorConfigModel is used.

    metrics: list of Metric types
        Defines the list of Metric types that this collector type supports.
    """

    name: str
    description: Optional[str]
    start: Type[functools.singledispatch]
    config: Optional[CollectorConfigModel]
    metrics: List[Type[Metric]]
