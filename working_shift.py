# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from trytond import backend
from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['WorkingShift']
__metaclass__ = PoolMeta

STATES = {
    'readonly': Eval('state') != 'draft',
    }
DEPENDS = ['state']


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
        return [
            ('start', '>=',
                datetime.datetime.combine(clause[2], datetime.time(0, 0))),
            ]
    elif operator == '<':
        return [
            ('start', '<',
                datetime.datetime.combine(clause[2], datetime.time(0, 0))),
            ]
    elif operator == '<=':
        return [
            ('start', '<',
                datetime.datetime.combine(
                    clause[2] + relativedelta(days=1),
                    datetime.time(0, 0))),
            ]
    elif operator == '=':
        return [
            ('start', '>=',
                datetime.datetime.combine(clause[2], datetime.time(0, 0))),
            ('start', '<',
                datetime.datetime.combine(
                    clause[2] + relativedelta(days=1),
                    datetime.time(0, 0))),
            ]
    elif operator == '!=':
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
        states=STATES, depends=DEPENDS)
    start = fields.DateTime('Start', required=True, states=STATES,
        depends=DEPENDS)
    start_date = fields.Function(fields.Date('Start Date'),
        'get_start_date', searcher='search_start_date')
    end = fields.DateTime('End', domain=[
            ['OR',
                ('end', '=', None),
                ('end', '>', Eval('start')),
                ],
            ],
        states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('state').in_(['confirmed', 'done']),
            }, depends=DEPENDS+['start'])
    hours = fields.Function(fields.Numeric('Hours', digits=(16, 2)),
        'on_change_with_hours')
    interventions = fields.One2Many('working_shift.intervention', 'shift',
        'Interventions', states=STATES, depends=DEPENDS)
    comment = fields.Text('Comment')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('canceled', 'Cancelled'),
            ], 'State', required=True, readonly=True, select=True)

    @classmethod
    def __setup__(cls):
        super(WorkingShift, cls).__setup__()
        cls._order.insert(0, ('code', 'DESC'))
        cls._order.insert(1, ('id', 'DESC'))
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('confirmed', 'done'),
                ('draft', 'canceled'),
                ('confirmed', 'canceled'),
                ('done', 'canceled'),
                ('canceled', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state') == 'canceled',
                    'icon': 'tryton-cancel',
                    },
                'draft': {
                    'invisible': Eval('state') != 'canceled',
                    'icon': 'tryton-clear',
                    },
                'confirm': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-go-next',
                    },
                'done': {
                    'invisible': Eval('state') != 'confirmed',
                    'icon': 'tryton-ok',
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().connection.cursor()
        sql_table = cls.__table__()

        # Migration from 3.4.0: renamed start/end_date to start/end
        table = TableHandler(cls, module_name)
        start_end_date_exist = (table.column_exist('start_date')
            and table.column_exist('end_date'))

        super(WorkingShift, cls).__register__(module_name)

        # Migration from 3.4.0: renamed start/end_date to start/end
        if start_end_date_exist:
            cursor.execute(*sql_table.update(
                    columns=[sql_table.start, sql_table.end],
                    values=[sql_table.start_date, sql_table.end_date]))
            table = TableHandler(cls, module_name)
            table.not_null_action('start', action='add')
            table.drop_column('start_date')
            table.drop_column('end_date')

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_start():
        return datetime.datetime.now()

    @staticmethod
    def default_employee():
        return Transaction().context.get('employee')

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
    @Workflow.transition('canceled')
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
        Sequence = pool.get('ir.sequence')
        Config = pool.get('working_shift.configuration')

        config = Config(1)
        if not config.working_shift_sequence:
            raise UserError(gettext(
                'working_shift.missing_working_shift_sequence'))
        for value in vlist:
            if value.get('code'):
                continue
            value['code'] = Sequence.get_id(config.working_shift_sequence.id)
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
                raise UserError(gettext('working_shift.delete_non_draft',
                    ws=working_shift.rec_name))
        super(WorkingShift, cls).delete(working_shifts)
