#     Copyright 2020, Jeremy Schulman
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

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

from nwkatk.config_model import EnvSecretUrl

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
