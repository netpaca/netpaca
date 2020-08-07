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

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from itertools import chain
import re

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import httpx
from tenacity import retry, wait_exponential


from nwkatk.config_model import EnvSecretUrl, NoExtraBaseModel

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca import Metric
from netpaca import log
from netpaca.drivers import DriverBase
from netpaca.exporters import ExporterBase

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = []


class InfluxDBConfigModel(NoExtraBaseModel):
    server_url: EnvSecretUrl
    database: str


class InfluxDBExporter(ExporterBase):
    config = InfluxDBConfigModel

    def __init__(self, name):
        super().__init__(name)
        self.server_url = None
        self.post_url = None
        self.httpx = None
        self.log = log.get_logger()

    def prepare(self, config: InfluxDBConfigModel):
        self.server_url = config.server_url.get_secret_value()
        self.post_url = f"{self.server_url}/write?db={config.database}"
        self.httpx = httpx.AsyncClient(verify=False)

    async def export_metrics(self, device: DriverBase, metrics):
        self.log.debug(f"{device.name}: exporting {len(metrics)} metrics to InfluxDB")

        metrics_data = "\n".join(
            _make_influxdb_metric(device_tags=device.tags, metric=metric)
            for metric in metrics
        )

        @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
        async def post_metrics():
            res: httpx.Response = await self.httpx.post(
                self.post_url, data=metrics_data.encode()
            )
            self.log.debug(f"{device.name}: InfluxDB POST status {res.status_code}")
            if not res.is_error:
                return

            if 400 <= res.status_code < 500:
                errmsg = f"{device.name}: InfluxDB bad request, skipping: {res.json()}"
                self.log.error(errmsg)

            if 500 <= res.status_code < 600:
                errmsg = f"{device.name}: InfluxDB unavailable: {res.json()}"
                self.log.error(errmsg)
                raise RuntimeError(errmsg)

        try:
            await post_metrics()

        except Exception as exc:  # noqa
            exc_name = exc.__class__.__name__
            self.log.critical(
                f"{device.name}: Unable to send metrics to InfluxDB: {exc_name}"
            )


_re_escape_chars = re.compile(r"[\s,=]").sub


def _escape_tag_value(value):
    if not value:
        return "''"

    return _re_escape_chars(lambda mo: f"\\{mo.group()}", value)


def _make_influxdb_metric(device_tags, metric: Metric) -> str:
    all_tags = chain(device_tags.items(), metric.tags.items())
    labels = ",".join(f"{tag}={_escape_tag_value(value)}" for tag, value in all_tags)
    return f"{metric.name},{labels} value={metric.value} {metric.ts * 1_000_000}"
