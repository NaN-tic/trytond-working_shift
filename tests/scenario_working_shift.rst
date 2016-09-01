======================
Working Shift Scenario
======================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()
    >>> now = datetime.datetime.now()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install working_shift::

    >>> Module = Model.get('ir.module')
    >>> module, = Module.find([('name', '=', 'working_shift')])
    >>> module.click('install')
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()
    >>> party = company.party

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create Employee::

    >>> Party = Model.get('party.party')
    >>> Employee = Model.get('company.employee')
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
    >>> config._context = User.get_preferences(True, config.context)

Configure sequences::

    >>> WorkingShiftConfig = Model.get('working_shift.configuration')
    >>> Sequence = Model.get('ir.sequence')
    >>> working_shift_config = WorkingShiftConfig(1)
    >>> intervention_sequence, = Sequence.find([
    ...     ('code', '=', 'working_shift.intervention')])
    >>> working_shift_config.intervention_sequence = intervention_sequence
    >>> working_shift_sequence, = Sequence.find([
    ...     ('code', '=', 'working_shift')])
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
    >>> intervention = shift.interventions.new()
    >>> intervention.start = now + relativedelta(minutes=1)
    >>> intervention.end = now + relativedelta(hours=1)
    >>> shift.save()

A confirmed intervention can not be deleted::

    >>> shift.click('confirm')
    >>> Intervention = Model.get('working_shift.intervention')
    >>> intervention, = Intervention.find([])
    >>> intervention.delete()
    Traceback (most recent call last):
        ...
    UserError: ('UserError', (u'Intervention "1" can not be deleted because its working shift is not in draft state.', ''))

Create an invalid intervention::

    >>> shift.click('cancel')
    >>> shift.click('draft')
    >>> invalid_intervention = shift.interventions.new()
    >>> invalid_intervention.start = now + relativedelta(days=2,
    ...     minutes=1)
    >>> invalid_intervention.end = now + relativedelta(days=2,
    ...     hours=1)
    >>> shift.save()
    Traceback (most recent call last):
        ...
    UserError: ('UserError', (u'Intervention\'s "2" period is outside working shift "1" period.', ''))
    >>> invalid_intervention.delete()
