from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import json
import random
from flask import make_response
from flask import make_response, send_from_directory
from datetime import timedelta


uri = os.getenv("DATABASE_URL")  # or other relevant config var
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
# rest of connection code using the connection string `uri`


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = uri or "sqlite:///fnafsmash.db"
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

    for url_data in urls:
        thumbnail_url = url_data.split('B2B--B2B')[0]
        if not LeaderboardEntry.query.filter_by(url=thumbnail_url).first():
            db.session.add(LeaderboardEntry(url=thumbnail_url))
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
    url1_data, url2_data = random.sample(urls, 2)
    url1_parts = url1_data.split("B2B--B2B")
    url2_parts = url2_data.split("B2B--B2B")

    url1 = url1_parts[0]
    title1 = url1_parts[1]
    game_link1 = url1_parts[2]
    url2 = url2_parts[0]
    title2 = url2_parts[1]
    game_link2 = url2_parts[2]

    return render_template("index.html", url1=url1, url2=url2, title1=title1, title2=title2, game_link1=game_link1, game_link2=game_link2)


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

@app.route('/static/twocent.png')
def serve_twocent_image():
    with open('static/twocent.png', 'rb') as img:
        img_data = img.read()

    response = make_response(img_data)
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Cache-Control', 'public, max-age={}'.format(int(timedelta(days=30).total_seconds())))
    return response



@app.route("/leaderboard/load_more", methods=["POST"])
def load_more_leaderboard_entries():
    start = int(request.form.get("start"))
    limit = int(request.form.get("limit"))
    entries = (
        LeaderboardEntry.query.order_by(LeaderboardEntry.elo.desc(), LeaderboardEntry.id.asc())
        .offset(start)
        .limit(limit)
        .all()
    )
    entries_data = [
        {"url": entry.url, "elo": entry.elo, "id": entry.id, "title": get_title_from_url(entry.url), "game_url": get_game_url_from_url(entry.url)} for entry in entries
    ]
    return json.dumps(entries_data)

def get_title_from_url(url):
    for url_data in urls:
        thumbnail_url, title, _ = url_data.split('B2B--B2B')
        if thumbnail_url == url:
            return title
    return None

def get_game_url_from_url(url):
    for url_data in urls:
        thumbnail_url, title, game_url = url_data.split('B2B--B2B', 2)
        if thumbnail_url == url:
            return game_url
    return None




if __name__ == "__main__":
    app.run(debug=True)
