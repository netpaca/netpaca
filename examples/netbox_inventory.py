#!/usr/bin/env python3.8
# -----------------------------------------------------------------------------
# Netbox inventory -> CSV generator
# Version: 0.2.0, 2020-jul-17
# -----------------------------------------------------------------------------
#
# This script is used to retrieve the device inventory from a Netbox system and
# emil the CSV file to either stdout (default) or a filename provided
#
# The following Environment variables are REQUIRED:
#
#   NETBOX_ADDR: the URL to the NetBox server
#       "https://my-netbox-server"
#
#   NETBOX_TOKEN: the NetBox login token
#       "e0759aa0d6b4146-from-netbox-f744c4489adfec48f"
#
# The following Environment variables are OPTIONAL:
#
#   NETBOX_INVENTORY_OPTIONS
#       Same as the options provided by "--help"
#
# The output of this script is a CSV file that contains the fields listed in the
# CSV_FIELD_NAMES variable below.
#
# Special Note: The `os_name` value will be the platform value assigned to the
#               device.  If you also tag a device with "platform_flavor=<value>"
#               then the flavor value will be appened to the platform.  For
#               exmaple, if you have a device with platform assigned as "nxos"
#               and tagged with "platform_flavor=ssh", then the `os_name` value
#               in the CSV file will be "nxos_ssh".
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import sys
import argparse
import os
import csv
from functools import lru_cache
from itertools import chain
from urllib3 import disable_warnings  # noqa

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import requests  # noqa


CSV_FIELD_NAMES = ["host", "ipaddr", "os_name", "role", "site", "region"]


# -----------------------------------------------------------------------------
#
#                             CODE BEGINS
#
# -----------------------------------------------------------------------------


def rec_to_csv(rec):
    """
    This generatpr accepts a Netbox API device record and yeilds a list of
    values in the order defined in the CSV_FIELD_NAMES variable above. If for
    any reason the record cannot be used, for example it does not have a
    platform assigned or it is missing a primary IP address then this generator
    will not yield a list back; thus filtering out "bad" records.

    Parameters
    ----------
    rec: dict

    Yields
    -------
    list as described
    """
    # skip any device that does not have a platform value assigned.
    if not (platform := rec["platform"]):
        return

    # if the primary IP address is not assigned, then skip this record.

    try:
        ipaddr = rec["primary_ip"]["address"].split("/")[0]
    except (KeyError, TypeError):
        return

    hostname = rec["name"]
    os_name = platform["slug"]

    # if there is a platform "flavor" tag, then append the os_name value.

    if platform_flavor := next(
        (
            tag.partition("=")[-1]
            for tag in rec["tags"]
            if tag.startswith("platform_flavor")
        ),
        None,
    ):
        os_name += f"_{platform_flavor}"

    role = rec["device_role"]["slug"]
    site = rec["site"]["slug"]
    region = get_site(site)["region"]["slug"]

    yield [hostname, ipaddr, os_name, role, site, region]


def cli():
    """ Create CLI option parser, parse User inputs and return results """
    options_parser = argparse.ArgumentParser()
    options_parser.add_argument("--site", action="store", help="limit devices to site")
    options_parser.add_argument(
        "--region", action="store", help="limit devices to region"
    )
    options_parser.add_argument(
        "--role", action="append", help="limit devices with role(s)"
    )
    options_parser.add_argument(
        "--exclude-role", action="append", help="exclude devices with role(s)"
    )
    options_parser.add_argument(
        "--exclude-tag", action="append", help="exclude devices with tag(s)"
    )
    options_parser.add_argument(
        "--output",
        type=argparse.FileType("w+"),
        default=sys.stdout,
        help="save inventory to filename",
    )

    nb_env_opts = os.environ.get("NETBOX_INVENTORY_OPTIONS")
    opt_arg = nb_env_opts.split(";") if nb_env_opts else None
    return options_parser.parse_args(opt_arg)


class NetBoxSession(requests.Session):
    def __init__(self, url, token):
        super(NetBoxSession, self).__init__()
        self.url = url
        self.headers["authorization"] = "Token %s" % token
        self.verify = False

    def prepare_request(self, request):
        request.url = self.url + request.url
        return super(NetBoxSession, self).prepare_request(request)


netbox: NetBoxSession = None


@lru_cache()
def get_site(site_slug):
    res = netbox.get("/api/dcim/sites/", params={"slug": site_slug})
    res.raise_for_status()
    return res.json()["results"][0]


def create_csv_file(inventory_records, cli_opts):
    csv_wr = csv.writer(cli_opts.output)
    csv_wr.writerow(CSV_FIELD_NAMES)

    result = chain.from_iterable(map(rec_to_csv, inventory_records))
    for rec in result:
        csv_wr.writerow(rec)


def fetch_inventory(cli_opts):
    global netbox

    try:
        nb_url = os.environ["NETBOX_ADDR"]
        nb_token = os.environ["NETBOX_TOKEN"]
    except KeyError as exc:
        sys.exit(f"ERROR: missing envirnoment variable: {exc.args[0]}")

    netbox = NetBoxSession(url=nb_url, token=nb_token)

    # -------------------------------------------------------------------------
    # perform a GET on the API URL to obtain the Netbox version; the value is
    # stored in the response header.  convert to tuple(int) for comparison
    # purposes.  If the Netbox version is after 2.6 the API status/choice
    # changed from int -> str.
    # -------------------------------------------------------------------------

    res = netbox.get("/api")
    api_ver = tuple(map(int, res.headers["API-Version"].split(".")))
    params = dict(limit=0, status=1, has_primary_ip="true")
    params["exclude"] = "config_context"

    if api_ver > (2, 6):
        params["status"] = "active"

    if cli_opts.site:
        params["site"] = cli_opts.site

    if cli_opts.region:
        params["region"] = cli_opts.region

    res = netbox.get("/api/dcim/devices/", params=params)
    if not res.ok:
        sys.exit("FAIL: get inventory: " + res.text)

    body = res.json()
    device_list = body["results"]

    # -------------------------------------------------------------------------
    # User Filters
    # -------------------------------------------------------------------------

    # If Caller provided an explicit list of device-roles, then filter the
    # device list based on those roles before creating the inventory

    filter_functions = []

    if cli_opts.role:

        def filter_role(dev_dict):
            return dev_dict["device_role"]["slug"] in cli_opts.role

        filter_functions.append(filter_role)

    if cli_opts.exclude_role:

        def filter_ex_role(dev_dict):
            return dev_dict["device_role"]["slug"] not in cli_opts.exclude_role

        filter_functions.append(filter_ex_role)

    if cli_opts.exclude_tag:
        ex_tag_set = set(cli_opts.exclude_tag)

        def filter_ex_tag(dev_dict):
            return not set(dev_dict["tags"]) & ex_tag_set

        filter_functions.append(filter_ex_tag)

    def apply_filters():
        for dev_dict in device_list:
            if all(fn(dev_dict) for fn in filter_functions):
                yield dev_dict

    return apply_filters() if filter_functions else iter(device_list)


def build_inventory():
    cli_opts = cli()
    inventory = fetch_inventory(cli_opts)
    create_csv_file(inventory, cli_opts)


if __name__ == "__main__":
    disable_warnings()
    build_inventory()
