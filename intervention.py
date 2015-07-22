# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Intervention']
__metaclass__ = PoolMeta

STATES = {
    'readonly': Eval('shift_state') != 'draft',
    }
DEPENDS = ['shift_state']


class Intervention(ModelSQL, ModelView):
    'Intervention'
    __name__ = 'working_shift.intervention'
    code = fields.Char('Code', required=True, readonly=True)
    shift = fields.Many2One('working_shift', 'Working Shift',
        required=True, select=True, ondelete='CASCADE', states=STATES,
        depends=DEPENDS)
    shift_state = fields.Function(fields.Selection([], 'Shift State'),
        'on_change_with_shift_state')
    reference = fields.Char('Reference', states=STATES, depends=DEPENDS)
    contact_name = fields.Char('Contact Name', states=STATES, depends=DEPENDS)
    party = fields.Many2One('party.party', 'Party', states=STATES,
        depends=DEPENDS)
    start_date = fields.DateTime('Start Date', required=True, states=STATES,
        depends=DEPENDS)
    end_date = fields.DateTime('End Date', domain=[
            ['OR',
                ('end_date', '=', None),
                ('end_date', '>', Eval('start_date')),
                ],
            ],
        states=STATES, depends=DEPENDS+['start_date'])
    comments = fields.Text('Comments', states=STATES, depends=DEPENDS)

    @classmethod
    def __setup__(cls):
        super(Intervention, cls).__setup__()
        cls._error_messages.update({
                'missing_intervention_sequence': ('There is no intervention'
                    ' sequence defined. Please define one in working shift '
                    'configuration.'),
                'date_outside_working_shift': ('Intervention\'s '
                    '"%(intervention)s" period is outside working shift '
                    '"%(shift)s" period.'),
                'delete_non_draft': ('Intervention "%s" can not be deleted '
                    'because its working shift is not in draft state.'),
                })
        # Copy selection from shift
        Shift = Pool().get('working_shift')
        cls.shift_state.selection = Shift.state.selection

    def get_rec_name(self, name):
        res = self.code
        if self.reference:
            res += ' (' + self.reference + ')'
        return res

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('code',) + tuple(clause[1:]),
            ('reference',) + tuple(clause[1:]),
            ]

    @fields.depends('shift')
    def on_change_with_shift_state(self, name=None):
        if self.shift:
            return self.shift.state

    @classmethod
    def validate(cls, interventions):
        super(Intervention, cls).validate(interventions)
        for intervention in interventions:
            intervention.check_working_shift_period()

    def check_working_shift_period(self):
        error = False
        if self.start_date < self.shift.start_date:
            error = True
        if self.shift.end_date:
            if (self.start_date > self.shift.end_date or
                    (self.end_date and self.end_date > self.shift.end_date)):
                error = True
        if self.end_date:
            if self.end_date < self.shift.start_date:
                error = True

        if error:
            self.raise_user_error('date_outside_working_shift', {
                    'intervention': self.rec_name,
                    'shift': self.shift.rec_name,
                    })

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('working_shift.configuration')

        config = Config(1)
        if not config.intervention_sequence:
            cls.raise_user_error('missing_intervention_sequence')
        for value in vlist:
            if value.get('code'):
                continue
            value['code'] = Sequence.get_id(config.intervention_sequence.id)
        return super(Intervention, cls).create(vlist)

    @classmethod
    def delete(cls, interventions):
        for intervention in interventions:
            if intervention.shift.state != 'draft':
                cls.raise_user_error('delete_non_draft', intervention.rec_name)
        super(Intervention, cls).delete(interventions)
