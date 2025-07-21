from flask import Flask, jsonify
import json

app = Flask(__name__) # this line initializes the Flask application
@app.route("/tagged_messages.json")
def get_tagged_messages():
    with open("shared_folder/tagged_messages.json", "r") as tagged_file:
        data = json.load(tagged_file)
    return jsonify(data)

@app.route("/location_cache.json")
def get_location_cache():
    with open("shared_folder/location_cache.json", "r") as location_file:
        data = json.load(location_file)
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)