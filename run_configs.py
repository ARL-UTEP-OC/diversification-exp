#!/usr/bin/python2
import json
import logging
from os import listdir
from os.path import isfile, join
from subprocess import Popen
import sys
import shlex

def run_configs(foldername):
	logging.debug("run_configs() instantiated")
	exp_files = [f for f in listdir(foldername) if isfile(join(foldername, f))]

	for filename in exp_files:
		runCmd = "./Amoeba_Exp.sh " + join(foldername,filename)
		
		logging.debug("run_configs(): running command " + runCmd)
		process = Popen(shlex.split(runCmd))
		process.wait()
		logging.debug("run_configs(): complete " + runCmd)

if __name__ == "__main__":
	logging.getLogger().setLevel(logging.DEBUG)
	logging.debug("Starting Program")
	if len(sys.argv) != 2:
		logging.error("Usage: run_configs.py <config-directory>")
		exit()
	foldername = sys.argv[1]
	run_configs(foldername)
