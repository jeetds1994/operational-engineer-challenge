#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from functools import wraps

from accounting import db
from flask import jsonify
from models import Contact, Invoice, Payment, Policy

"""
#######################################################
This is the base code for the engineer project.
#######################################################
"""

class PolicyAccounting(object):
    """
        Each policy has its own instance of accounting.
    """
    def __init__(self, policy_id):
        self.policy = Policy.query.filter_by(id=policy_id).one()

        if not self.policy.invoices:
            self.make_invoices()

    def change_billing(self, new_billing_schedule):
        self.policy.billing_schedule = new_billing_schedule

        for invoice in self.policy.invoices:
            invoice.deleted = 1

        db.session.commit()

        make_invoices(delete_existing_invoices=False)

    """
        Calculates the account balance at a given date by checking for over invoices and payments.
        @Returns an integar represting balance.
    """
    def return_account_balance(self, date_cursor=None):
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()
        due_now = 0
        for invoice in invoices:
            due_now += invoice.amount_due

        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()
        for payment in payments:
            due_now -= payment.amount_paid

        return due_now

    """
        Retreive invoices between a range of dates. (Note: We retreive the latest if end date is not specified.)
        @Returns list of Invoice
    """
    def get_invoices_by_date(self, start_date, end_date=datetime.now().date()):
        return Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date >= start_date)\
                                .filter(Invoice.bill_date <= end_date)\
                                .order_by(Invoice.bill_date)\
                                .all()
    """
        Make payments at a date with a contact_id.
        @Retuns instance of Payment created.
    """
    def make_payment(self, contact_id=None, date_cursor=None, amount=0):
        if not date_cursor:
            date_cursor = datetime.now().date()

        if not contact_id:
            try:
                contact_id = self.policy.named_insured
            except:
                pass

        payment = Payment(self.policy.id,
                          contact_id,
                          amount,
                          date_cursor)
        db.session.add(payment)
        db.session.commit()

        return payment

    """

         If this function returns true, an invoice
         on a policy has passed the due date without
         being paid in full. However, it has not necessarily
         made it to the cancel_date yet.
    """
    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=datetime.now().date()):
        invoice = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.due_date <= date_cursor)\
                                .filter(Invoice.cancel_date >= date_cursor)\
                                .first()
        return bool(invoice)

    def cancel_policy(self, cancelation_date=datetime.now().date(), cancel_description=""):
        if self.evaluate_cancel():
            self.policy.status = "Canceled"
            self.policy.cancelation_date = cancelation_date
            self.policy.cancel_description = cancel_description
            db.session.commit()
            print("Policy canceled")
            return True
        else:
            print("Policy can't be canceled due to balance.")
        return False


    """
        Determine if Policy still have outstanding balance.
    """
    def evaluate_cancel(self, date_cursor=None):
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()
        can_cancel = False
        for invoice in invoices:
            if not self.return_account_balance(invoice.cancel_date):
                continue
            else:
                can_cancel = True
                print "THIS POLICY SHOULD HAVE CANCELED"
                break
        else:
            print "THIS POLICY SHOULD NOT CANCEL"

        return can_cancel

    """
        Generates invoices for policy based on billing schedules.
    """
    def make_invoices(self, delete_existing_invoices=True):
        if delete_existing_invoices:
            for invoice in self.policy.invoices:
                invoice.delete()

        billing_schedules = {'Annual': None, 'Semi-Annual': 3, 'Quarterly': 4, 'Monthly': 12}

        invoices = []
        first_invoice = Invoice(self.policy.id,
                                self.policy.effective_date, #bill_date
                                self.policy.effective_date + relativedelta(months=1), #due
                                self.policy.effective_date + relativedelta(months=1, days=14), #cancel
                                self.policy.annual_premium)
        invoices.append(first_invoice)

        if self.policy.billing_schedule == "Annual":
            pass
        elif self.policy.billing_schedule == "Two-Pay":
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i*6
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
                invoices.append(invoice)
        elif self.policy.billing_schedule == "Quarterly":
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i*3
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
                invoices.append(invoice)
        elif self.policy.billing_schedule == "Monthly":
            pass
        else:
            print "You have chosen a bad billing schedule."

        for invoice in invoices:
            db.session.add(invoice)
        db.session.commit()

################################
# The functions below are for the db and
# shouldn't need to be edited.
################################
def build_or_refresh_db():
    db.drop_all()
    db.create_all()
    insert_data()
    print "DB Ready!"

def insert_data():
    #Contacts
    contacts = []
    john_doe_agent = Contact('John Doe', 'Agent')
    contacts.append(john_doe_agent)
    john_doe_insured = Contact('John Doe', 'Named Insured')
    contacts.append(john_doe_insured)
    bob_smith = Contact('Bob Smith', 'Agent')
    contacts.append(bob_smith)
    anna_white = Contact('Anna White', 'Named Insured')
    contacts.append(anna_white)
    joe_lee = Contact('Joe Lee', 'Agent')
    contacts.append(joe_lee)
    ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
    contacts.append(ryan_bucket)

    for contact in contacts:
        db.session.add(contact)
    db.session.commit()

    policies = []
    p1 = Policy('Policy One', date(2015, 1, 1), 365)
    p1.billing_schedule = 'Annual'
    p1.agent = bob_smith.id
    policies.append(p1)

    p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
    p2.billing_schedule = 'Quarterly'
    p2.named_insured = anna_white.id
    p2.agent = joe_lee.id
    policies.append(p2)

    p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
    p3.billing_schedule = 'Monthly'
    p3.named_insured = ryan_bucket.id
    p3.agent = john_doe_agent.id
    policies.append(p3)

    for policy in policies:
        db.session.add(policy)
    db.session.commit()

    for policy in policies:
        PolicyAccounting(policy.id)

    payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
    db.session.add(payment_for_p2)
    db.session.commit()

def validate_headers(request, expected_headers):
    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            for header in expected_headers:
                #I am aware this does not validate the field type or content
                if header not in request.args or len(request.args.get(header)) is 0:
                    return jsonify(msg='Bad request'), 403
            return func(*args, **kwargs)
        return decorated_function
    return wrapper
