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
"""
This module contains functions to get device SNMPv2 interface related tables.
"""

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

__all__ = [
    "get_if_name_table",
    "get_if_alias_table",
    "get_if_lastchange_table",
    "get_if_operstatus_table",
]
# -----------------------------------------------------------------------------
#
#                                   CODE BEGINS
#
# -----------------------------------------------------------------------------

ODI_IF_NAME = "1.3.6.1.2.1.2.2.1.2"  # ifDesc table provide interface name
OID_IF_DESC = "1.3.6.1.2.1.31.1.1.1.18"  # ifAlias table provide interface description
OID_IF_OPSTATUS = "1.3.6.1.2.1.2.2.1.8"  # provides interface up/down status
OID_IF_LASTUPDATE = "1.3.6.1.2.1.2.2.1.9"  # provides last update time value


async def get_if_name_table(device: DriverBase) -> dict:
    """
    Fetches the ifName table and returns dictionary:
        key: int
            ifIndex
        value: str
            interface name, for example "GigabitEthernet0/1"

    Parameters
    ----------
    device: DriverBase
        The device instance
    """
    recs = await walk_table(device, oid=ODI_IF_NAME, factory=factory_ifindex_value)
    return dict(recs)


async def get_if_alias_table(device: DriverBase) -> dict:
    """
    Fetches the ifAlias table and returns dictionary:
        key: int
            ifIndex
        value: str
            interface description string, "" if not cnfigured on device

    Parameters
    ----------
    device: DriverBase
        The device instance
    """
    recs = await walk_table(device, oid=OID_IF_DESC, factory=factory_ifindex_value)
    return dict(recs)


async def get_if_operstatus_table(device: DriverBase) -> dict:
    """
    Fetches the ifOpStatus table and returns dictionary:
        key: int
            ifIndex
        value: bool
            True if link-up
            False if link-down

    Parameters
    ----------
    device: DriverBase
        The device instance
    """

    def factory(var_bind):
        """ oid values: up(1), down(2) -> True, False """
        var_name, var_value = var_bind
        oid = var_name.getOid()
        if_index = oid.asTuple()[-1]
        link_up = "1" == var_value.prettyPrint()
        return if_index, link_up

    recs = await walk_table(device, oid=OID_IF_OPSTATUS, factory=factory)
    return dict(recs)


async def get_if_lastchange_table(device):
    """
    Fetches the ifName table and returns dictionary:
        key: int
            ifIndex
        value: int
            last changed time as SNMP TimeTicks

    Parameters
    ----------
    device: DriverBase
        The device instance
    """

    def factory(var_bind):
        """ oid values as TimeTicks int """
        var_name, var_value = var_bind
        oid = var_name.getOid()
        if_index = oid.asTuple()[-1]
        return if_index, int(var_value.prettyPrint())

    recs = await walk_table(device, oid=OID_IF_LASTUPDATE, factory=factory)
    return dict(recs)


def factory_ifindex_value(var_bind):
    """ factory for converting a var_bind to (ifIndex, value) """
    var_name, var_value = var_bind
    oid = var_name.getOid()
    if_index = oid.asTuple()[-1]
    return if_index, var_value.prettyPrint()
