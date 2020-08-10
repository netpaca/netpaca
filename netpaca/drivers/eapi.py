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

from asynceapi import Device as DeviceEAPI

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca.drivers import DriverBase, Credential


class Device(DriverBase):
    """
    DriverBase for Arista EOS devices via EAPI.
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
