#!/usr/bin/python

def contains(a, b):
	""" Returns if the first completely contains the second"""
	return b["x"] >= a["x"] and b["y"] >= a["y"] and a["x"]+a["width"]>=b["x"]+b["width"] and a["y"]+a["height"]>=b["y"]+b["height"]

# Returns 0 if the two intervals i1 and i2 are disjoint, or the length of their overlap otherwise.
def commonIntervalLength(i1start, i1end, i2start, i2end):
	if (i1end < i2start or i2end < i1start):
		return 0
	return min(i1end, i2end) - max(i1start, i2start)

def overlap(rect1, rect2):
	x1=rect1["x"]
	x2=rect1["x"]+rect1["width"]
	x3=rect2["x"]
	x4=rect2["x"]+rect2["width"]
	y1=rect1["y"]
	y2=rect1["y"]+rect1["height"]
	y3=rect2["y"]
	y4=rect2["y"]+rect2["height"]
	return not ((commonIntervalLength(x1,x2,x3,x4) == 0) or (commonIntervalLength(y1,y2,y3,y4) == 0))


class MaxRectsBinPack:
	def __init__(self, w, h):
		self.w=w
		self.h=h
		allRect = {"width" : w, "height":h, "x":0, "y":0}
		self.usedRectangles = []
		self.freeRectangles = [allRect]

	def insert(self, rects):
		while len(rects):
			bestScore1 = 1e101
			bestScore2 = 1e101
			bestNode = None
			for k,r in enumerate(rects):
				newNode, score1, score2 = self.scoreRect(r);
				if (score1 < bestScore1 or (score1 == bestScore1 and score2 < bestScore2)):
					bestScore1 = score1;
					bestScore2 = score2;
					bestNode = newNode;
					bestNodeIndex = k

			if bestNode is None:
				return False;

			self.placeRect(bestNode);
			del rects[bestNodeIndex]
		self.__assertions()

		return True

	def placeRect(self, rect): # pass a rect
		deleteList=[]
		for i,x in enumerate(self.freeRectangles):
			if self.splitFreeNode(x, rect):
				assert(not i in deleteList)
				deleteList+=[i]

		deleteList.sort(reverse=True)
		for i in deleteList:
			del self.freeRectangles[i]

		self.pruneFreeList();
		self.usedRectangles += [rect]

	def scoreRect(self, r):
		newNode, score1, score2 = self.findPositionForNewNodeBestShortSideFit(r["width"], r["height"]);
		if newNode is None: # Cannot fit the current rectangle.
			return None, 1e100, 1e100
		r["x"] = newNode["x"]
		r["y"] = newNode["y"]
		return r, score1, score2

	def occupancy(self):
		usedSurfaceArea = 0
		for v in self.usedRectangles:
			usedSurfaceArea += v.w * v.h

		return 1.0 * usedSurfaceArea / (self.binWidth * self.binHeight);

	def findPositionForNewNodeBestShortSideFit(self, w, h):

		bestNode = None
		bssf = 1e100; # best short side fit
		blsf = 1e100; # best long side fit
		for v in self.freeRectangles:
			if (v["width"] >= w) and (v["height"] >= h):
				leftoverHoriz = v["width"] - w;
				leftoverVert = v["height"] - h;
				ssf = min(leftoverHoriz, leftoverVert);
				lsf = max(leftoverHoriz, leftoverVert);

				if (ssf < bssf or (ssf == bssf and lsf < blsf)):
					bestNode = {"x":v["x"], "y":v["y"], "width":w, "height":h }
					bssf = ssf;
					blsf = lsf;

		return bestNode, bssf, blsf;


	def splitFreeNode(self, freeNode, usedNode):
		"""returns, if split was performed.
		freeNode is part of the freeRectangle list.
		usedNode is to be examined, returns true if freeNode must be deleted."""
		if not overlap(freeNode, usedNode):
			return False

		if (usedNode["x"] < freeNode["x"] + freeNode["width"]) and (usedNode["x"] + usedNode["width"] > freeNode["x"]):
			# New node at the top side of the used node.
			if (usedNode["y"] > freeNode["y"]) and (usedNode["y"] < freeNode["y"] + freeNode["height"]):
				newNode = {"x": freeNode["x"], "y":freeNode["y"], "width": freeNode["width"],"height": freeNode["height"]}
				newNode["height"] = usedNode["y"] - newNode["y"];
				self.freeRectangles += [newNode];

			# New node at the bottom side of the used node.
			if (usedNode["y"] + usedNode["height"]) < (freeNode["y"] + freeNode["height"]):
				newNode = {"x": freeNode["x"], "y":freeNode["y"], "width": freeNode["width"],"height": freeNode["height"]}
				newNode["y"] = usedNode["y"] + usedNode["height"];
				newNode["height"] = freeNode["y"] + freeNode["height"] - (usedNode["y"] + usedNode["height"]);
				self.freeRectangles += [newNode];

		if (usedNode["y"] < freeNode["y"] + freeNode["height"]) and (usedNode["y"] + usedNode["height"] > freeNode["y"]):
			# New node at the left side of the used node.
			if (usedNode["x"] > freeNode["x"]) and (usedNode["x"] < freeNode["x"] + freeNode["width"]):
				newNode = {"x": freeNode["x"], "y":freeNode["y"], "width": freeNode["width"],"height": freeNode["height"]}
				newNode["width"] = usedNode["x"] - newNode["x"];
				self.freeRectangles += [newNode]

			# New node at the right side of the used node.
			if usedNode["x"] + usedNode["width"] < freeNode["x"] + freeNode["width"]:
				newNode = {"x": freeNode["x"], "y":freeNode["y"], "width": freeNode["width"],"height": freeNode["height"]}
				newNode["x"] = usedNode["x"] + usedNode["width"];
				newNode["width"] = freeNode["x"] + freeNode["width"] - (usedNode["x"] + usedNode["width"]);
				self.freeRectangles += [newNode]
		return True;

	def pruneFreeList(self):
		# Go through each pair and remove any rectangle that is redundant.
		deleteList=[]
		for j,a in enumerate(self.freeRectangles):
			for b in self.freeRectangles[j+1:]:
				if contains(b,a) and (not j in deleteList):
					deleteList += [j]
					break;

		deleteList.sort(reverse=True)
		for i in deleteList:
			del self.freeRectangles[i]

	def __repr__(self):
		s = "MaxRectsBinBack free = [ \n"
		for x in self.freeRectangles:
			s+="    "+str(x)+"\n"
		s+=" ] containing [\n"
		for x in self.usedRectangles:
			s+="    "+str(x)+"\n"
		s+=" ]"
		return s

	def __assertRectNotUsed(self, rect):
		for uindex, u in enumerate(self.usedRectangles):
			x1=rect["x"]
			x2=rect["x"]+rect["width"]
			x3=u["x"]
			x4=u["x"]+u["width"]
			y1=rect["y"]
			y2=rect["y"]+rect["height"]
			y3=u["y"]
			y4=u["y"]+u["height"]
			assert((commonIntervalLength(x1,x2,x3,x4) == 0) or (commonIntervalLength(y1,y2,y3,y4) == 0))

	def __assertions(self):
		# no placed rects may overlap
		for vindex, v in enumerate(self.usedRectangles):
			for uindex, u in enumerate(self.usedRectangles):
				if (uindex !=vindex):
					assert(not overlap(v,u))

		# a placed rect must not be overlapped by a free rect
		for vindex, v in enumerate(self.usedRectangles):
			for uindex, u in enumerate(self.freeRectangles):
				assert(not overlap(v,u))

