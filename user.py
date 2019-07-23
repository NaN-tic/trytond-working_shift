# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.config import config as config_

__all__ = ['User']

LOGIN = config_.getboolean('working_shift', 'login', default=True)


class User(metaclass=PoolMeta):
    __name__ = "res.user"

    @classmethod
    def get_preferences(cls, context_only=False):
        ModelData = Pool().get('ir.model.data')

        preferences = super(User, cls).get_preferences(context_only)
        if LOGIN:
            actions = preferences.get('actions', [])
            actions.insert(0,ModelData.get_id('working_shift',
                    'wizard_employee_working_shift_start'))
            preferences['actions'] = actions
        return preferences.copy()
