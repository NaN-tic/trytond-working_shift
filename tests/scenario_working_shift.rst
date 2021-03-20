======================
Working Shift Scenario
======================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules, set_user
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()
    >>> now = datetime.datetime.now()

Activate working_shift::

    >>> config = activate_modules('working_shift')

Create company::

    >>> _ = create_company()
    >>> company = get_company()
    >>> party = company.party

Create Employee::

    >>> Party = Model.get('party.party')
    >>> Employee = Model.get('company.employee')
    >>> User = Model.get('res.user')
    >>> party = Party(name='Employee')
    >>> party.save()
    >>> employee = Employee()
    >>> employee.party = party
    >>> employee.company = company
    >>> employee.save()
    >>> user, = User.find([])
    >>> user.employees.append(employee)
    >>> user.employee = employee
    >>> user.save()
    >>> set_user(user)

Configure sequences::

    >>> WorkingShiftConfig = Model.get('working_shift.configuration')
    >>> Sequence = Model.get('ir.sequence')
    >>> working_shift_config = WorkingShiftConfig(1)
    >>> working_shift_sequence, = Sequence.find([
    ...     ('name', '=', 'Working Shift')])
    >>> working_shift_config.working_shift_sequence = working_shift_sequence
    >>> working_shift_config.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create working shift::

    >>> Shift = Model.get('working_shift')
    >>> shift = Shift()
    >>> shift.employee == employee
    True
    >>> shift.end = shift.start + relativedelta(days=1)
    >>> shift.save()
    >>> shift.click('confirm')
