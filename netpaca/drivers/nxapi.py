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
    DriverBase for Cisco NX-OS devices via NXAPI.
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
