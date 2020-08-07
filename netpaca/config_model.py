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


from typing import Dict, Optional, List, Type
from operator import itemgetter

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from first import first

from pydantic import (
    BaseSettings,
    Field,
    PositiveInt,
    validator,
    root_validator,
)

from pydantic import ValidationError  # noqa: F401

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from netpaca import consts

from nwkatk.config_model import (
    NoExtraBaseModel,
    EnvExpand,
    EnvSecretStr,
    Credential,
    PackagedEntryPoint,
    EntryPointImportPath,
    ImportPath,
    FilePathEnvExpand,
)

from netpaca.collectors import CollectorType, CollectorConfigModel
from netpaca.drivers import DriverBase
from netpaca.exporters import ExporterBase


class DefaultCredential(Credential, BaseSettings):
    username: EnvExpand
    password: EnvSecretStr


class DefaultsModel(NoExtraBaseModel, BaseSettings):
    interval: Optional[PositiveInt] = Field(default=consts.DEFAULT_INTERVAL)
    inventory: FilePathEnvExpand
    credentials: DefaultCredential
    exporters: Optional[List[str]]


class DeviceDriverModel(NoExtraBaseModel):
    use: Optional[Type[DriverBase]]
    driver: Optional[Type[DriverBase]]
    modules: List[ImportPath]

    @validator("use", pre=True)
    def _from_use_to_callable(cls, val):
        return PackagedEntryPoint.validate(val)

    @validator("driver", pre=True, always=True)
    def _from_driver_to_callable(cls, val, values):
        try:
            return EntryPointImportPath.validate(val) if val else values["use"]
        except KeyError:
            raise ValueError()


class CollectorModel(NoExtraBaseModel):
    use: Optional[Type[CollectorType]]
    collector: Optional[Type[CollectorType]]
    config: Optional[CollectorConfigModel]

    @validator("use", pre=True)
    def _from_use_to_callable(cls, val):
        return PackagedEntryPoint.validate(val)

    @validator("collector", pre=True, always=True)
    def _from_collector_to_callable(cls, val, values):
        try:
            return EntryPointImportPath.validate(val) if val else values["use"]
        except KeyError:
            raise ValueError("failed to import collector")

    @validator("config", pre=True, always=True)
    def _config_dict_to_obj(cls, val, values):
        try:
            return values["collector"].config.parse_obj(val or {})
        except KeyError:
            raise ValueError("failed to import collector")


class ExporterModel(NoExtraBaseModel):
    exporter: Optional[Type[ExporterBase]]
    use: Optional[Type[ExporterBase]]
    config: Optional[Dict]

    @validator("use", pre=True)
    def _from_use_to_callable(cls, val):
        return PackagedEntryPoint.validate(val)

    @root_validator
    def normalize_exporter(cls, values):
        try:
            values["exporter"] = first(itemgetter("exporter", "use")(values))
        except KeyError:
            raise ValueError("Missing one of ['exporter', 'use']")

        return values


class ConfigModel(NoExtraBaseModel):
    defaults: DefaultsModel
    device_drivers: Dict[str, DeviceDriverModel]
    collectors: Dict[str, CollectorModel]
    exporters: Dict[str, ExporterModel]

    @validator("exporters")
    def init_exporters(cls, exporters):
        for e_name, e_val in exporters.items():
            e_cls = e_val.exporter
            e_cfg_model = e_cls.config
            e_val.config = e_cfg_model.validate(e_val.config)
            e_inst = e_cls(e_name)
            e_inst.prepare(e_val.config)
            exporters[e_name] = e_inst

        return exporters
