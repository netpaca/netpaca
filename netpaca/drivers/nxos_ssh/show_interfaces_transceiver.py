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
This file uses TTP to parse the output of the Cisco NX-OS command:
"show interface transceiver details"

Examples CLI output
-------------------
Ethernet1/13
    transceiver is present
    type is 10Gbase-SR
    name is CISCO-OPLINK
    part number is TPP4XGDS0CCISE2G
    revision is 01
    serial number is OHMYREDACTED
    nominal bitrate is 10300 MBit/sec
    Link length supported for 50/125um OM2 fiber is 82 m
    Link length supported for 62.5/125um fiber is 26 m
    Link length supported for copper is 40 m
    Link length supported for 50/125um OM3 fiber is 300 m
    cisco id is --
    cisco extended id number is 4

           SFP Detail Diagnostics Information (internal calibration)
  ----------------------------------------------------------------------------
                Current              Alarms                  Warnings
                Measurement     High        Low         High          Low
  ----------------------------------------------------------------------------
  Temperature   33.30 C        75.00 C     -5.00 C     70.00 C        0.00 C
  Voltage        3.27 V         3.63 V      2.97 V      3.46 V        3.13 V
  Current        6.34 mA       12.00 mA     0.50 mA    11.50 mA       1.00 mA
  Tx Power      -2.26 dBm       1.99 dBm  -11.30 dBm   -1.00 dBm     -7.30 dBm
  Rx Power        N/A     --    1.99 dBm  -13.97 dBm   -1.00 dBm     -9.91 dBm
  ----------------------------------------------------------------------------
  Note: ++  high-alarm; +  high-warning; --  low-alarm; -  low-warning


Text parsing done with ttp:
https://ttp.readthedocs.io
"""

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional
from collections import defaultdict

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from ttp import ttp
from first import first

# -----------------------------------------------------------------------------
# Externs
# -----------------------------------------------------------------------------

__all__ = ["parse_show_interface_transceiver"]

# -----------------------------------------------------------------------------
#
#                                CODE BEGINS
#
# -----------------------------------------------------------------------------


def parse_show_interface_transceiver(parse_text: str) -> Optional[dict]:
    """
    This function is used to parse the IOS CLI text from the command
    "show interfaces transceiver" into a dictionary whose
        key=<if_name>
        value=<dict>:
            <tag>: <value>
            <tag>_flag: <flag_value>

    Where <tag> is the name of the DOM item such as "rxpower" and the <tag>_flag
    is the Cisco marker (++,--,+,-) that indicates the DOM item exceeds a
    threshold value.

    Parameters
    ----------
    parse_text : str
        The CLI output obtained from the device

    Returns
    -------
    The dictionary of output as described, if the output contains any transceivers.
    None otherwise.
    """

    # make a clean copy of the TTP parser and use the provided cli cli_text.
    try:
        parser = ttp(data=parse_text, template=_TEMPLATE)
        parser.parse()
        res = parser.result()
        ifdom_data = res[0][0]["interfaces"]

    except (IndexError, KeyError):
        return None

    ret_ifs_dom = defaultdict(dict)

    for if_name, if_dom_data in ifdom_data.items():
        try:
            for item in ("temp", "voltage", "txpower", "rxpower"):
                tag, *flag = item.split()
                ret_ifs_dom[if_name].update(
                    {tag: if_dom_data[tag], tag + "_flag": first(flag) or ""}
                )

        except KeyError:
            from netpaca.log import get_logger

            emsg = (
                f"NXOS-SSH interface-transceiver parser failed on interface: {if_name}"
            )
            get_logger().critical(emsg)
            raise RuntimeError(emsg)

    return ret_ifs_dom


# -----------------------------------------------------------------------------
#
#                                PRIVATE CODE BEGINS
#
# -----------------------------------------------------------------------------

_TEMPLATE = """
<vars>
FLOAT = "[-+]?[0-9]+\.[0-9]+"
FLAG = "(--|\+\+|-|\+)?"
</vars>
<group
    name="interfaces.{{ if_name }}"
    equal="present, present"
    containsall="temp"
>
{{ if_name }}
    transceiver is {{ present | ORPHRASE }}
    type is {{ media | ORPHRASE | upper | default(None) }}
    serial number is {{ serial_number }}
  Temperature {{ temp }} C {{ _line_ }}
  Voltage {{ voltage  | re("FLOAT") }} V {{ voltage_flag | re("FLAG") }} {{ _line_ }}
  Tx Power {{ txpower | re("FLOAT") }} dBm {{ txpower_flag | re("FLAG") }} {{ _line_ }}
  Tx Power {{ txpower | re("N/A") | default(0) }} {{ txpower_flag | re("FLAG") }} {{ _line_ }}
  Rx Power {{ rxpower | re("FLOAT") }} dBm {{ rxpower_flag | re("FLAG") }} {{ _line_ }}
  Rx Power {{ rxpower | re("N/A") | default("0") }} {{ rxpower_flag | re("FLAG") }} {{ _line_ }}
  Note: {{ _line_ }} {{ _end_ }}
</group>
"""  # noqa: W605
