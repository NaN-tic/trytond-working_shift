# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .intervention import *
from .working_shift import *


def register():
    Pool.register(
        WorkingShiftConfiguration,
        WorkingShiftConfigurationCompany,
        WorkingShift,
        Intervention,
        module='working_shift', type_='model')
