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

from itertools import chain

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import httpx
from tenacity import retry, wait_exponential
from pydantic import BaseModel

from netpaca.core.config_model import EnvSecretUrl

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca import Metric
from netpaca import log
from netpaca.drivers import DriverBase
from netpaca.exporters import ExporterBase


class CirconusConfigModel(BaseModel):
    circonus_datasubmission_url: EnvSecretUrl


class CirconusExporter(ExporterBase):
    config = CirconusConfigModel

    def __init__(self, name):
        super().__init__(name)
        self.post_url = None
        self.httpx = None
        self.log = log.get_logger()

    def prepare(self, config: CirconusConfigModel):
        self.post_url = config.circonus_datasubmission_url.get_secret_value()
        self.httpx = httpx.AsyncClient(
            verify=False, headers={"content-type": "application/json"},
        )

    async def export_metrics(self, device: DriverBase, metrics):
        self.log.debug(f"{device.name}: Exporting {len(metrics)} metrics")

        post_data = dict(
            make_circonus_metric(device_tags=device.tags, metric=metric,)
            for metric in metrics
        )

        @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
        async def to_circonus():
            res = await self.httpx.put(self.post_url, json=post_data)
            self.log.debug(f"{device.name}: Circonus PUT status {res.status_code}")

        try:
            await to_circonus()

        except Exception as exc:  # noqa
            exc_name = exc.__class__.__name__
            self.log.error(
                f"{device.name}: Unable to send metrics to Circonus: {exc_name}"
            )


def make_circonus_metric(device_tags, metric: Metric):
    all_tags = chain(device_tags.items(), metric.tags.items())

    def to_str(value):
        if isinstance(value, bytes):
            return 'b"%s"' % value.decode("utf-8")
        else:
            return value

    stream_tags = ",".join(f"{key}:{to_str(value)}" for key, value in all_tags)

    name = f"{metric.name}|ST[{stream_tags}]"
    value = metric.value
    return name, value
