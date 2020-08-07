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


from typing import Optional

from nwkatk.config_model import Credential
from netpaca import log


class DriverBase(object):
    def __init__(self, name):
        self.name = name
        self.device_host = None
        self.private = None
        self.tags = dict()
        self.creds = None
        self.log = log.get_logger()

    def prepare(self, inventory_rec, config):  # noqa
        self.device_host = inventory_rec.get("ipaddr") or inventory_rec["host"]
        self.private = inventory_rec.copy()
        self.tags = inventory_rec.copy()

    async def login(self, creds: Optional[Credential] = None) -> bool:
        raise NotImplementedError()

    def __str__(self):
        return self.name
