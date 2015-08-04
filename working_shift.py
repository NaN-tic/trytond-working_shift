# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
from decimal import Decimal

from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['WorkingShift']
__metaclass__ = PoolMeta

STATES = {
    'readonly': Eval('state') != 'draft',
    }
DEPENDS = ['state']


class WorkingShift(Workflow, ModelSQL, ModelView):
    'Working Shift'
    __name__ = 'working_shift'
    _rec_name = 'code'
    code = fields.Char('Code', readonly=True, required=True)
    employee = fields.Many2One('company.employee', 'Employee', required=True,
        states=STATES, depends=DEPENDS)
    start_date = fields.DateTime('Start Date', required=True, states=STATES,
        depends=DEPENDS)
    end_date = fields.DateTime('End Date', domain=[
            ['OR',
                ('end_date', '=', None),
                ('end_date', '>', Eval('start_date')),
                ],
            ],
        states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('state').in_(['confirmed', 'done']),
            }, depends=DEPENDS+['start_date'])
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
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('confirmed', 'done'),
                ('canceled', 'draft'),
                ('draft', 'canceled'),
                ('confirmed', 'canceled'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state').in_(['canceled', 'done']),
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
        cls._error_messages.update({
                'missing_working_shift_sequence': (
                    'There is no working shift sequence defined.\n'
                    'Please, define one in working shift configuration.'),
                'delete_non_draft': ('Working Shift "%s" can not be deleted '
                    'because it is not in draft state.'),
                })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_start_date():
        return datetime.datetime.now()

    @staticmethod
    def default_employee():
        return Transaction().context.get('employee')

    @fields.depends('start_date', 'end_date')
    def on_change_with_hours(self, name=None):
        if not self.start_date or not self.end_date:
            return Decimal(0)
        hours = (self.end_date - self.start_date).total_seconds() / 3600.0
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
            cls.raise_user_error('missing_working_shift_sequence')
        for value in vlist:
            if value.get('code'):
                continue
            value['code'] = Sequence.get_id(config.working_shift_sequence.id)
        return super(WorkingShift, cls).create(vlist)

    @classmethod
    def delete(cls, working_shifts):
        for working_shift in working_shifts:
            if working_shift.state != 'draft':
                cls.raise_user_error('delete_non_draft', working_shift.rec_name)
        super(WorkingShift, cls).delete(working_shifts)
