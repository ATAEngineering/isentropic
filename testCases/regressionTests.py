# Copyright 2023, ATA Engineering, Inc.
#
# This file is part of the CHEM solver framework.
#
# The CHEM solver framework is free software: you can redistribute it
# and/or modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# The CHEM solver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with the CHEM solver.  If not, see <http://www.gnu.org/licenses>
#
# NOTICE: The GNU license describes the parameters of your redistribution
# rights granted by Mississippi State University but the redistribution
# of this software is also constrained by export control laws.  This
# software may also be considered as covered by EAR or ITAR regulation
# regimes and so it is your responsibility to ensure that this software
# is redistributed only to US persons and any redistribution is in
# conformance with applicable United States export control laws.
#

import os
import argparse
import shutil
import sys
import datetime
import subprocess
import time


class regressionTest:
  def __init__(self):
    self._caseName = "none"
    self._iterations = 100
    self._outputFreq = 50
    self._procs = 1
    self._truthData = {}
    self._truthDataLocation = {}
    self._mpirunPath = "mpirun"
    self._home = os.getcwd()
    self._runDirectory = "."
    self._percentTolerance = 0.01
    self._isRestart = False
    self._restartFile = "none"
    self._passedStatus = "NOT RUN"
    self._runScriptName = "run"

  def SetRegressionCase(self, name):
    self._caseName = name

  def SetNumberOfIterations(self, num):
    self._iterations = num
    self._outputFreq = num // 2

  def OutputFrequency(self):
    return self._outputFreq

  # In case we need a different output frequency, e.g. in the case of restarts
  def SetOutputFrequency(self, num):
    self._outputFreq = num

  def SetNumberOfProcessors(self, num):
    self._procs = num

  def Processors(self):
    return self._procs

  def PassedStatus(self):
    return self._passedStatus

  def SetTruthData(self, tdata, tdataLoc):
    self._truthData = tdata  # "file" : [data]
    self._truthDataLocation = tdataLoc  # "file" : [columns]

  def SetRunDirectory(self, path):
    self._runDirectory = path

  def SetMpirunPath(self, path):
    self._mpirunPath = path

  def SetIgnoreIndices(self, ind):
    self._ignoreIndices.append(ind)

  def SetPercentTolerance(self, per):
    self._percentTolerance = per

  def GoToRunDirectory(self):
    os.chdir(self._runDirectory)

  def SetRunScript(self, name):
    self._runScriptName = name

  def SetRestart(self, resFlag):
    self._isRestart = resFlag

  def SetRestartFile(self, resFile):
    self._restartFile = resFile

  def ReturnToHomeDirectory(self):
    os.chdir(self._home)

  def GetSimulationData(self):
    simData = {}
    for fname, cols in self._truthDataLocation.items():
      rfile = open(fname, "r")
      lastLine = rfile.readlines()[-1]
      rfile.close()
      tokens = lastLine.split()
      sd = [float(tokens[i]) for i in cols]
      simData.update({fname: sd})
    return simData

  def CompareSimulationToTruth(self, returnCode):
    simData = self.GetSimulationData()
    passing = []
    if (returnCode == 0):
      for fname, truthData in self._truthData.items():
        sd = simData[fname]
        filePass = [abs(sd - truthData[i]) <= self._percentTolerance * abs(truthData[i])
                    for i, sd in enumerate(sd)]
        passing.extend(filePass)
    else:
      for fname, truthData in self._truthData.items():
        passing.extend([False for i in truthData])
    return passing, simData, self._truthData

  # change input file to have number of iterations specified for test
  def ModifyInputFile(self):
    fname = self._caseName + ".vars"
    fnameBackup = fname + ".old"
    shutil.move(fname, fnameBackup)
    with open(fname, "w") as fout:
      with open(fnameBackup, "r") as fin:
        for line in fin:
          if "stop_iter:" in line:
            fout.write("stop_iter: " + str(self._iterations) + "\n")
          elif "plot_freq:" in line:
            fout.write("plot_freq: " + str(self._outputFreq) + "\n")
          elif "restart_freq:" in line:
            fout.write("restart_freq: " + str(self._outputFreq) + "\n")
          else:
            fout.write(line)

  # modify the input file and run the test
  def RunCase(self):
    self.GoToRunDirectory()
    print("---------- Starting Test:", self._runDirectory, "----------")
    print("Current directory:", os.getcwd())
    print("Modifying input file...")
    self.ModifyInputFile()
    cmd = "bash ./" + self._runScriptName
    print(cmd)
    start = datetime.datetime.now()
    interval = start
    process = subprocess.Popen(cmd, shell=True)
    while process.poll() is None:
      current = datetime.datetime.now()
      if (current - interval).total_seconds() > 60.:
        print("----- Run Time: %s -----" % (current - start))
        interval = current
        time.sleep(0.5)
    returnCode = process.poll()
    
    passed, sim, truth = self.CompareSimulationToTruth(returnCode)
    if (returnCode == 0):
      print("Simulation completed with no errors")
      # test simulation/truth for pass/fail
      if all(passed):
        print("All tests for", self._runDirectory, "PASSED!")
        self._passedStatus = "PASSED"
      else:
        print("Tests for", self._runDirectory, "FAILED!")
        self._passedStatus = "MISMATCH"
      print("Expecting data:", truth)
      print("Got data:      ", sim)
    else:
      print("ERROR: Simulation terminated with errors")
      self._passedStatus = "ERRORS"
    
    duration = datetime.datetime.now() - start
    print("Test Duration:", duration)
    print("---------- End Test:", self._runDirectory, "----------")
    print("")
    print("")
    self.ReturnToHomeDirectory()
    return passed


