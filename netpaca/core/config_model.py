import os
from os.path import expandvars
import re
from itertools import chain
from pkg_resources import EntryPoint, iter_entry_points
from importlib import import_module
from first import first

from pydantic import BaseModel, SecretStr, FilePath, AnyHttpUrl, ValidationError

_var_re = re.compile(
    r"\${(?P<bname>[a-z0-9_]+)}" r"|" r"\$(?P<name>[^{][a-z_0-9]+)", flags=re.IGNORECASE
)


class NoExtraBaseModel(BaseModel):
    class Config:
        extra = "forbid"


class EnvExpand(str):
    """
    When a string value contains a reference to an environment variable, use
    this type to expand the contents of the variable using os.path.expandvars.

    For example like:
        password = "$MY_PASSWORD"
        foo_password = "${MY_PASSWORD}_foo"

    will be expanded, given MY_PASSWORD is set to 'boo!' in the environment:
        password -> "boo!"
        foo_password -> "boo!_foo"
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if found_vars := list(filter(len, chain.from_iterable(_var_re.findall(v)))):
            for var in found_vars:
                if (var_val := os.getenv(var)) is None:
                    raise ValueError(f'Environment variable "{var}" missing.')

                if not len(var_val):
                    raise ValueError(f'Environment variable "{var}" empty.')

            return expandvars(v)

        return v


class EnvSecretStr(EnvExpand, SecretStr):
    @classmethod
    def validate(cls, v):
        return SecretStr.validate(EnvExpand.validate(v))


class EnvSecretUrl(EnvSecretStr):
    """
    The EnvSecretUrl is used to define configuraiton options that store as
    Secret and validate as AnyHttpUrl
    """

    @classmethod
    def __get_validators__(cls):
        yield EnvSecretStr.validate
        yield cls.validate

    @classmethod
    def validate(cls, v):
        url = v.get_secret_value()

        # the only way I've realized to validate an AnyHttpUrl field is to
        # define a model class and then attempt to instantiate an instance.
        # TODO: find a better way.

        class __T(BaseModel):
            url: AnyHttpUrl

        try:
            __T(url=url)
        except ValidationError as exc:
            errmsg = exc.errors()[0]["msg"]
            raise ValueError(f"{errmsg}: {url}")

        return v


class Credential(NoExtraBaseModel):
    username: EnvExpand
    password: EnvSecretStr


class FilePathEnvExpand(FilePath):
    """ A FilePath field whose value can interpolated from env vars """

    @classmethod
    def __get_validators__(cls):
        yield from EnvExpand.__get_validators__()
        yield from FilePath.__get_validators__()


class ImportPath(BaseModel):
    @classmethod
    def validate(cls, v):
        try:
            return import_module(name=v)
        except ImportError as exc:
            raise ValueError(f"Unable to import {v}: {str(exc)}")


class EntryPointImportPath(BaseModel):
    @classmethod
    def validate(cls, v):
        try:
            return EntryPoint.parse(f"ep = {v}").resolve()
        except ImportError:
            raise ValueError(f"Unable to import {v}")


class PackagedEntryPoint(BaseModel):
    @classmethod
    def validate(cls, v):
        try:
            group, _, name = v.partition(":")
            ep = first(iter_entry_points(group=group, name=name))
            return ep.resolve()

        except AttributeError:
            raise ValueError(f"Unable to find package-import: {v}")

        except ImportError as exc:
            raise ValueError(f"Unable to import {v}: {str(exc)}")


def config_validation_errors(errors, filepath=None):
    sp_4 = " " * 4

    as_human = ["Configuration errors", f"{sp_4}File:[{filepath or 'ENV'}]"]

    for _err in errors:
        loc_str = ".".join(map(str, _err["loc"]))
        as_human.append(f"{sp_4}Section: [{loc_str}]: {_err['msg']}")

    return "\n".join(as_human)
