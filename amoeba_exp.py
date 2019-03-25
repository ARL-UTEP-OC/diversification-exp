#!/usr/bin/python2
import json
import logging
import os
import shutil
import shlex
import sys
from jinja2 import Environment, FileSystemLoader
from subprocess import Popen

def readExperimentFile(filename):
	logging.debug("readExperimentFile() instantiated")
	with open(filename) as json_input:
		experiment = json.load(json_input)
		logging.info("Reading JSON file")
		
		logging.debug("readExperimentFile(): Reading global parameters")
		g = experiment['global'][0]
		logging.debug("experiment-name: " + g['experiment-name'])
		logging.debug("amoeba-path: " + g['amoeba-path'])
		logging.debug("amoeba-bin-outpath: " + g['amoeba-bin-outpath'])
		logging.debug("amoeba-iterations: " + g['amoeba-iterations'])
		logging.debug("amoeba-algs: " + str(g['amoeba-algs']))			
		logging.debug("amoeba-template-path: " + g['amoeba-template-path'])	
		logging.debug("perf-events: " + g['perf-events'])
		logging.debug("perf-out-path: " + g['perf-out-path'])	

		#change working directory to Amoeba
		os.chdir(g['amoeba-path'])

		#embed the diversification algorithm choice
		alg=g['experiment-name']
		#generate the ail.ml file
		genAlgs(g['amoeba-algs'], g['amoeba-template-path'], "ail.ml")
		#recompile amoeba
		compileAmoeba()
		
		for p in experiment['config']:
			logging.debug("Entry: " + str(p))
			logging.debug("bin-name: " + p['bin-name'])
			logging.debug("bin-arguments: " + p['bin-arguments'])
			
			binpath, binfilename = os.path.split(p['bin-name'])
			#create outfilename and run analysis on original
			outfilename = os.path.join(g['perf-out-path'],binfilename+".perf")
			logging.info("Running performance analysis on: " + p['bin-name'])
			runPerfAnalyze(p['bin-name'], p['bin-arguments'], g['perf-events'], outfilename)
		
				#create outfilename and diversify
			doutfilename = os.path.join(g['amoeba-bin-outpath'],binfilename+"."+g['amoeba-iterations']+"."+str(alg)+".diversified")
			runAmoeba(p['bin-name'], g['amoeba-algs'], g['amoeba-iterations'], doutfilename)
				#create outfilename and run analysis on diversified
			outfilename = os.path.join(g['perf-out-path'],binfilename+"."+g['amoeba-iterations']+"."+str(alg)+".diversified.perf")
			logging.info("Running performance analysis on: " + doutfilename)
			runPerfAnalyze(doutfilename, p['bin-arguments'], g['perf-events'], outfilename)

def genAlgs(algs, templatepath, outfile):
	logging.debug("genAlgs() instantiated")
	logging.debug("genAlgs(): reading template file")
	env = Environment(
		loader=FileSystemLoader(templatepath)
		)
	logging.debug("genAlgs(): rendering ail.ml")
	
	with open(outfile, "w") as out:
		out.write(env.get_template("ail.ml.jnj2").render(jinjaAlgs=algs))
	
	
def compileAmoeba():
	logging.debug("compileAmoeba() instantiated")
	#sudo opam switch 4.01.0
	compileCmd = "opam switch 4.01.0"
	logging.debug("compileAmoeba(): running command " + compileCmd)
	process = Popen(shlex.split(compileCmd))
	process.wait()
	#eval `opam config env`
	compileCmd = "eval `opam config env`"
	logging.debug("compileAmoeba(): running command " + compileCmd)
	process = Popen(shlex.split(compileCmd), shell=True)
	process.wait()
	#./build
	compileCmd = "./build"
	logging.debug("compileAmoeba(): running command " + compileCmd)
	process = Popen(shlex.split(compileCmd), shell=True)
	process.wait()
	
def runAmoeba(binname, algorithm, iterations, outname):
	logging.debug("runAmoeba() instantiated")
	try:
		binpath, binfilename = os.path.split(binname)
		if not os.path.exists(binpath):
			logging.info("runAmoeba(): outputpath directory does not exist, creating: " + binpath)
			os.makedirs(binpath)
		
		outpath, outfilename = os.path.split(outname)
		if not os.path.exists(outpath):
			logging.info("runAmoeba(): outputpath directory does not exist, creating: " + outpath)
			os.makedirs(outpath)
		
		amoebaCmd = "python amoeba.py " + "-i " + iterations + " " + binname
		logging.debug("runAmoeba(): running command " + amoebaCmd)
		process = Popen(shlex.split(amoebaCmd))
		process.wait()
		
		logging.debug("runAmoeba(): amoeba execution complete " + binname)
		logging.debug("runAmoeba(): moving output file to outpath " + binfilename + " TO " + outname)
		
		#Amoeba places the diversified file in the cwd, we need to move it to the desired location
		shutil.move(binfilename, outname)
		logging.debug("runAmoeba(): move completed")
		
	except Exception as e:
		logging.error("An error occured" + str(e))

def runPerfAnalyze(binname, arguments, perfevents, outname):
	logging.debug("runPerfAnalyze() instantiated")
	try:
		binpath, binfilename = os.path.split(binname)
		if not os.path.exists(binpath):
			logging.info("runPerfAnalyze(): outputpath directory does not exist, creating: " + binpath)
			os.makedirs(binpath)
			
		outpath, outfilename = os.path.split(outname)
		if not os.path.exists(outpath):
			logging.info("runPerfAnalyze(): outputpath directory does not exist, creating: " + outpath)
			os.makedirs(outpath)
	
		perfCmd = "perf stat -o " + outname + " -e " + perfevents + " " + binname + " " + arguments
		logging.debug("runPerfAnalyze(): running command " + perfCmd)
		process = Popen(shlex.split(perfCmd))
		process.wait()
		
		logging.debug("runPerfAnalyze(): perf execution complete. Outfile: " + outname)
			
	except Exception as e:
		logging.error("An error occured" + str(e))


if __name__ == "__main__":
	logging.getLogger().setLevel(logging.DEBUG)
	logging.debug("Starting Program")
	if len(sys.argv) != 2:
		logging.error("Usage: amoeba_exp.py <experiment file>")
		exit()
	#filename = '/home/research/div_experimentation/experiment-001.div'
	filename = sys.argv[1]
	readExperimentFile(filename)

#possible algs
###  (* 1: basic block reorder diversify *)
###  let il' = bb_rod_div#visit il' in
###  (* 2: basic block split diversify *)
###  let il' = bb_spt_div#visit il' in
###  (* 3: instruction garbage insertion diversify *)
###  let il' = ins_gar_div#visit il' in
###  (* 4: instruction replace diversify *)
###  let il' = ins_rpl_div#visit il' in
###  (* 5: function reorder diversify *)
###  let il' = func_rod_div#visit il' in
###  (* 6: basic block opaque predicate diversify  *)
###  let il' = bb_opq_div#visit il' in
###  (* 7: function inline diversify *)
###  let il' = func_inline_div#visit  il' in
###  (* 8: basic block merge diversify *)
###  let il' = bb_meg_div#visit il' in
###  (* 9: basic block flatten diversify *)
###  let il' = bb_fln_div#visit il' in
###  (* 10: control flow branch function diversify *)
###  let il' = bb_bfn_div#visit il' in
###
