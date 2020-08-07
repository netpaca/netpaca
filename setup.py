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

from setuptools import setup, find_packages
from itertools import chain

package_name = "netpaca"
package_version = open("VERSION").read().strip()


def requirements(filename="requirements.txt"):
    return open(filename.strip()).readlines()


with open("README.md", "r") as fh:
    long_description = fh.read()

# -----------------------------------------------------------------------------
#
#                           Extras Requirements
#
# -----------------------------------------------------------------------------

# builtin extras to support Cisco NX-API and Arista EOS device driver.

extras_require = {
    "nxapi": requirements("requirements-drivers-nxapi.txt"),
    "eapi": requirements("requirements-drivers-eapi.txt"),
    "ios": requirements("requirements-drivers-ssh.txt"),
}

# add the option for all optional extras
extras_require["all"] = list(chain.from_iterable(extras_require.values()))


# -----------------------------------------------------------------------------
#
#                                 Main Setup
#
# -----------------------------------------------------------------------------

setup(
    name=package_name,
    version=package_version,
    description="Netpaca Core Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jeremy Schulman",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements(),
    extras_require=extras_require,
    entry_points={
        "console_scripts": ["netpaca = netpaca.script:main"],
        "netpaca.device_drivers": [
            "arista.eos = netpaca.drivers.eapi:Device",
            "cisco.nxapi = netpaca.drivers.nxapi:Device",
            "cisco.ios_ssh = netpaca.drivers.ios_ssh:Device",
            "cisco.nxos_ssh = netpaca.drivers.nxos_ssh:Device",
        ],
        "netpaca.exporters": [
            "circonus = netpaca.exporters.circonus:CirconusExporter",
            "influxdb = netpaca.exporters.influxdb:InfluxDBExporter",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
    ],
)
