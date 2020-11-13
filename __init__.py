# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import working_shift
from . import user
from . import employee


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequence,
        working_shift.WorkingShift,
        working_shift.EmployeeWorkingShiftStart,
        user.User,
        employee.Employee,
        module='working_shift', type_='model')
    Pool.register(
        working_shift.EmployeeWorkingShift,
        module='working_shift', type_='wizard')
