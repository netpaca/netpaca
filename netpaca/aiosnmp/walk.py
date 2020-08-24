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
This file contains asyncio SNMPv2 functions that can be used by DeviceBase
instance.
"""
# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional, Callable, List, Any

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from netpaca.drivers import DriverBase

from pysnmp.hlapi.asyncio import (
    ObjectType,
    ObjectIdentity,
    nextCmd,
    UdpTransportTarget,
    ContextData,
)

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["walk_table"]

# -----------------------------------------------------------------------------
#
#                                   CODE BEGINS
#
# -----------------------------------------------------------------------------


SNMP_V2_PORT = 161


async def walk_table(
    device: DriverBase, oid, factory: Optional[Callable] = None
) -> List[Any]:
    """
    This coroutine implements an SNMP "walk" of a given table starting
    at `oid`.

    Parameters
    ----------
    device: DriverBase
        The device instance

    oid: str
        The SNMP table OID string value, for example "1.3.6.1.2.1.1.3"

    factory: Callable
        If provided by Caller this function is called for reach var_bind ('row
        data') in the table so that this factory function can extract what is
        desired for builting up the resulting list of records.  If this function
        is not provided, then the default factory behavior is to extract the
        var_bind data only (via the .prettyPrint method).
    """
    target = device.device_host

    # obtain the pySnmp required objects from the device private dictionary.

    dev_pysnmp = device.private["pysnmp"]
    snmp_engine = dev_pysnmp["engine"]
    snmp_community = dev_pysnmp["community"]

    initial_var_binds = var_binds = [ObjectType(ObjectIdentity(oid))]
    collected = list()

    # if a factory function is not provided, then return the oid value

    if not factory:

        def factory(_vb):
            """ default row factory to return value only """
            return _vb[1].prettyPrint()

    while True:

        (err_indications, err_st, err_idx, var_bind_table) = await nextCmd(
            snmp_engine,
            snmp_community,
            UdpTransportTarget((target, SNMP_V2_PORT)),
            ContextData(),
            *var_binds,
        )

        if err_indications:
            # an error indication is reason to raise an exception and stop
            # processing the walk
            emsg = f"{device.name}: SNMP failed on OID: {oid}"
            device.log.error(emsg)
            raise RuntimeError(emsg, err_indications)

        elif err_st:
            # an error status is reason to log the error, but continue walking
            # the MIB table.
            emsg = "%s at %s" % (
                err_st.prettyPrint(),
                err_idx and var_binds[int(err_idx) - 1][0] or "?",
            )
            device.log.error(emsg)

        for var_bind_row in var_bind_table:
            for idx, var_bind in enumerate(var_bind_row):
                if not initial_var_binds[0][idx].isPrefixOf(var_bind[0]):
                    return collected

                collected.append(factory(var_bind))

        # setup to fetch the next item in table
        var_binds = var_bind_table[-1]
