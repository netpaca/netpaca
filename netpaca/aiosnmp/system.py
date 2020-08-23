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
# Public Imports
# -----------------------------------------------------------------------------

from netpaca.drivers import DriverBase


# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .walk import walk_table

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["get_sys_uptime", "get_snmpengine_uptime"]

# -----------------------------------------------------------------------------
#
#                                   CODE BEGINS
#
# -----------------------------------------------------------------------------


OID_SYS_UPTIME = "1.3.6.1.2.1.1.3"
OID_SNMP_ENGINE_UPTIME = "1.3.6.1.6.3.10.2.1.3"  # not always avaialble


async def get_sys_uptime(device: DriverBase, community: str) -> int:
    """
    Returns the device SNMP sysUpTime value as an integer (TimeTicks).

    Parameters
    ----------
    device: DriverBase
        The device instance

    community: str
        The SNMPv2 community string

    Returns
    -------
    The sysUptime (TimeTicks) as an integer.

    Raises
    ------
    RuntimeError
        If unable to obain the value since all devices should provide it.

    References
    ----------
    SNMP sysUpTime OID:
        http://oid-info.com/get/1.3.6.1.2.1.1.3
    """
    res = await walk_table(device, oid=OID_SYS_UPTIME, community=community)
    return int(res[0])


async def get_snmpengine_uptime(device, community):
    """
    Returns the SNMP engine uptime value in seconds as int.  See References.
    If the device does not support this OID, then None is returned.

    Parameters
    ----------
    device: DriverBase
        The instance of the dveice

    community: str
        The SNMPv2 community string

    Returns
    -------
    uptime as int if OID is available on device
    None otherwise

    References
    ----------
    http://oid-info.com/get/1.3.6.1.6.3.10.2.1.3
    """
    try:
        res = await walk_table(device, oid=OID_SNMP_ENGINE_UPTIME, community=community)
        return int(res[0])

    except RuntimeError:
        return None
