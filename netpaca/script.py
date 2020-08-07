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

import sys
import asyncio
from importlib import metadata
from functools import update_wrapper

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import click
from nwkatk.cli.inventory import opts_inventory, pass_inventory_records

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca.config import load_config_file
from netpaca.config_model import ConfigModel
from netpaca import log

from netpaca.collectors.executor import CollectorExecutor

VERSION = metadata.version(__package__)


async def async_main_device(executor, inventory_rec, config: ConfigModel):
    lgr = log.get_logger()
    interval = config.defaults.interval

    device_name = inventory_rec["host"]

    if not (os_name := inventory_rec["os_name"]) in config.device_drivers:
        lgr.error(
            f"{device_name} uses os_name {os_name} not found in config, skipping."
        )
        return

    device = config.device_drivers[os_name].driver(name=device_name)
    creds = config.defaults.credentials

    try:
        device.prepare(inventory_rec=inventory_rec, config=config)
        ok = await device.login(creds=creds)
        assert ok
    except (RuntimeError, AssertionError):
        lgr.error(f"{device_name}: failed to connect to device, skipping.")
        return

    # TODO: filter options to not copy all tag values
    #       ....

    for c_name, c_spec in config.collectors.items():

        # c_start will be the functools singledispatch function bound to the
        # collector type.  The first param, Device, is used by singledispatch
        # call the Device class specific start coroutine registered.

        c_start = c_spec.collector.start

        c_config = c_spec.config
        c_config.interval = c_config.interval or interval
        await c_start(device, executor=executor, spec=c_spec)


# -----------------------------------------------------------------------------


def set_log_level(ctx, param, value):  # noqa
    lgr = log.setup_logging()
    lgr.setLevel(value.upper())


def map_config_inventory(f):
    """
    This decorator is used to map the netmon config model inventory value
    into the kwargs['inventory'] so that the standard nwkatk inventory
    loader will work as expected ;-)
    """

    @click.pass_context
    def mapper(ctx, *args, **kwargs):
        kwargs["inventory"] = str(kwargs["config"].defaults.inventory)
        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(mapper, f)


@click.command()
@click.version_option(version=VERSION)
@click.option(
    "--config",
    "-C",
    type=click.File(),
    is_eager=True,
    default="netmon.toml",
    callback=load_config_file,
)
@opts_inventory
@click.option(
    "--interval", type=click.IntRange(min=30), help="collection interval (seconds)",
)
@click.option(
    "--log-level",
    help="log level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    callback=set_log_level,
)
@map_config_inventory
@pass_inventory_records
def cli_netifdom(inventory_records, config, **kwargs):

    if interval := kwargs["interval"]:
        config.defaults.interval = interval

    # Start each collector on the device
    executor = CollectorExecutor(config=config)

    loop = asyncio.get_event_loop()
    # loop.run_until_complete(async_main_exporters(config=config))

    for rec in inventory_records:
        loop.create_task(async_main_device(executor, rec, config=config))

    loop.run_forever()


def main():
    try:
        cli_netifdom()

    except Exception:  # noqa
        import traceback

        content = traceback.format_exc(limit=-1)
        sys.exit(content)


if __name__ == "__main__":
    main()
