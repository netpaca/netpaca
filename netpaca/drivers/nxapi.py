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

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from asyncnxapi import Device as DeviceNXAPI

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca.drivers import DriverBase, Credential


class Device(DriverBase):
    """
    Network Automation Netmon DriverBase for Cisco NXAPI devices.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.nxapi = None

    async def login(self, creds: Optional[Credential] = None) -> bool:
        self.nxapi = DeviceNXAPI(
            host=self.device_host,
            creds=(creds.username, creds.password.get_secret_value()),
        )

        self.log.info(f"{self.name}: Connecting to NX-OS device")

        try:
            res = await self.nxapi.exec(["show hostname"])

        except Exception as exc:
            emsg = f"{self.name} No NXAPI access: {str(exc)}, skipping."
            self.log.error(emsg)
            return False

        self.nxapi.host = res[0].output.findtext("hostname")
        self.creds = creds
        return True
