#!/usr/bin/python2
import json
import logging
from os import listdir
from os.path import isfile, join
from subprocess import Popen
import sys
import shlex
#import plotly.plotly as py
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go

def filedata_to_dict(foldername):
	logging.debug("filedata_to_dict() instantiated")
	bin_data = {}
	exp_files = [f for f in listdir(foldername) if isfile(join(foldername, f)) and f.endswith(".perf")]
	exp_files.sort()

	for filename in exp_files:
		splitfilename = filename.split(".")
		binname = splitfilename[0]
		if binname not in bin_data:
			bin_data[binname] = {}
		#get file data
		bin_data[binname][filename] = getfiledata(join(foldername,filename), "seconds time elapsed")
	logging.debug("filedata_to_dict() completed")
	return bin_data

def getfiledata(filepath, keyphrase):
	logging.debug("getfiledata() instantiated")
	logging.debug("getfiledata(): looking in file: " + filepath)
	answer = {}
	found = 0

	try:
		with open(filepath) as f:
			#get the parameters we want
			for line in f:
				#logging.debug("getfiledata(): looking for string in line: " + line)
				#get time elapsed data
				if keyphrase in line:
					found = 1
					logging.debug("getfiledata(): string found: " + line.split()[0])
					answer['time'] = float(line.split()[0])
				#add more fields as needed here
		if found == 0:
			logging.error("String " + "seconds time elapsed" + " not found in file: " + filepath)
			exit() 
	except Exception as e:
		logging.error("Error when reading file: " + e)	

	return answer
	
def graph_gen_time(bin_data, stat_name, title):
	logging.debug("graph_gen_time() instantiated")
	data = []
	for binname, configs in bin_data.iteritems():

		time_vals = []
		for stat in configs.values():
			time_vals.append(stat[stat_name])

		#logging.debug("Adding a trace -- " + "name: " + binname + " x: " + str(configs.keys()) + " y: " + str(time_vals))
	
		trace=go.Bar(
				name=binname,
				x=configs.keys(),
				y=time_vals)
		data.append(trace)

	layout = go.Layout(
	title=title,
    barmode='group'
	)
	plot({"data": data, "layout": layout})

if __name__ == "__main__":
	logging.getLogger().setLevel(logging.DEBUG)
	logging.debug("Starting Program")
	if len(sys.argv) != 2:
		logging.error("Usage: graph_exp.py <perf-file-directory>")
		exit()
	foldername = sys.argv[1]
	bindata = filedata_to_dict(foldername)
	graph_gen_time(bindata, stat_name="time", title="Time Elapsed")
