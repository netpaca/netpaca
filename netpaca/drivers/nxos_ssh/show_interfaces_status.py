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

"""
Text parsing done with ttp:
https://ttp.readthedocs.io
"""

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from ttp import ttp

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["parse_show_interfaces_status"]


# -----------------------------------------------------------------------------
#
#                                CODE BEGINS
#
# -----------------------------------------------------------------------------


def parse_show_interfaces_status(parse_text: str) -> Optional[dict]:
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
        parser = ttp(
            data=parse_text[_skip_header], template=_TEMPLATE, log_level="none"
        )
        parser.parse()
        res = parser.result()[0][0]
        return res["interfaces"]

    except (IndexError, KeyError):
        return None


# -----------------------------------------------------------------------------
#
#                                PRIVATE CODE BEGINS
#
# -----------------------------------------------------------------------------

_skip_header = slice(
    len(
        """\
Port      Name               Status       Vlan       Duplex  Speed Type
"""
    ),
    -1,
)

_TEMPLATE = """
<group name="interfaces.{{ if_name }}" method="table">
{{ if_name }} {{ if_desc | ORPHRASE }} {{ if_status }} {{ if_vlan }} {{ duplex }} {{ speed }} {{ if_type }}
</group>
"""
