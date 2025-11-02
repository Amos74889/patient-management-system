from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================
# MODELS
# ==========================
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(120))
    appointment = db.Column(db.String(200))
    billing = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Patient {self.name}>'

# ==========================
# ROUTES
# ==========================
@app.route('/')
def index():
    patients = Patient.query.all()
    return render_template('index.html', patients=patients)

@app.route('/add', methods=['POST'])
def add_patient():
    name = request.form['name']
    address = request.form['address']
    contact = request.form['contact']
    email = request.form['email']
    new_patient = Patient(name=name, address=address, contact=contact, email=email)
    db.session.add(new_patient)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    patient.name = request.form['name']
    patient.address = request.form['address']
    patient.contact = request.form['contact']
    patient.email = request.form['email']
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/appointment/<int:id>', methods=['POST'])
def add_appointment(id):
    patient = Patient.query.get_or_404(id)
    patient.appointment = request.form['appointment']
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/billing/<int:id>', methods=['POST'])
def update_billing(id):
    patient = Patient.query.get_or_404(id)
    patient.billing = float(request.form['billing'])
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
