from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import json
import random


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///fnafsmash.db'

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    elo = db.Column(db.Float, default=1500)

with app.app_context():
    db.create_all()

    # Load URLs from JSON file
    with open("urls.json", "r") as f:
        urls = json.load(f)

    for url in urls:
        if not LeaderboardEntry.query.filter_by(url=url).first():
            db.session.add(LeaderboardEntry(url=url))
    db.session.commit()

def update_elo(url1, url2, winner_url):
    K = 32
    entry1 = LeaderboardEntry.query.filter_by(url=url1).first()
    entry2 = LeaderboardEntry.query.filter_by(url=url2).first()

    expected1 = 1 / (1 + 10 ** ((entry2.elo - entry1.elo) / 400))
    expected2 = 1 / (1 + 10 ** ((entry1.elo - entry2.elo) / 400))
    
    if winner_url == url1:
        entry1.elo += K * (1 - expected1)
        entry2.elo += K * (0 - expected2)
    else:
        entry1.elo += K * (0 - expected1)
        entry2.elo += K * (1 - expected2)

    db.session.commit()

@app.route("/")
def home():
    url1, url2 = random.sample(urls, 2)
    return render_template("index.html", url1=url1, url2=url2)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/vote", methods=["POST"])
def vote():
    url1 = request.form.get("url1")
    url2 = request.form.get("url2")
    selected_url = request.form.get("selected_url")
    if selected_url:
        update_elo(url1, url2, selected_url)
    return redirect(url_for("home"))

@app.route("/leaderboard")
def show_leaderboard():
    return render_template("leaderboard.html")

@app.route("/leaderboard/load_more", methods=["POST"])
def load_more_leaderboard_entries():
    start = int(request.form.get("start"))
    limit = int(request.form.get("limit"))
    entries = (
        LeaderboardEntry.query.order_by(LeaderboardEntry.elo.desc())
        .offset(start)
        .limit(limit)
        .all()
    )
    entries_data = [
        {"url": entry.url, "elo": entry.elo, "id": entry.id} for entry in entries
    ]
    return json.dumps(entries_data)

if __name__ == "__main__":
    app.run(debug=True)