def main():
  # Set up options
  parser = argparse.ArgumentParser()
  parser.add_argument("-m", "--mpirunPath", action="store",
                      dest="mpirunPath", default="mpirun",
                      help="Path to mpirun. Default = %(default)s")
  parser.add_argument("-n", "--numCores", action="store",
                      dest="numCores", default=1, type=int,
                      help="Maximum number of cores to use. Default = 1")
  

  args = parser.parse_args()

  # get maximum cores on server
  maxProcs = args.numCores

  totalPass = True

  # ------------------------------------------------------------------
  # Regression tests
  # ------------------------------------------------------------------
  run_nozzle1 = True
  run_nozzle2 = True

  # ------------------------------------------------------------------
  # nozzle1 - Mach 2 nozzle, specified h0 and fixed mass fractions
  nozzle1 = regressionTest()
  if run_nozzle1:
    nozzle1.SetRegressionCase("nozzle")
    nozzle1.SetRunDirectory("nozzle1")
    nozzle1.SetNumberOfProcessors(maxProcs)
    nozzle1.SetNumberOfIterations(200)
    truthData = {os.path.join("output", "resid.dat"): [0.02381815049, 501788.5418, 1.59875457], # residuals
                                        "probe1.dat": [2842.986883529, 92002.71268649, 2.5234447473189e-06]} # probe
    truthDataLocation = {os.path.join("output", "resid.dat"): [1, 2, 3],
                                                "probe1.dat": [2, 3, 15]} # T, P, fNO
    nozzle1.SetTruthData(truthData, truthDataLocation)

    # run regression case
    passed = nozzle1.RunCase()
    totalPass = totalPass and all(passed)

  # ------------------------------------------------------------------
  # nozzle2 - Mach 2 nozzle, specified h0 and equilibrium mass fractions
  nozzle2 = regressionTest()
  if run_nozzle2:
    nozzle2.SetRegressionCase("nozzle")
    nozzle2.SetRunDirectory("nozzle2")
    nozzle2.SetNumberOfProcessors(maxProcs)
    nozzle2.SetNumberOfIterations(200)
    truthData = {os.path.join("output", "resid.dat"): [1.409578009e-12, 1.25970193e-05, 2.723237489e-09], # residuals
                                        "probe1.dat": [2661.5920734386, 92099.373376843, 0.031681178968845]} # probe
    truthDataLocation = {os.path.join("output", "resid.dat"): [1, 2, 3],
                                                "probe1.dat": [2, 3, 15]} # T, P, fNO
    nozzle2.SetTruthData(truthData, truthDataLocation)

    # run regression case
    passed = nozzle2.RunCase()
    totalPass = totalPass and all(passed)

  # ------------------------------------------------------------------
  # regression test overall pass/fail
  # ------------------------------------------------------------------
  errorCode = 0
  if totalPass:
    print("All tests passed!")
  else:
    print("ERROR: Some tests failed")
    errorCode = 1
  print("--------------------------------------------------")
  print("nozzle1: ", nozzle1.PassedStatus())
  print("nozzle2: ", nozzle2.PassedStatus())
  sys.exit(errorCode)


if __name__ == "__main__":
  main()
