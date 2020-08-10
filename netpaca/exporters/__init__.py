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
#

from typing import Optional, List
from netpaca.core.config_model import BaseModel

from netpaca.drivers import DriverBase
from netpaca import Metric


class ExporterBase(object):
    config: Optional[BaseModel] = None

    def __init__(self, name):
        self.name = name
        self.private = None
        self.tags = dict()
        self.creds = None

    def prepare(self, config):
        raise NotImplementedError()

    async def export_metrics(self, device: DriverBase, metrics: List[Metric]):
        pass

    def __str__(self):
        return self.name
