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


import asyncio
import functools

from first import first

from netpaca import timestamp_now
from netpaca import log
from netpaca.exporters import ExporterBase

from netpaca.config_model import ConfigModel
from netpaca.config_model import CollectorModel


class CollectorExecutor(object):
    def __init__(self, config):
        self.config: ConfigModel = config
        exporter_name = first(self.config.defaults.exporters) or first(
            self.config.exporters.keys()
        )
        self.exporter: ExporterBase = self.config.exporters[exporter_name]
        self.log = log.get_logger()

    def start(self, spec: CollectorModel, coro, device, interval=None, **kwargs):
        interval = interval or spec.config.interval
        ic = self.interval_executor(spec, interval)(coro)
        task = ic(device, **kwargs)
        asyncio.create_task(task)

    def interval_executor(self, spec, interval):
        """
        This decorator should be used on all interval based collector coroutines
        so that the coroutine is scheduled on the loop on a interval-periodic
        basis.

        Examples
        --------
        When using this decorator you MUST call it, that is with the parenthesis, as shown:

            @interval_collector()
            async def my_collector(device, interval, **kwargs):
                # does the actual work of the collector

        """

        def decorate(coro):
            @functools.wraps(coro)
            async def wrapped(device, **kwargs):

                # await the original collector coroutine to return the collected
                # metrics.

                # TODO: add profiling around the callector coroutine to measure
                #       the amount of time it takes and log that in DEBUG

                log_ident = f"{device.name}/{spec.collector.name}"
                self.log.debug(f"{log_ident}: Collecting")

                try:
                    ts_start = timestamp_now()
                    metrics = await coro(device=device, timestamp=ts_start, **kwargs)
                    count = len(metrics) if metrics else 0
                    ts_end = timestamp_now()
                    self.log.debug(
                        f"{log_ident}: count={count} time={ts_end-ts_start} ms"
                    )

                except Exception as exc:  # noqa
                    # the collector coroutine causes an exception then log that
                    # information and stop collecting for this device.

                    cls_name = str(exc.__class__)
                    import traceback

                    tb_text = traceback.format_exc()
                    self.log.critical(
                        f"{log_ident}: collector execution failed: {cls_name}:{str(exc)}\n"
                        f"{tb_text}\nRemoving device from collection process"
                    )
                    return

                if metrics:
                    asyncio.create_task(
                        self.exporter.export_metrics(device=device, metrics=metrics)
                    )
                elif hasattr(spec.collector, "metrics"):
                    # if the collector is defined to have metrics (not all do),
                    # but no metrics where produced, log a warning.  This
                    # condition may or may not be an actual issue given that
                    # some collectors might not have anything to emit during
                    # that cycle.
                    self.log.warning(f"{log_ident} 0 metrics")

                # sleep for an interval of time and then create a new task to
                # invoke the wrapped coroutine so that we get the effect of a
                # periodic invocation.

                self.log.debug(
                    f"{log_ident}: Waiting {interval}s before next collection"
                )
                await asyncio.sleep(interval)
                asyncio.create_task(wrapped(device=device, **kwargs))

            return wrapped

        return decorate
