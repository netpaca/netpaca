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

from scrapli.driver.core import AsyncIOSXEDriver

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
        self.driver: AsyncIOSXEDriver = Optional[None]

    async def login(self, creds: Optional[Credential] = None) -> bool:
        conn_args = dict(
            auth_username=creds.username,
            auth_password=creds.password.get_secret_value(),
            auth_strict_key=False,
            timeout_socket=60,  # connect timeout
            transport="asyncssh",
        )

        self.log.info(f"{self.name}: Connecting to Cisco SSH device")
        self.driver = AsyncIOSXEDriver(host=self.device_host, **conn_args)

        try:
            await self.driver.open()
            await self.driver.send_command("show users")

        except Exception as exc:
            emsg = f"{self.name} No Cisco SSH access: {str(exc)}, skipping."
            self.log.error(emsg)
            return False

        self.creds = creds
        return True
