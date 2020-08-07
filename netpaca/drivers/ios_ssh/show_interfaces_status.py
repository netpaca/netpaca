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
import re
from typing import Optional

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

# from ttp import ttp

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["parse_show_interfaces_status"]


# -----------------------------------------------------------------------------
#
#                                CODE BEGINS
#
# -----------------------------------------------------------------------------


def parse_show_interfaces_status(cli_text: str) -> Optional[dict]:
    """
    This function is used to parse the IOS CLI text from the command
    "show interfaces status" into a dictionary whose
        key=<if_name>
        value=<dict>:
            <if_desc>: str
                The interface description value
            <if_status>: str
                The interface status value, "connected" for exxample
            <if_vlan>:
                The VLAN information; usually the access VLAN or the word "trunk"
            <if_duplex>:
                The interface duplex value, such as "auto" or "a-full"
            <if_speed>:
                The interface speed value such as "auto" or "a-1000"

            <if_type>:
                The interface media type (if present) converted to
                uppercase.  For example the original value "1000BaseLX SFP"
                is returned as "1000BASELX SFP"

    Parameters
    ----------
    cli_text : str
        The CLI output obtained from the device

    Returns
    -------
    The dictionary of output as described, if the output contains any transceivers.
    None otherwise.
    """

    return {row["if_name"]: row for row in parse_table(cli_text)}

    # make a clean copy of the TTP parser and use the provided cli cli_text.
    # try:
    #     parser = ttp(data=cli_text[_skip_header], template=_TEMPLATE, log_level="none")
    #     parser.parse()
    #     res = parser.result()[0][0]
    #     return res["interfaces"]
    #
    # except (IndexError, KeyError):
    #     return None


# -----------------------------------------------------------------------------
#
#                                PRIVATE CODE BEGINS
#
# -----------------------------------------------------------------------------

_header = "Port      Name               Status       Vlan       Duplex  Speed Type"
_vars = [
    "if_name",
    "if_desc",
    "if_status",
    "if_vlan",
    "if_duplex",
    "if_speed",
    "if_type",
]

_col_values = _header.split()
_col_spaces = [len(spcs) for spcs in re.findall(r"\s+", _header)]
_col_width = [len(col) + _col_spaces[i] for i, col in enumerate(_col_values[:-1])]
_re_expr = "".join(
    ["(?P<%s>.{%s})" % (_vars[i], len) for i, len in enumerate(_col_width)]
    + ["(?P<if_type>.*)"]
)
_skip_header = slice(len(_header) + 1, -1)
_match = re.compile(_re_expr).match


def parse_table(content) -> dict:
    for row in content[_skip_header].splitlines():
        mo = _match(row)
        if not mo:
            continue
        yield dict((key, value.strip()) for key, value in mo.groupdict().items())


_TEMPLATE = """
<vars>
OPT_IF_DESC = '(\S+)?'
</vars>

<group name="interfaces.{{ if_name }}"
    method="table"
    default=""
>
{{ if_name }} {{ if_desc }} {{ if_status }} {{ if_vlan }} {{ if_duplex }} {{ if_speed }} {{ if_type }} {{ if_type2 }}
{{ if_name }} {{ if_status }} {{ if_vlan }} {{ if_duplex }} {{ if_speed }} {{ if_type | ORPHRASE }}
</group>
"""  # noqa

# {{ if_name }} {{ if_desc | ORPHRASE }} {{ if_status }} {{ if_vlan }} {{ if_duplex }} {{ if_speed }} {{ if_type | ORPHRASE | upper }}
# {{ if_name }} {{ if_status }} {{ if_vlan }} {{ if_duplex }} {{ if_speed }} {{ if_type | ORPHRASE | upper }}


_TEMPLATE = """
<group>
Port      Name               Status       Vlan       Duplex  Speed Type   {{ _headers_ }}
</group>   
"""