import click
from functools import reduce, update_wrapper

from netpaca.core import inventory

# -----------------------------------------------------------------------------
# Inventory Options
# -----------------------------------------------------------------------------


opt_inventory = click.option("--inventory", "-i", help="Inventory filepath")

opt_limits = click.option(
    "--limit", "-il", multiple=True, help="limit into inventory", is_eager=True
)

opt_excludes = click.option(
    "--exclude", "-ie", multiple=True, help="exclude from inventory", is_eager=True
)


def opts_inventory(in_fn_deco):
    return reduce(
        lambda _d, fn: fn(_d), [opt_inventory, opt_limits, opt_excludes], in_fn_deco
    )


# -----------------------------------------------------------------------------
# Inventory parameter generator
# -----------------------------------------------------------------------------


def pass_inventory_records(f):
    """
    This decorator is used to load the inventory records using the provided inventory options.  The Caller should use
    this decorator when creating a Click.Command so that the records are available in the callback function.

    Examples
    --------
    @click.command()
    @opts_inventory
    @pass_inventory_records
    def cli_foo(inventory_records, **kwargs):
        click.echo(f"There are {len(inventory_records)} inventory items.")
    """

    @click.pass_context
    def preload_inventory(ctx, *args, **kwargs):

        inv_fp = kwargs["inventory"]
        if not inv_fp:
            ctx.fail("Missing inventory option")

        inv = inventory.load(
            filepath=inv_fp, limits=kwargs.get("limit"), excludes=kwargs.get("exclude")
        )

        if not inv:
            ctx.fail(f"No inventory matching limits in: {inv_fp}")

        return ctx.invoke(f, inv, *args, **kwargs)

    return update_wrapper(preload_inventory, f)
