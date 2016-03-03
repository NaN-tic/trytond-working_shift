======================
Working Shift Scenario
======================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()
    >>> now = datetime.datetime.now()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install working_shift::

    >>> Module = Model.get('ir.module.module')
    >>> module, = Module.find([('name', '=', 'working_shift')])
    >>> module.click('install')
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create Employee::

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
    True