if __name__ == "__main__":
	main={"x":0, "y":0, "width":5, "height":5 }
	assert(contains(main,{"x":0,"y":0, "width":1, "height":1 }))
	assert(contains(main,{"x":0,"y":0, "width":5, "height":5 }))
	assert(contains(main,{"x":4,"y":4, "width":1, "height":1 }))
	assert(contains(main,{"x":4,"y":0, "width":1, "height":1 }))
	assert(contains(main,{"x":0,"y":4, "width":1, "height":1 }))
	assert(not contains(main, {"x":-1,"y":-1, "width":1, "height":1 }))
	assert(not contains(main, {"x": 5,"y": 5, "width":1, "height":1 }))
	assert(not contains(main, {"x": 5,"y": 0, "width":1, "height":1 }))
	assert(not contains(main, {"x": 0,"y": 5, "width":1, "height":1 }))
	assert(not contains(main, {"x": 0,"y": 0, "width":6, "height":1 }))
	assert(not contains(main, {"x": 0,"y": 0, "width":1, "height":6 }))
	assert(commonIntervalLength(0,1,2,3) == 0)
	assert(commonIntervalLength(0,2,2,3) == 0)
	assert(commonIntervalLength(0,3,2,3) == 1)
	assert(commonIntervalLength(0,3,2,4) == 1)
	assert(commonIntervalLength(0,7,2,4) == 2)
	assert(commonIntervalLength(2,7,2,4) == 2)
	assert(commonIntervalLength(3,7,2,4) == 1)
	assert(commonIntervalLength(4,7,2,4) == 0)
	assert(commonIntervalLength(5,7,2,4) == 0)

	assert(overlap({"x":0,"y":0, "width":3, "height":3 },{"x":0,"y":0, "width":1, "height":1 }))
	assert(overlap({"x":0,"y":0, "width":3, "height":3 },{"x":2,"y":2, "width":1, "height":1 }))
	assert(overlap({"x":0,"y":0, "width":3, "height":3 },{"x":0,"y":2, "width":1, "height":1 }))
	assert(overlap({"x":0,"y":0, "width":3, "height":3 },{"x":2,"y":0, "width":1, "height":1 }))

	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":3,"y":0, "width":1, "height":1 }))
	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":0,"y":3, "width":1, "height":1 }))
	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":3,"y":3, "width":1, "height":1 }))
	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":-1,"y":0, "width":1, "height":1 }))
	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":0,"y":-1, "width":1, "height":1 }))

	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":-1,"y":-1, "width":1, "height":1 }))
	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":-2,"y":2, "width":1, "height":1 }))
	assert(not overlap({"x":0,"y":0, "width":3, "height":3 },{"x":-2,"y":4, "width":1, "height":1 }))

	v=MaxRectsBinPack(10, 10)
	v.placeRect({"x":2, "y":2, "width":2, "height":2})
	v.placeRect({"x":2, "y":4, "width":2, "height":2})
	v.placeRect({"x":2, "y":6, "width":2, "height":2})

