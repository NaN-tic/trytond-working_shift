# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import working_shift
from . import user
from . import employee
from . import working_day


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequence,
        working_shift.WorkingShift,
        working_shift.EmployeeWorkingShiftStart,
        user.User,
        employee.Employee,
        working_day.WorkingDayRule,
        working_day.WorkingDay,
        working_day.WorkingDayStart,
        module='working_shift', type_='model')
    Pool.register(
        working_shift.EmployeeWorkingShift,
        working_day.WorkingDayWizard,
        module='working_shift', type_='wizard')
