from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os

app = Flask(__name__)
db_user = os.getenv("DB_USER", "")
db_password = os.getenv("DB_PASSWORD", "")
db_host = os.getenv("DB_HOST", "")
db_name = os.getenv("DB_NAME", "")
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

PRICE_PER_BLOCK = 20
BLOCK_MINUTES = 15


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num_children = db.Column(db.Integer)
    blocks = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
    start_time = db.Column(db.DateTime(timezone=True), index=True)
    end_time = db.Column(db.DateTime(timezone=True), index=True)
    status = db.Column(db.String(20), default="active", index=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        num_children = int(request.form["num_children"])
        blocks = int(request.form["blocks"])

        total_amount = num_children * blocks * PRICE_PER_BLOCK

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=blocks * BLOCK_MINUTES)

        ride = Ride(
            num_children=num_children,
            blocks=blocks,
            total_amount=total_amount,
            start_time=start_time,
            end_time=end_time,
        )

        db.session.add(ride)
        db.session.commit()
        return redirect("/")

    now = datetime.now(timezone.utc)
    tz_mx = ZoneInfo("America/Mexico_City")

    rides_db = Ride.query.filter_by(status="active").order_by(Ride.end_time).all()
    rides = []

    for ride in rides_db:
        ride_start_utc = ride.start_time.replace(tzinfo=timezone.utc)
        ride_end_utc = ride.end_time.replace(tzinfo=timezone.utc)

        if now >= ride_end_utc:
            ride.status = "finished"
            continue

        remaining = int((ride_end_utc - now).total_seconds())

        # Convierte a hora local México (Guadalajara)
        start_local = ride_start_utc.astimezone(tz_mx)
        end_local = ride_end_utc.astimezone(tz_mx)

        rides.append(
            {
                "id": ride.id,
                "num_children": ride.num_children,
                "total_amount": ride.total_amount,
                "start_time": start_local,
                "end_time": end_local,
                "remaining": remaining,
            }
        )

    db.session.commit()

    return render_template("index.html", rides=rides)


@app.route("/inactive", methods=["GET"])
def inactive():
    tz_mx = ZoneInfo("America/Mexico_City")
    
    # Get date filter from query parameters
    date_filter = request.args.get('date')
    
    query = Ride.query.filter(Ride.status != "active")
    
    if date_filter:
        try:
            # Parse date (assuming YYYY-MM-DD format)
            # filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            start = datetime.strptime(date_filter, "%Y-%m-%d")
            end = start + timedelta(days=1)            

            query = query.filter(
                Ride.start_time >= start,
                Ride.start_time < end
            )            
        except ValueError:
            pass  # Invalid date, ignore filter
    
    rides_db = query.all()
    rides = []
    
    for ride in rides_db:
        ride_start_utc = ride.start_time.replace(tzinfo=timezone.utc)
        ride_end_utc = ride.end_time.replace(tzinfo=timezone.utc)
        
        # Convert to local time (Mexico City)
        start_local = ride_start_utc.astimezone(tz_mx)
        end_local = ride_end_utc.astimezone(tz_mx)
        
        rides.append(
            {
                "id": ride.id,
                "num_children": ride.num_children,
                "blocks": ride.blocks,
                "total_amount": ride.total_amount,
                "start_time": start_local,
                "end_time": end_local,
                "status": ride.status,
            }
        )
    
    return render_template("inactive.html", rides=rides, date_filter=date_filter)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
