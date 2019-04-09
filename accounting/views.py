# You will probably need more methods from flask but this one is a good start.
from flask import render_template, request
from flask_cors import CORS
import json

# Import things from Flask that we need.
from accounting import app, db

# Import our models
from models import Contact, Invoice, Policy, policy_schema, invoices_schema

from utils import validate_headers

CORS(app)

# Routing for the server.
@app.route("/")
def index():
    # You will need to serve something up here.
    return render_template('index.html')

@app.route("/policy/<policy_id>")
def policy(policy_id):
    policy = Policy.query.get(policy_id)
    return policy_schema.jsonify(policy)

@app.route("/invoice")
@validate_headers(request, ["policyId", "invoiceDate"])
def invoices():
    q = Invoice.query

    policy_id = request.args.get('policyId')
    invoice_date = request.args.get('invoiceDate')

    return invoices_schema.jsonify(Invoice.query.filter(Invoice.due_date==invoice_date).filter(Invoice.policy_id==policy_id).all())
