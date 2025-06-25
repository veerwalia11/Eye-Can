from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import random
from sqlalchemy import Text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eyescreening.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class EyeScreening(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(80), nullable=False)
    vision_score = db.Column(db.String(20), nullable=False)
    school = db.Column(db.String(80), nullable=False)
    matched_optotypes = db.Column(db.Text, nullable=False)
    calculated_acuity = db.Column(db.String(20), nullable=False)
    estimated_prescription = db.Column(db.String(20), nullable=False)

class PolicyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_name = db.Column(db.String(80), nullable=False)
    organization = db.Column(db.String(80), nullable=False)
    request_description = db.Column(db.Text, nullable=False)

SNELLEN_LINES = [200, 100, 70, 50, 40, 30, 25, 20, 15, 10]

def estimate_prescription(num_correct, total_optotypes, screen_distance_inches):
    """Estimates the prescription in diopters based on the number of correct optotypes."""
    if num_correct == 0:
        return None
    line_index = min(num_correct - 1, len(SNELLEN_LINES) - 1)
    snellen_denominator = SNELLEN_LINES[line_index]
    distance_m = screen_distance_inches * 0.0254
    standard_distance_m = 6.096
    try:
        diopters = (1 / distance_m) - (1 / (standard_distance_m * snellen_denominator / 20))
    except ZeroDivisionError:
        diopters = 0
    return round(diopters * 4) / 4.0

@app.route("/submit_screening", methods=["POST"])
def submit_screening():
    data = request.json
    required_fields = ["student_name", "vision_score", "school", "matched_optotypes", "calculated_acuity", "estimated_prescription"]

    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    screening = EyeScreening(
        student_name=data["student_name"],
        vision_score=data["vision_score"],
        school=data["school"],
        matched_optotypes=data["matched_optotypes"],
        calculated_acuity=data["calculated_acuity"],
        estimated_prescription=data["estimated_prescription"]
    )
    db.session.add(screening)
    db.session.commit()
    return jsonify({"status": "success", "id": screening.id}), 201

@app.route("/optotype_test", methods=["GET"])
def optotype_test():
    optotypes = ["E", "F", "P", "T", "O", "Z", "L"]
    selected = random.sample(optotypes, 5)
    return jsonify({"optotypes": selected}), 200

@app.route("/evaluate_vision", methods=["POST"])
def evaluate_vision():
    data = request.json
    matched = data.get("matched_optotypes", [])
    screen_distance_inches = float(data.get("screen_distance_inches", 16))
    num_correct = len(matched)
    total_optotypes = 5
    estimated_prescription = estimate_prescription(num_correct, total_optotypes, screen_distance_inches)

    result = "Unable to estimate prescription. Please try again." if estimated_prescription is None else f"Estimated prescription: {estimated_prescription:+.2f} D"

    return jsonify({
        "calculated_acuity": num_correct / total_optotypes,
        "estimated_prescription": estimated_prescription,
        "vision_quality": result
    }), 200

@app.route("/submit_policy_request", methods=["POST"])
def submit_policy_request():
    data = request.json
    required_fields = ["requester_name", "organization", "request_description"]

    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    policy_req = PolicyRequest(
        requester_name=data["requester_name"],
        organization=data["organization"],
        request_description=data["request_description"]
    )
    db.session.add(policy_req)
    db.session.commit()
    return jsonify({"status": "success", "id": policy_req.id}), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=True)