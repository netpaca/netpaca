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

from asynceapi import Device as DeviceEAPI

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca.drivers import DriverBase, Credential


class Device(DriverBase):
    """
    Network Automation Netmon DriverBase for Arista EOS devices.
    """

    def __init__(self, *vargs, **kwargs):
        super().__init__(*vargs, **kwargs)
        self.eapi = None

    async def login(self, creds: Optional[Credential] = None) -> bool:
        self.eapi = DeviceEAPI(
            host=self.device_host,
            creds=(creds.username, creds.password.get_secret_value()),
            private=self.private,
        )

        self.log.info(f"{self.name}: Connecting to Arista EOS device")

        try:
            res = await self.eapi.exec(["show hostname"])

        except Exception as exc:
            self.log.error(f"{self.name} No NXAPI access: {str(exc)}, skipping.")
            return False

        self.eapi.host = res[0].output["hostname"]
        self.creds = creds
        return True
