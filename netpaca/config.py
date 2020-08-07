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

from contextvars import ContextVar  # noqa

import toml
from nwkatk.config_model import config_validation_errors

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
