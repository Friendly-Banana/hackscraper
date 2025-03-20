# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")

# by importing controllers you expose the actions defined in it
from . import controllers

# by importing db you expose it to the _dashboard/dbadmin
from .models import db

# import the scheduler
from .tasks import scheduler

# optional parameters
__version__ = "0.0.1"
__author__ = "Gabriel me@gabriels.cloud>"
__license__ = "ARR"
