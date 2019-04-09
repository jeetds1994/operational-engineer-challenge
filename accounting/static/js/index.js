
function HomeViewModel() {
  this.invoices = ko.observableArray([]);
  this.policy = ko.observableArray([]);
  this.invoice_date = ko.observable().extend({ date: true });
  this.policy_number = ko.observable().extend({ number: true });
  this.onSubmit = function() {
    this.policy.removeAll()
    this.invoices.removeAll()
    loadPolicyTable(this.policy_number(), this.policy)
    loadInvoiceTable(this.policy_number(), this.invoice_date(), this.invoices)
  }
}

var BACKEND_API_ENDPOINT = "http://localhost:5000"

function loadPolicyTable(policyNumber, policy) {
    fetch(BACKEND_API_ENDPOINT + `/policy/${policyNumber}`).then(resp => resp.json()).then((data) => {
            const {
              id,
              agent,
              annual_premium,
              billing_schedule,
              cancelation_date,
              effective_date,
              named_insured,
              policy_cancelation_description,
              policy_number,
              status
            } = data

            policy.push(
              {
                policy_number: policy_number,
                effective_date: effective_date,
                status: status,
                billing_schedule: billing_schedule,
                annual_premium: annual_premium,
                named_insured: named_insured,
                policy_cancelation_description: policy_cancelation_description,
                cancelation_date: cancelation_date
              }
            );
        })
}

function loadInvoiceTable(policyId, invoiceDate, invoices) {
    fetch(BACKEND_API_ENDPOINT + `/invoice?policyId=${policyId}&invoiceDate=${invoiceDate}`).then(resp => resp.json()).then(data => {
      data.forEach(invoice => {
        const {
          id,
          amount_due,
          bill_date,
          cancel_date,
          deleted,
          due_date,
          policy_id
        } = invoice

        invoices.push(
          {
            amount_due: amount_due,
            bill_date: bill_date,
            cancel_date: cancel_date,
            deleted: Boolean(deleted),
            due_date: due_date,
            policy_id: policy_id
          }
        )
    })
  })
}
ko.applyBindings(new HomeViewModel());
