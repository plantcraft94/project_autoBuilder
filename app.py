from flask import Flask, render_template, request
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pixeldrain

# Fetch the service account key JSON file contents
cred = credentials.Certificate(".data/firebase-adminsdk.json")
# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://autobuilder-project-default-rtdb.asia-southeast1.firebasedatabase.app/"
    },
)


def upload_totkab_to_pixeldrain(totkab_file):
    upload_details = pixeldrain.upload_file(totkab_file)
    return "https://pixeldrain.com/u/" + upload_details["id"]


def upload_to_db(name, image_link, download_link, description):
    ref = db.reference("/")
    ref.push(
        {
            "Name": name,
            "Image": image_link,
            "Download": download_link,
            "Description": description,
        }
    )


app = Flask(__name__)

app.url_map.strict_slashes = False


@app.route("/")
def index():
    Name = []
    Image = []
    routes = []
    ref = db.reference("/")
    ddata = ref.get()
    if ddata is not None:
        for i in ref.get():
            refs = db.reference(i)
            Name.append(refs.get()["Name"])
            Image.append(refs.get()["Image"])
            routes.append(i)
        data = [
            {"id": id, "image": image, "route": route}
            for id, image, route in zip(Name, Image, routes)
        ]
        return render_template("index.html", data=data)
    return render_template("index.html")


@app.route("/guide")
def faq():
    return render_template("faq.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        totkab_file = request.files["totkabFile"]
        uname = request.form["name"]
        uImage = request.form["imageUrl"]
        uDisc = request.form["description"]
        print(uname, uImage, uDisc)

        if totkab_file and totkab_file.filename.endswith(".cai"):
            # Save the file locally
            totkab_file.save(totkab_file.filename)

            # Upload the file to GoFile
            gofile_url = upload_totkab_to_pixeldrain(totkab_file.filename)
            # Delete the local file
            os.remove(totkab_file.filename)

            if gofile_url:
                # File uploaded successfully, redirect to the download page
                upload_to_db(uname, uImage, gofile_url, uDisc)
                return f"File uploaded successfully. Return to <a href='https://autobuildshare.glitch.me/'>Home page</a>."
            else:
                # Error uploading file to GoFile
                return f"Error uploading file: {gofile_url}"
        else:
            return "Invalid file format. Only .totkab files are allowed."

    return render_template("upload.html")


@app.route("/<route>")
def detail(route):
    ref = db.reference(route)
    data = ref.get()

    if data is not None:
        dName = data.get("Name")
        dImage = data.get("Image")
        dDownload = data.get("Download")
        dDesc = data.get("Description")

        return render_template(
            "detail.html", dName=dName, dImage=dImage, dDownload=dDownload, dDesc=dDesc
        )

    return "404"


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get("query")
        results = perform_search(query)
        Name = []
        Image = []
        routes = []
        for i in results:
            refs = db.reference(i)
            Name.append(refs.get()["Name"])
            Image.append(refs.get()["Image"])
            routes.append(i)
        data = [
            {"id": id, "image": image, "route": route}
            for id, image, route in zip(Name, Image, routes)
        ]
        return render_template("search_results.html", data=data)
    else:
        return render_template("search_form.html")


def perform_search(query):
    # Get a reference to the database
    ref = db.reference("/")

    # Perform the search
    results = []
    data = ref.get()
    for key, value in data.items():
        if query in str(value):
            results.append(key)

    return results


if __name__ == "__main__":
    app.run()
