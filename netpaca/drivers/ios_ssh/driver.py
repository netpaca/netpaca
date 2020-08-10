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
    DriverBase for Cisco IOS devices via SSH.
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
