from trytond.model import fields
from trytond.pool import PoolMeta


class Employee(metaclass=PoolMeta):
    __name__ = 'company.employee'
    _order_name = 'party'

    create_working_days = fields.Boolean('Create Working Days')

    @staticmethod
    def default_create_working_days():
        return True
