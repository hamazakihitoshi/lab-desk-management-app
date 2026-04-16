from seed.dummy_data import dummy_data
from database import insert_dummy_data

insert_dummy_data(dummy_data)

from flask import Flask, render_template, request, redirect
from database import init_db
from services.desk_service import (
    get_dashboard_data,
    start_using_desk,
    release_desk,
)

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    data = get_dashboard_data()
    return render_template(
        "index.html",
        desks=data["desks"],
        history=data["history"],
        analysis=data["analysis"],
        summary=data["summary"]
    )


@app.route("/use", methods=["POST"])
def use():
    name = request.form["name"]
    desk_id = int(request.form["desk"])
    start_using_desk(name, desk_id)
    return redirect("/")


@app.route("/release", methods=["POST"])
def release():
    desk_id = int(request.form["desk"])
    release_desk(desk_id)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)