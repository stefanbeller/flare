#!/usr/bin/python

import MaxRectsBinPack
import random
import sys
import tempfile
import subprocess
import os
import copy

class MinRectFinder:
	def __init__(self):
		self.tryBoundExponential = 64
		self.tryBoundBinSearch = 128
		self.tryBoundLinear = 4096
		self.tryBoundSimilar = 1024

	def areaScore(self, rects):
		size,w,h = self._areaInformation(rects)
		w_2, h_2 = 1, 1;

		while w >= w_2:
			w_2 *= 2
		while h >= h_2:
			h_2 *= 2

		return (w_2 * h_2 + w * h, w * h)

	def _setBestMatchTo(self, rects):
		print "update bestMatch to ", self._areaInformation(rects)
		self.bestMatch=[]
		for rect in rects:
			newdict={}
			for k in rect:
				newdict[k] = rect[k]
			self.bestMatch += [newdict]

	def _compareRectConfigurations(self, rects):
		""" updates self.bestMatch if argument is better"""
		if self.bestMatch is None:
			self._setBestMatchTo(rects)
			return True

		currentScore = self.areaScore(rects)
		bestScore = self.areaScore(self.bestMatch)
		for cs, bs in zip(currentScore, bestScore):
			if cs > bs:
				return False
			if cs < bs:
				self._setBestMatchTo(rects)
				return True
		return False

	def _areaInformation(self, rects):
		""" returns the maximum width and the maximum height of the given rects."""
		w, h = 0, 0
		for n in rects:
			w = max(n["x"]+n["width"], w)
			h = max(n["y"]+n["height"], h)
		return w * h, w, h

	def findBestEnclosingRectangle(self, rects):
		self.bestMatch = None # holds the very best result found so far: w,h, images
		self.rects = rects
		self._defineBoundaries()
		print"attempt to place ", len(rects), "rectangles total area =",
		print self.minTotalArea, " maximum width/height:",self.minWidth,self.minHeight

		upperBound = self._exponentialGrowth()
		upperBound = min(upperBound, self.maxTotalArea)
		self._binarySearch(self.minTotalArea, upperBound)
		self._linearLowering()
		self._similarSearch()
		return self.bestMatch

	def _defineBoundaries(self):
		self.minTotalArea = 0 # the sum of all individual rect areas
		self.minWidth = 0 # the maximum width of the rects
		self.minHeight = 0# the maximum height of the rects
		for i in self.rects:
			self.minTotalArea += i["width"]*i["height"]
			self.minWidth = max(i["width"], self.minWidth)
			self.minHeight = max(i["height"], self.minHeight)
		self.maxTotalArea = self.minWidth * self.minHeight * len(self.rects)

		self.rectPassString="" # passed to rectpacker
		for rect in sorted(self.rects, key=lambda x: x["index"]):
			self.rectPassString += " " + str(rect["width"]) + " " + str(rect["height"])

	def _exponentialGrowth(self):
		print "exponential growth"
		growing=1;
		area = 1.0 * self.minTotalArea
		keepgoing=True
		while keepgoing:
			keepgoing = True
			area = self.minTotalArea + growing
			growing = 2 * growing
			if self.checkAreaSize(area, maxTries=self.tryBoundExponential):
				keepgoing = False

		return area

	def _binarySearch(self, lowerBound, upperBound):
		print "bin search"
		while upperBound - lowerBound > 1:
			area = int((upperBound+lowerBound)/2)
			if self.checkAreaSize(area, maxTries=self.tryBoundBinSearch):
				upperBound=area
			else:
				lowerBound=area

	def _linearLowering(self):
		print "linear lowering"
		keepGoing = True
		while keepGoing:
			print "new iteration of _linearLowering"
			area = self._areaInformation(self.bestMatch)[0] - 1
			if not self.checkAreaSize(area, maxTries=self.tryBoundLinear, maxRandomAreaShrinking=0.1 * area):
				keepGoing = False

	def _similarSearch(self):
		print "similar search"
		keepGoing = True
		while keepGoing:
			info = self._areaInformation(self.bestMatch)
			area = info[0]
			if not self.checkAreaSize(area, maxTries=self.tryBoundSimilar, widthrange=(info[1]*0.9,info[1]*1.1)):
				keepGoing = False

	def checkAreaSize(self, area, maxTries=8, quitEarly=True, maxRandomAreaShrinking=0, widthrange=None):
		# returns true if a better thing was found.
		foundBetter=False
		processes = []
		filehandles = []
		yetToStart=maxTries
		maxCpus = 12
		while yetToStart > 0 or len(processes) > 0:
			while len(processes) < maxCpus and yetToStart > 0:
				newarea = area - random.randint(0, int(maxRandomAreaShrinking*(1.0*yetToStart/maxTries)))
				if widthrange is None:
					w = random.randint(self.minWidth, int(newarea/self.minWidth))
				else:
					w = random.randint(int(widthrange[0]), int(widthrange[1]))
				h = int(newarea/w)
				tf = tempfile.mkstemp()
				string = "rectpacker " + str(w) + " " + str(h) + self.rectPassString
				p = subprocess.Popen(string, stdout = tf[0], shell = True)
				yetToStart -= 1
				processes += [p]
				filehandles += [tf]

			for c in xrange(len(processes)-1, -1, -1):
				p = processes[c]
				tf = filehandles[c]
				if yetToStart <= 0:
					p.wait()

				if not p.poll() is not None:
					continue

				if p.returncode == 0:
					filehandle = open(tf[1], 'r')
					positions = filehandle.readlines()
					filehandle.close()
					rectscopy = []
					rectscopy.extend(self.rects)
					assert(len(positions) == len(rectscopy))
					for pos, rect in zip(positions, rectscopy):
						rect["x"]=int(pos.split()[0])
						rect["y"]=int(pos.split()[1])
					foundBetter = self._compareRectConfigurations(rectscopy)
					if quitEarly:
						yetToStart = 0

				os.close(tf[0])
				os.remove(tf[1])
				del processes[c]
				del filehandles[c]
				assert(len(processes) == len(filehandles))
		return foundBetter
