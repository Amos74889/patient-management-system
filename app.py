import os
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify
)
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import stripe

load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/pms")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-for-prod")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client.get_default_database() if client.get_default_database() else client["pms"]
stripe.api_key = STRIPE_SECRET_KEY

def oid(id_str):
    try:
        return ObjectId(id_str)
    except Exception:
        return None

def serialize_doc(doc):
    if not doc:
        return None
    d = dict(doc)
    d["_id"] = str(d["_id"])
    return d

@app.route("/")
def index():
    patients_count = db.patients.count_documents({})
    appts_count = db.appointments.count_documents({})
    invoices_count = db.invoices.count_documents({})
    return render_template("index.html",
                           patients_count=patients_count,
                           appts_count=appts_count,
                           invoices_count=invoices_count)

# Patients
@app.route("/patients")
def patients_list():
    patients = list(db.patients.find().sort("created_at", -1))
    return render_template("patients.html", patients=patients)

@app.route("/patients/new", methods=["GET", "POST"])
def patient_new():
    if request.method == "POST":
        data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "address": request.form.get("address", "").strip(),
            "contact": request.form.get("contact", "").strip(),
            "email": request.form.get("email", "").strip(),
            "created_at": datetime.utcnow()
        }
        db.patients.insert_one(data)
        flash("Patient added.", "success")
        return redirect(url_for("patients_list"))
    return render_template("patient_form.html", patient=None)

@app.route("/patients/<id>/edit", methods=["GET", "POST"])
def patient_edit(id):
    _id = oid(id)
    p = db.patients.find_one({"_id": _id})
    if not p:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients_list"))
    if request.method == "POST":
        update = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "address": request.form.get("address", "").strip(),
            "contact": request.form.get("contact", "").strip(),
            "email": request.form.get("email", "").strip(),
        }
        db.patients.update_one({"_id": _id}, {"$set": update})
        flash("Patient updated.", "success")
        return redirect(url_for("patients_list"))
    return render_template("patient_form.html", patient=serialize_doc(p))

@app.route("/patients/<id>/delete", methods=["POST"])
def patient_delete(id):
    _id = oid(id)
    db.patients.delete_one({"_id": _id})
    flash("Patient deleted.", "warning")
    return redirect(url_for("patients_list"))

# Appointments
@app.route("/appointments")
def appointments_list():
    appts = list(db.appointments.find().sort("start_time", -1))
    for a in appts:
        p = db.patients.find_one({"_id": oid(a.get("patient_id"))})
        a["patient_name"] = f"{p.get('first_name','')} {p.get('last_name','')}" if p else "Unknown"
        if isinstance(a.get("start_time"), datetime):
            a["start_time"] = a["start_time"].isoformat()
        if isinstance(a.get("end_time"), datetime):
            a["end_time"] = a["end_time"].isoformat()
        a["_id"] = str(a["_id"])
    patients = list(db.patients.find().sort("first_name", 1))
    return render_template("appointments.html", appts=appts, patients=patients)

@app.route("/appointments/new", methods=["GET", "POST"])
def appointment_new():
    patients = list(db.patients.find().sort("first_name", 1))
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        notes = request.form.get("notes", "")
        appt = {
            "patient_id": patient_id,
            "start_time": start_time,
            "end_time": end_time,
            "notes": notes,
            "status": "booked",
            "created_at": datetime.utcnow()
        }
        db.appointments.insert_one(appt)
        flash("Appointment created.", "success")
        return redirect(url_for("appointments_list"))
    return render_template("appointment_form.html", patients=patients)

@app.route("/appointments/<id>/delete", methods=["POST"])
def appointment_delete(id):
    db.appointments.delete_one({"_id": oid(id)})
    flash("Appointment removed.", "warning")
    return redirect(url_for("appointments_list"))

# Invoices & Billing
@app.route("/invoices")
def invoices_list():
    invoices = list(db.invoices.find().sort("created_at", -1))
    for inv in invoices:
        inv["_id"] = str(inv["_id"])
    return render_template("invoices.html", invoices=invoices)

@app.route("/invoices/new/<appointment_id>", methods=["GET", "POST"])
def invoice_new(appointment_id):
    appt = db.appointments.find_one({"_id": oid(appointment_id)})
    if not appt:
        flash("Appointment not found.", "danger")
        return redirect(url_for("appointments_list"))
    patient = db.patients.find_one({"_id": oid(appt["patient_id"])})
    if request.method == "POST":
        description = request.form.get("description", "Consultation")
        qty = int(request.form.get("qty", "1"))
        unit_price = float(request.form.get("unit_price", "0"))
        total = qty * unit_price
        invoice = {
            "appointment_id": appointment_id,
            "patient_id": appt["patient_id"],
            "items": [{"description": description, "qty": qty, "unit_price": unit_price}],
            "total": total,
            "status": "unpaid",
            "created_at": datetime.utcnow()
        }
        res = db.invoices.insert_one(invoice)
        invoice_id = str(res.inserted_id)
        flash("Invoice created. Proceed to payment.", "success")
        return redirect(url_for("invoice_pay", invoice_id=invoice_id))
    return render_template("invoice.html", appointment=serialize_doc(appt), patient=serialize_doc(patient))

@app.route("/invoices/<invoice_id>/pay", methods=["GET"])
def invoice_pay(invoice_id):
    inv = db.invoices.find_one({"_id": oid(invoice_id)})
    if not inv:
        flash("Invoice not found.", "danger")
        return redirect(url_for("index"))
    domain = os.getenv("BASE_URL", request.url_root.rstrip("/"))
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": inv["items"][0]["description"] if inv["items"] else "Invoice"},
                    "unit_amount": int(inv["total"] * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{domain}/invoices/{invoice_id}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain}/invoices/{invoice_id}/cancel",
            metadata={"invoice_id": invoice_id},
        )
    except Exception as e:
        flash("Stripe error: " + str(e), "danger")
        return redirect(url_for("invoices_list"))
    return redirect(checkout_session.url, code=303)

@app.route("/invoices/<invoice_id>/success")
def invoice_success(invoice_id):
    inv = db.invoices.find_one({"_id": oid(invoice_id)})
    return render_template("invoice_paid.html", invoice=serialize_doc(inv))

@app.route("/invoices/<invoice_id>/cancel")
def invoice_cancel(invoice_id):
    flash("Payment cancelled.", "warning")
    return redirect(url_for("index"))

@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    event = None
    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            print("Webhook signature verification failed:", e)
            return jsonify({"msg": "invalid signature"}), 400
    else:
        try:
            event = stripe.Event.construct_from(request.get_json(force=True), stripe.api_key)
        except Exception as e:
            return jsonify({"msg":"invalid webhook"}), 400

    if event and event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        inv_id = session.get("metadata", {}).get("invoice_id")
        if inv_id:
            db.invoices.update_one({"_id": oid(inv_id)}, {"$set": {"status": "paid", "paid_at": datetime.utcnow(), "stripe_session": session}})
    return "", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
