import unittest

from dateutil.relativedelta import relativedelta
from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules, set_user


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Activate working_shift
        activate_modules('working_shift')

        # Create company
        _ = create_company()
        company = get_company()
        party = company.party

        # Create Employee
        Party = Model.get('party.party')
        Employee = Model.get('company.employee')
        User = Model.get('res.user')
        party = Party(name='Employee')
        party.save()
        employee = Employee()
        employee.party = party
        employee.company = company
        employee.save()
        user, = User.find([])
        user.employees.append(employee)
        user.employee = employee
        user.save()
        set_user(user)

        # Configure sequences
        WorkingShiftConfig = Model.get('working_shift.configuration')
        Sequence = Model.get('ir.sequence')
        working_shift_config = WorkingShiftConfig(1)
        working_shift_sequence, = Sequence.find([('name', '=', 'Working Shift')
                                                 ])
        working_shift_config.working_shift_sequence = working_shift_sequence
        working_shift_config.save()

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create working shift
        Shift = Model.get('working_shift')
        shift = Shift()
        self.assertEqual(shift.employee, employee)
        shift.end = shift.start + relativedelta(days=1)
        shift.save()
        shift.click('confirm')
