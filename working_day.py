from datetime import timedelta
from decimal import Decimal
from trytond.model import MatchMixin, ModelSQL, ModelView, fields, Unique
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool
from trytond.transaction import Transaction

ZERO = Decimal(0)

def date_range(start_date, end_date):
    if end_date < start_date:
        return
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


class WorkingDayRule(ModelSQL, ModelView, MatchMixin):
    'Working Day Rule'
    __name__ = 'employee.working_day.rule'

    weekday = fields.Many2One('ir.calendar.day', 'Day of Week')
    hours = fields.Numeric('Hours', required=True)

    @classmethod
    def compute(cls, weekday, rules=None):
        if rules is None:
            rules = cls.search([])

        pattern = {
            'weekday': weekday,
            }
        for rule in rules:
            if not rule.match(pattern):
                continue
            break
        else:
            return ZERO
        return rule.hours


class WorkingDay(ModelSQL, ModelView):
    'Working Day'
    __name__ = 'employee.working_day'

    employee = fields.Many2One('company.employee', 'Employee', required=True)
    date = fields.Date('Date', required=True)
    hours = fields.Numeric('Hours', required=True)
    missing_hours = fields.Function(fields.Numeric('Missing Hours'),
        'get_missing_hours')
    exceeding_hours = fields.Function(fields.Numeric('Exceeding Hours'),
        'get_exceeding_hours')
    working_shifts = fields.Function(fields.One2Many('working_shift',
        None, 'Working Shifts'), 'get_working_shifts')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('employee_date_uniq', Unique(t, t.employee, t.date),
                'working_shift.msg_working_day_unique'),
        ]

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            ('employee.rec_name',) + tuple(clause[1:]),
            ]

    def get_rec_name(self, name):
        return self.employee.rec_name + ' ' + self.date.strftime('%Y-%m-%d')

    @classmethod
    def get_working_shifts(cls, days, name):
        WorkingShift = Pool().get('working_shift')

        employees = [day.employee.id for day in days]
        dates = [x.date for x in days]

        shifts = WorkingShift.search([
                ('employee', 'in', employees),
                ('start', '>=', min(dates).strftime('%Y-%m-%d 00:00:00')),
                ('end', '<=', max(dates).strftime('%Y-%m-%d 23:59:59')),
                ])
        items = {}
        for shift in shifts:
            key = (shift.employee.id, shift.start_date)
            items.setdefault(key, []).append(shift.id)
        res = {}
        for day in days:
            key = (day.employee.id, day.date)
            res[day.id] = items.get(key, [])
        return res

    def get_missing_hours(self, name):
        done = sum([x.hours for x in self.working_shifts])
        return max(0, self.hours - done)

    def get_exceeding_hours(self, name):
        done = sum([x.hours for x in self.working_shifts])
        return max(0, done - self.hours)

    @classmethod
    def compute(cls, start_date=None, end_date=None, employees=None):
        pool = Pool()
        Employee = pool.get('company.employee')
        Date = pool.get('ir.date')
        Weekday = pool.get('ir.calendar.day')
        Rule = pool.get('employee.working_day.rule')
        try:
            Leave = pool.get('employee.leave')
        except KeyError:
            Leave = None

        if start_date is None:
            start_date = Date.today().replace(day=1, month=1)

        if end_date is None:
            end_date = Date.today().replace(day=31, month=12)

        if employees is None:
            employees = Employee.search([
                    ('company', '=', Transaction().context.get('company')),
                    ('create_working_days', '=', True),
                    ('OR',
                        ('start_date', '<=', end_date),
                        ('start_date', '=', None),
                        ),
                    ('OR',
                        ('end_date', '>=', start_date),
                        ('end_date', '=', None),
                        ),
                    ])

        rules = Rule.search([])

        leave_days = {x.id: {} for x in employees}
        if Leave:
            # TODO: Consider hours
            leaves = Leave.search([
                    ('employee', 'in', [x.id for x in employees]),
                    ('start', '<=', end_date),
                    ('end', '>=', start_date),
                    ])
            for leave in leaves:
                date = leave.start
                daily_hours = leave.hours / ((leave.end - leave.start).days + 1)
                for date in date_range(leave.start, leave.end):
                    if date < start_date or date > end_date:
                        continue
                    leave_days[leave.employee.id][date] = daily_hours

        weekdays = {x.index: x.id for x in Weekday.search([])}

        existing = cls.search([
            ('employee', 'in', [x.id for x in employees]),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ])
        existing = {(x.employee.id, x.date): x for x in existing}

        to_save = []
        for employee in employees:
            # Loop for all dates from start_date to end_date
            # and create working day for each date
            if employee.start_date:
                employee_start = max(start_date, employee.start_date)
            else:
                employee_start = start_date
            if employee.end_date:
                employee_end = min(end_date, employee.end_date)
            else:
                employee_end = end_date
            for date in date_range(employee_start, employee_end):
                key = (employee.id, date)
                working_day = existing.get(key)
                hours = Rule.compute(weekdays[date.weekday()], rules=rules)
                hours -= leave_days.get(employee.id, {}).get(date, 0)
                if hours <= 0:
                    continue
                if not working_day:
                    working_day = cls()
                    working_day.employee = employee
                    working_day.date = date

                existing.pop(key, None)
                working_day.hours = hours
                to_save.append(working_day)

        cls.delete(list(existing.values()))
        cls.save(to_save)


class WorkingDayStart(ModelView):
    'Working Day Start'
    __name__ = 'employee.working_day.start'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    @staticmethod
    def default_start_date():
        Date = Pool().get('ir.date')
        return Date.today().replace(day=1, month=1)

    @staticmethod
    def default_end_date():
        Date = Pool().get('ir.date')
        return Date.today().replace(day=31, month=12)


class WorkingDayWizard(Wizard):
    'Working Day Wizard'
    __name__ = 'employee.working_day.create'

    start = StateView('employee.working_day.start',
        'working_shift.working_day_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_ = StateTransition()

    def transition_create_(self):
        WorkingDay.compute(
            start_date=self.start.start_date,
            end_date=self.start.end_date)
        return 'end'

