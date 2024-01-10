# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from trytond import backend
from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pyson import Eval
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.model.exceptions import AccessError
from trytond.exceptions import UserError

__all__ = ['WorkingShift', 'EmployeeWorkingShiftStart', 'EmployeeWorkingShift']

STATES = {
    'readonly': Eval('state') != 'draft',
    }


def start_date_searcher(name, clause):
    operator = clause[1]
    if operator == '>':
        return [
            ('start', '>=',
                datetime.datetime.combine(
                    clause[2] + relativedelta(days=1),
                    datetime.time(0, 0))),
            ]
    elif operator == '>=':
        value = clause[2]
        if value:
            value = datetime.datetime.combine(value, datetime.time(0, 0))
        return [
            ('start', '>=', value),
            ]
    elif operator == '<':
        value = clause[2]
        if value:
            value = datetime.datetime.combine(value, datetime.time(0, 0))
        return [
            ('start', '<', value),
            ]
    elif operator == '<=':
        value = clause[2]
        if value:
            value = datetime.datetime.combine(value + relativedelta(days=1),
                datetime.time(0, 0))
        return [
            ('start', '<', value),
            ]
    elif operator == '=':
        if clause[2] is None:
            return [('start', '=', None)]
        else:
            return [
                ('start', '>=',
                    datetime.datetime.combine(clause[2], datetime.time(0, 0))),
                ('start', '<',
                    datetime.datetime.combine(
                        clause[2] + relativedelta(days=1),
                        datetime.time(0, 0))),
                ]
    elif operator == '!=':
        if clause[2] is None:
            return [('start', '!=', None)]
        else:
            return [
                ['OR',
                    ('start', '<',
                        datetime.datetime.combine(
                            clause[2], datetime.time(0, 0))),
                    ('start', '>=',
                        datetime.datetime.combine(
                            clause[2] + relativedelta(days=1),
                            datetime.time(0, 0))),
                    ],
                ]
    raise NotImplementedError


