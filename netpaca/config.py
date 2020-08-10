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
#

from contextvars import ContextVar  # noqa

import toml
from netpaca.core.config_model import config_validation_errors

from .config_model import ConfigModel, ValidationError


_config = ContextVar("config")


def load_config_file(ctx, param, value):  # noqa
    """ click option callback for processing the config option """
    try:
        config_data = toml.load(value)
        config_obj = ConfigModel.parse_obj(config_data)

    except ValidationError as exc:
        raise RuntimeError(
            config_validation_errors(errors=exc.errors(), filepath=value.name)
        )

    _config.set(config_obj)
    return config_obj


# @lru_cache
# def get_config():
#     return _config.get()
