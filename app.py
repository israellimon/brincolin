from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

PRICE_PER_BLOCK = 20
BLOCK_MINUTES = 15


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num_children = db.Column(db.Integer)
    blocks = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="active")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        num_children = int(request.form["num_children"])
        blocks = int(request.form["blocks"])

        total_amount = num_children * blocks * PRICE_PER_BLOCK

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=blocks * BLOCK_MINUTES)

        ride = Ride(
            num_children=num_children,
            blocks=blocks,
            total_amount=total_amount,
            start_time=start_time,
            end_time=end_time
        )

        db.session.add(ride)
        db.session.commit()
        return redirect("/")

    now = datetime.now()
    active_rides = Ride.query.filter_by(status="active").all()

    for ride in active_rides:
        if now >= ride.end_time:
            ride.status = "finished"
    db.session.commit()

    active_rides = Ride.query.filter_by(status="active").order_by(Ride.end_time).all()

    return render_template("index.html", rides=active_rides)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) # For render