class WorkingShift(Workflow, ModelSQL, ModelView):
    'Working Shift'
    __name__ = 'working_shift'
    _rec_name = 'code'
    code = fields.Char('Code', readonly=True, required=True)
    employee = fields.Many2One('company.employee', 'Employee', required=True,
        states=STATES)
    start = fields.DateTime('Start', required=True, states=STATES)
    start_date = fields.Function(fields.Date('Start Date'),
        'get_start_date', searcher='search_start_date')
    end = fields.DateTime('End', domain=[
            ['OR',
                ('end', '=', None),
                ('end', '>', Eval('start')),
                ],
            ],
        states={
            'readonly': Eval('state').in_(['cancelled', 'done']),
            'required': Eval('state').in_(['done']),
            }, depends=['start'])
    hours = fields.Function(fields.Numeric('Hours', digits=(16, 2)),
        'on_change_with_hours')
    comment = fields.Text('Comment')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancelled', "Cancelled"),
            ], 'State', required=True, readonly=True)

    @classmethod
    def __setup__(cls):
        super(WorkingShift, cls).__setup__()
        cls._order.insert(0, ('code', 'DESC'))
        cls._order.insert(1, ('id', 'DESC'))
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('confirmed', 'done'),
                ('draft', 'cancelled'),
                ('confirmed', 'cancelled'),
                ('done', 'cancelled'),
                ('cancelled', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state') == 'cancelled',
                    'icon': 'tryton-cancel',
                    },
                'draft': {
                    'invisible': Eval('state') != 'cancelled',
                    'icon': 'tryton-clear',
                    },
                'confirm': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-forward',
                    },
                'done': {
                    'invisible': Eval('state') != 'confirmed',
                    'icon': 'tryton-ok',
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().connection.cursor()
        sql_table = cls.__table__()

        # Migration from 3.4.0: renamed start/end_date to start/end
        table = backend.TableHandler(cls, module_name)
        start_end_date_exist = (table.column_exist('start_date')
            and table.column_exist('end_date'))

        super(WorkingShift, cls).__register__(module_name)

        # Migration from 3.4.0: renamed start/end_date to start/end
        if start_end_date_exist:
            cursor.execute(*sql_table.update(
                    columns=[sql_table.start, sql_table.end],
                    values=[sql_table.start_date, sql_table.end_date]))
            table = backend.TableHandler(cls, module_name)
            table.not_null_action('start', action='add')
            table.drop_column('start_date')
            table.drop_column('end_date')

        # Migration from 5.6: rename state canceled to cancelled
        cursor.execute(*sql_table.update(
                [sql_table.state], ['cancelled'],
                where=sql_table.state == 'canceled'))

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_start():
        return datetime.datetime.now()

    @staticmethod
    def default_employee():
        return Transaction().context.get('employee')

    def get_rec_name(self, name):
        Company = Pool().get('company.company')

        locale = Transaction().context.get('locale')
        dformat = '%Y/%m/%d %H:%M'
        if locale:
            dformat = locale.get('date', '%Y/%m/%d') + ' %H:%M'

        start = self.start
        end = self.end

        company_id = Transaction().context.get('company')
        if company_id:
            company = Company(company_id)
            if company.timezone:
                timezone = pytz.timezone(company.timezone)
                if self.start:
                    start = timezone.localize(self.start)
                    start = self.start + start.utcoffset()
                if self.end:
                    end = timezone.localize(self.end)
                    end = self.end + end.utcoffset()

        rec_name = '[%s] %s - %s' % (
            self.code, self.employee.rec_name, start.strftime(dformat))
        if end:
            rec_name += ' - %s' % end.strftime(dformat)
        return rec_name

    def get_start_date(self, name):
        if self.start:
            return self.start.date()

    @classmethod
    def search_start_date(cls, name, clause):
        return start_date_searcher(name, clause)

    @fields.depends('start', 'end')
    def on_change_with_hours(self, name=None):
        if not self.start or not self.end:
            return Decimal(0)
        hours = (self.end - self.start).total_seconds() / 3600.0
        digits = self.__class__.hours.digits
        return Decimal(str(hours)).quantize(Decimal(str(10 ** -digits[1])))

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, working_shifts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, working_shifts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, working_shifts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, working_shifts):
        pass

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Config = pool.get('working_shift.configuration')

        config = Config(1)
        if not config.working_shift_sequence:
            raise UserError(gettext(
                'working_shift.missing_working_shift_sequence'))
        for value in vlist:
            if value.get('code'):
                continue
            value['code'] = config.working_shift_sequence.get()
        return super(WorkingShift, cls).create(vlist)

    @classmethod
    def copy(cls, working_shifts, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['code'] = None
        return super(WorkingShift, cls).copy(working_shifts, default=default)

    @classmethod
    def delete(cls, working_shifts):
        for working_shift in working_shifts:
            if working_shift.state != 'draft':
                raise AccessError(gettext('working_shift.delete_non_draft',
                    ws=working_shift.rec_name))
        super(WorkingShift, cls).delete(working_shifts)


class EmployeeWorkingShiftStart(ModelView):
    'Employee Working Shift Start'
    __name__ = 'employee.working_shift.start'
    working_shift = fields.Many2One('working_shift', 'Working Shift',
        domain=[
            ('employee', '=', Eval('employee', -1)),
            ('state', 'in', ['draft', 'confirmed']),
        ])
    employee = fields.Many2One('company.employee', 'Employee', required=True,
        readonly=True)
    start = fields.DateTime('Start')
    end = fields.DateTime('End')

    @classmethod
    def default_working_shift(cls):
        pool = Pool()
        WorkingShift = pool.get('working_shift')
        Date = pool.get('ir.date')

        start_date = datetime.datetime.combine(
                    Date.today(),
                    datetime.time(0, 0))
        working_shifts = WorkingShift.search([
                ('employee', '=', Transaction().context.get('employee', -1)),
                ('state', 'in', ['draft', 'confirmed']),
                ('start', '>=', start_date),
                ('end', '=', None),
            ], limit=1, order=[('start', 'ASC')])
        if working_shifts:
            return working_shifts[0].id

    @staticmethod
    def default_employee():
        return Transaction().context.get('employee')

    @fields.depends('working_shift')
    def on_change_with_start(self):
        return (self.working_shift.start
            if self.working_shift else datetime.datetime.now())

    @fields.depends('working_shift')
    def on_change_with_end(self):
        return (self.working_shift.end or datetime.datetime.now()
            if self.working_shift else None)


class EmployeeWorkingShift(Wizard):
    'Employee Working Shift'
    __name__ = 'employee.working_shift'
    start = StateView('employee.working_shift.start',
        'working_shift.employee_working_shift_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Done', 'set_working_shift', 'tryton-ok', default=True),
            ])
    set_working_shift = StateTransition()

    def transition_set_working_shift(self):
        WorkingShift = Pool().get('working_shift')

        start = self.start.start
        end = self.start.end

        working_shift = self.start.working_shift
        if self.start.working_shift:
            working_shift = self.start.working_shift
        else:
            working_shift = WorkingShift()
            working_shift.start = datetime.datetime.now()
            working_shift.employee = self.start.employee
        if start:
            working_shift.start = start
        if end:
            working_shift.end = end
        working_shift.save()
        WorkingShift.confirm([working_shift])
        return 'end'

    def end(self):
        return 'reload menu'
