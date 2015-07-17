# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import Model, ModelSQL, ModelView, ModelSingleton, fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all_ = ['WorkingShiftConfiguration', 'WorkingShiftConfigurationCompany']
__metaclass__ = PoolMeta


class WorkingShiftConfiguration(ModelSingleton, ModelSQL, ModelView):
    'Working Shift Configuration'
    __name__ = 'working_shift.configuration'
    intervention_sequence = fields.Function(fields.Many2One('ir.sequence',
            'Intervention Sequence',
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'working_shift.intervention'),
                ]),
        'get_company_config', 'set_company_config')
    working_shift_sequence = fields.Function(fields.Many2One('ir.sequence',
            'Working Shift Sequence',
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'working_shift'),
                ]),
        'get_company_config', 'set_company_config')

    @classmethod
    def get_company_config(cls, configs, names):
        pool = Pool()
        CompanyConfig = pool.get('working_shift.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])

        res = {}
        for fname in names:
            res[fname] = {
                configs[0].id: None,
                }
            if company_configs:
                val = getattr(company_configs[0], fname)
                if isinstance(val, Model):
                    val = val.id
                res[fname][configs[0].id] = val
        return res

    @classmethod
    def set_company_config(cls, configs, name, value):
        pool = Pool()
        CompanyConfig = pool.get('working_shift.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])
        if company_configs:
            company_config = company_configs[0]
        else:
            company_config = CompanyConfig(company=company_id)
        setattr(company_config, name, value)
        company_config.save()


class WorkingShiftConfigurationCompany(ModelSQL):
    'Working Shift Configuration per Company'
    __name__ = 'working_shift.configuration.company'
    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE', select=True)
    intervention_sequence = fields.Many2One('ir.sequence',
        'Intervention Sequence',
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'working_shift.intervention'),
            ])
    working_shift_sequence = fields.Many2One('ir.sequence',
        'Working Shift Sequence',
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('code', '=', 'working_shift'),
            ])
