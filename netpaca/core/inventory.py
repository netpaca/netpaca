# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import AnyStr, Optional, List
from pathlib import Path

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .filtering import create_filter
from .filetypes import CommentedCsvReader


def load(
    filepath: AnyStr,
    limits: Optional[List[AnyStr]] = None,
    excludes: Optional[List[AnyStr]] = None,
) -> List[dict]:
    """
    Loads the inventory from the `filepath` location, applies any of the filtering constraints specified by `limits`
    and/or `excludes`.

    Parameters
    ----------
    filepath
        Location of the inventory file on the local filesystem

    limits
        List of constrains that would allow inventory records

    excludes
        List of constraints that would exclude inventory records

    Returns
    -------
    List of inventory records (dict)
    """
    inventory_file = Path(filepath)
    if not inventory_file.exists():
        raise FileNotFoundError(
            f"Inventory file does not exist: {inventory_file.absolute()}"
        )

    iter_recs = CommentedCsvReader(inventory_file.open())
    field_names = iter_recs.fieldnames

    if limits:
        filter_fn = create_filter(constraints=limits, field_names=field_names)
        iter_recs = filter(filter_fn, iter_recs)

    if excludes:
        filter_fn = create_filter(
            constraints=excludes, field_names=field_names, include=False
        )
        iter_recs = filter(filter_fn, iter_recs)

    return list(iter_recs)
