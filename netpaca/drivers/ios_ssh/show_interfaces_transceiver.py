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
"show interfaces transceiver details"

Example CLI output
------------------
mA: milliamperes, dBm: decibels (milliwatts), NA or N/A: not applicable.
++ : high alarm, +  : high warning, -  : low warning, -- : low alarm.
A2D readouts (if they differ), are reported in parentheses.
The threshold values are calibrated.

                              High Alarm  High Warn  Low Warn   Low Alarm
           Temperature        Threshold   Threshold  Threshold  Threshold
Port       (Celsius)          (Celsius)   (Celsius)  (Celsius)  (Celsius)
---------  -----------------  ----------  ---------  ---------  ---------
Te1/1/1      37.1                   90.0       85.0       -5.0      -10.0
Te1/1/2      37.4                   90.0       85.0       -5.0      -10.0

                              High Alarm  High Warn  Low Warn   Low Alarm
           Voltage            Threshold   Threshold  Threshold  Threshold
Port       (Volts)            (Volts)     (Volts)    (Volts)    (Volts)
---------  -----------------  ----------  ---------  ---------  ---------
Te1/1/1      3.30                   3.63       3.47       3.14       2.97
Te1/1/2      3.30                   3.63       3.47       3.14       2.97

                              High Alarm  High Warn  Low Warn   Low Alarm
           Current            Threshold   Threshold  Threshold  Threshold
Port       (milliamperes)     (mA)        (mA)       (mA)       (mA)
---------  -----------------  ----------  ---------  ---------  ---------
Te1/1/1      12.7                   65.1       61.0        3.0        2.4
Te1/1/2      13.1                   65.1       61.0        3.0        2.4

           Optical            High Alarm  High Warn  Low Warn   Low Alarm
           Transmit Power     Threshold   Threshold  Threshold  Threshold
Port       (dBm)              (dBm)       (dBm)      (dBm)      (dBm)
---------  -----------------  ----------  ---------  ---------  ---------
Te1/1/1      -7.1                    0.0       -3.0       -9.5      -13.0
Te1/1/2      -7.1                    0.0       -3.0       -9.5      -13.0

           Optical            High Alarm  High Warn  Low Warn   Low Alarm
           Receive Power      Threshold   Threshold  Threshold  Threshold
Port       (dBm)              (dBm)       (dBm)      (dBm)      (dBm)
---------  -----------------  ----------  ---------  ---------  ---------
Te1/1/1      -8.6                    0.0       -3.0      -19.0      -23.0
Te1/1/2     -21.8                    0.0       -3.0      -19.0      -23.0


Notes
-----
The CLI output does not appear to "mark" the anomolise as expected; for example
the Rx Power for Te1/1/2 should be marked with a "-" to indicate a warning on
low-threshold.

References
----------
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

# -----------------------------------------------------------------------------
# Externs
# -----------------------------------------------------------------------------

__all__ = ["parse_show_interface_transceiver"]

# -----------------------------------------------------------------------------
#
#                                CODE BEGINS
#
# -----------------------------------------------------------------------------


def parse_show_interface_transceiver(cli_text: str) -> Optional[dict]:
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
    cli_text : str
        The CLI output obtained from the device

    Returns
    -------
    The dictionary of output as described, if the output contains any transceivers.
    None otherwise.
    """

    # make a clean copy of the TTP parser and use the provided cli cli_text.
    try:
        parser = ttp(data=cli_text, template=_TEMPLATE, log_level="none")
        parser.parse()
        res = parser.result()[0][0]
        metrics_ifs = res["metrics"]
    except (IndexError, KeyError):
        return None

    ret_ifs_dom = defaultdict(dict)

    for metric_name, if_data in metrics_ifs.items():
        for if_name, if_metric in if_data.items():
            ret_ifs_dom[if_name].update(
                {
                    metric_name: if_metric["value"],
                    metric_name + "_flag": _threshold_outside(if_metric),
                }
            )

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
<macro>
def first(data):
    names = {
        'temperature': 'temp',
        'transmit': 'txpower',
        'receive': 'rxpower',
        'voltage': 'voltage',
        'current': 'current'
    }
    return names[data.strip().split()[0].lower()]
</macro>
<group
    name="metrics.{{ metric_type }}.{{ if_name }}"
    del="_line_"
    method="table"
>
 {{ metric_type | re(".*Temp.*") | macro("first") }}
 {{ metric_type | re(".*Volt.*") | macro("first") }}
 {{ metric_type | re(".*Transmit.*") | macro("first") }}
 {{ metric_type | re(".*Receive.*") | macro("first")  }}
 {{ metric_type | re(".*Current.*") | macro("first")  }}

------- {{ _start_ }}
{{ if_name }} {{ value|re("FLOAT")|to_float }} {{ flag|re("FLAG") }} {{ hi_a|to_float }} {{ hi_w|to_float }} {{ lo_w|to_float }} {{ lo_a|to_float }}
</group>
"""  # noqa: W605


def _threshold_outside(measurement: dict) -> int:
    """
    This function determines a given metric "status" by comparing the IFdom value against
    the IFdom thresholds; which are obtained from the interface transceiver details.
    The status is encoded as (0=ok, 1=warn, 2=alert)

    Parameters
    ----------
    """
    value = measurement["value"]

    if value <= measurement["lo_a"] or value >= measurement["hi_a"]:
        return 2

    if value <= measurement["lo_w"] or value >= measurement["hi_w"]:
        return 1

    return 0
