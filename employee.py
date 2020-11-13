from trytond.pool import PoolMeta


class Employee(metaclass=PoolMeta):
    __name__ = 'company.employee'
    _order_name = 'party'
