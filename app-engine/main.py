from flask import Flask, render_template, request
from devices import updateDevice, pullSub

app = Flask(__name__)

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html')

@app.route("/ledMatrix", methods = ['POST'])
def updateLedMatrix():
    colour = request.get_data().decode("utf-8")
    updateDevice("led-matrix", "ON {}".format(colour))
    return "Success"