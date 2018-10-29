# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import intervention
from . import working_shift


def register():
    Pool.register(
        configuration.WorkingShiftConfiguration,
        configuration.WorkingShiftConfigurationCompany,
        working_shift.WorkingShift,
        intervention.Intervention,
        module='working_shift', type_='model')
