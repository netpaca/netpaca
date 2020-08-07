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
