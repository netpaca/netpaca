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

import sys
import logging


def setup_logging():
    log = logging.getLogger(__package__)
    log.addHandler(logging.StreamHandler(stream=sys.stdout))
    log.handlers[0].setFormatter(
        logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s")
    )
    return log


def get_logger():
    return logging.getLogger(__package__)
