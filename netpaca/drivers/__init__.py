#  Copyright 2020, Jeremy Schulman
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
