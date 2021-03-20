# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, ModelSingleton, fields
from trytond.pyson import Eval, Id
from trytond.pool import Pool
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)

__all_ = ['Configuration', 'ConfigurationSequence']

working_shift_sequence = fields.Many2One(
        'ir.sequence', "Working Shift Sequence", required=True,
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('sequence_type', '=', Id('working_shift',
                'sequence_type_working_shift')),
            ])

def default_func(field_name):
    @classmethod
    def default(cls, **pattern):
        return getattr(
            cls.multivalue_model(field_name),
            'default_%s' % field_name, lambda: None)()
    return default


class Configuration(
        ModelSingleton, ModelSQL, ModelView, CompanyMultiValueMixin):
    'Working Shift Configuration'
    __name__ = 'working_shift.configuration'
    working_shift_sequence = fields.MultiValue(working_shift_sequence)

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'working_shift_sequence':
            return pool.get('working_shift.configuration.sequence')
        return super(Configuration, cls).multivalue_model(field)

    default_working_shift_sequence = default_func('working_shift_sequence')


class ConfigurationSequence(ModelSQL, CompanyValueMixin):
    "Working Shift Configuration Sequence"
    __name__ = 'working_shift.configuration.sequence'
    working_shift_sequence = working_shift_sequence

    @classmethod
    def default_working_shift_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('working_shift', 'sequence_working_shift')
        except KeyError:
            return None
