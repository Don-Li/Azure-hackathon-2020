from flask import Flask, render_template, url_for, session, request, g
import sqlite3
import os
# from tornado.wsgi import WSGIContainer
# from tornado.httpserver import HTTPServer
# from tornado.ioloop import IOLoop
import processing
# TODO - uncomment on live server
# import rpy2.robjects as robjects
import json

# Define the application.
app = Flask(__name__)
app.debug = False

# Random secret key, so session cookies cannot be modified to gain access to other sessions even by the administrators.
app.secret_key = os.urandom(24)

# R setup.
# TODO - uncomment on live server.
# r = robjects.r

# App routing.
@app.route('/')
def index_page():
    return render_template('index.html', upload = True)

@app.route('/query', methods = ['GET'])
def query_page():
	# Check all parameters are filled in
	necessary = ['originLat', 'originLong', 'destinationLat', 'destinationLong', 'hour', 'weekday']
	for parameter in necessary:
		if not request.args.get(parameter):
			return "Missing inputs: <em>{}</em> not found.".format(parameter), 400

	lat1 = request.args.get('originLat')
	lng1 = request.args.get('originLong')
	lat2 = request.args.get('destinationLat')
	lng2 = request.args.get('destinationLong')
	hour = request.args.get('hour')
	weekday = request.args.get('weekday')

	# Validate data
	try:
		hour = int(hour)
		weekday = int(weekday)
	except:
		return "Invalid hour or weekday - should be numbers between 0-23 and 0-6.", 422
	if hour < 0 or hour > 23:
		return "Invalid hour: {}".format(hour), 422
	if weekday < 0 or weekday > 6:
		return "Invalid weekday: {}".format(weekday), 422

	# Make a prediction
	# Get the Azure Maps distance.
	# TODO (non-urgent) - use departAt parameter in Azure maps (which takes a date-time in the format 1996-12-19T16:39:57-08:00)
	azure_distance = processing.azure_distance(lat1, lng1, lat2, lng2)
	# Get OSRM distance.
	# TODO - Change local to True when we have a local version of OSRM running. Or leave as False for stability.
	osrm_distance = processing.osrm_distance(lat1, lng1, lat2, lng2, local=False)
	# Haversine / crow-flies distance
	crow_distance = processing.haversine_distance(lat1, lng1, lat2, lng2)

	# Whether it's a rush hour as a factor
	rush_hour = processing.get_rush_hour(hour)
	# Weekday as a factor
	f_weekday = processing.get_weekday(weekday)

	predicted_time = 0

	# TODO - Uncomment when we are connected to the model to make predictions.
	# The predict_time function may have to convert rush hour and weekday into a factor.
	# robjects.r("source('predict.R')")
	# robjects.r("predicted <- predict_time({}, {}, {}, {}, {}, '{}', '{}', {}, {}, {})".format(lat1, lng1, lat2, lng2, hour, f_weekday, rush_hour, azure_distance, osrm_distance, crow_distance))
	# We expect a matrix of predictions with 1 row - the first element should be the stacked prediction.
	# predicted_time = robjects.r("predicted[1,1]")

	# Return the predicted ETA
	return json.dumps({"eta": predicted_time})

if __name__ == "__main__":
	app.debug = False
	app.run(host = "0.0.0.0", port = 80, threaded = True)
	# This is for running as a standalone web application. You can also use nginx or other
	# load balancing things on Azure to deploy it.
	# http_server = HTTPServer(WSGIContainer(app))
	# http_server.listen(80)
	# IOLoop.instance().start()