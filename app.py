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

        start_time = datetime.utcnow()
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

    now = datetime.utcnow()

    rides_db = Ride.query.filter_by(status="active").order_by(Ride.end_time).all()

    rides = []

    for ride in rides_db:

        if now >= ride.end_time:
            ride.status = "finished"
            continue

        remaining = int((ride.end_time - now).total_seconds())

        rides.append({
            "id": ride.id,
            "num_children": ride.num_children,
            "total_amount": ride.total_amount,
            "start_time": ride.start_time,
            "end_time": ride.end_time,
            "remaining": remaining
        })

    db.session.commit()

    return render_template("index.html", rides=rides)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))