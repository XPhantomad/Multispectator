
function getDistance(pos1, pos2)
	return abs(hypot((pos1.x - pos2.x),(pos1.y-pos2.y)))
end


function getRobotByName(name)
	robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
    robot = findfirst(obj -> obj.name == name, robots)
    return robot !== nothing ? robots[robot] : nothing
end

function getPercRobotByColor(color)
	percRobots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), DiscoveredRobot)
    percRobot = findfirst(obj -> obj.color == color, percRobots)
    return percRobot !== nothing ? percRobots[percRobot] : nothing
end

function getRobotWithShortestDistanceToSUT(percRobot)

	#IMPORTANT consider only the exploration robots
	robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
	println(robots)
	closestRobot = nothing
	for robot in robots 
		# robot can not be already an observer of another SUT
		if !hasRole(robot, Observer, MonitoringTeam)
			# only for the first iteration
			if closestRobot == nothing
				closestRobot = robot
				continue
			end

			if getDistance(robot.position, percRobot.position) < getDistance(closestRobot.position, percRobot.position)
				closestRobot = robot
			end
		end
	end
	return closestRobot
end

function getSUTByColor(color)

	percRobots = getObjectsOfRole(getDynamicTeam(MonitoringTeam, 1), DiscoveredRobot)
    percRobot = findfirst(obj -> obj.color == color, percRobots)
    return percRobot !== nothing ? percRobots[percRobot] : nothing
end


function getMonitoringTeamBySUTColor(color)
	monitoringTeams = getDynamicTeams(MonitoringTeam)
	for team in monitoringTeams
		if team.color == color 
			return team
		end
	end
	return nothing

end


# TODO: combine to get object by attribute and roööe
function infoInMessage(message, text)
	for info in message 
		if info[1] == text
			return Position(info[2],info[3])
		end
	end
	return false
end



function getRoleOfTeam(team::DynamicTeam, role::Type)
	if !isempty(getObjectsOfRole(team, role))
		return getRole(getObjectsOfRole(team, role)[1], team) # TODO: eliminate magic number 1 --> getRole s OfTeam
	else
		return nothing
	end
end

function getFirstTeam(object)
	if getRoles(object) !== nothing 
        return first(keys(getRoles(object)[nothing]))
    else
        return nothing
    end
end

# FLOCKING 

function vecAddition(vec1, vec2)
	return [vec1[1]+vec2[1], vec1[2]+vec2[2]]
	
end

function claculateFollowingPosition(predecessorPosition)
	robotVector = [robotSelf.position.x, robotSelf.position.y]
	predVector = [predecessorPosition.x, predecessorPosition.y]
	
	theta = robotSelf.theta - (pi/2)
    if theta > pi
        theta = mod(theta,pi)
        theta = -theta
    end
	R = [cos(theta) -sin(theta); sin(theta) cos(theta)]
	
	differenceVector = predVector-robotVector           # robotVec + diffVec = predVec
	rotDiffVec = R^(-1) * differenceVector
	#println(rotDiffVec) 

	# RIGHT (left-branch)
	# resulting vector points to the rigth --> pred is front right --> robot itself is in the left branch
	if rotDiffVec[1] > 0 
		rotResultingVector = vecAddition(rotDiffVec, [-xDist, -yDist])
		#println(rotResultingVector)
		#println("left Branch")
		
		# check, if the x-value for the right branch is greter than zero -> robot should wait in this case (otherwise it lefts the predecessor)
		if rotResultingVector[1] < -0.1 
			return nothing
		end
	# LEFT (right branch)
    else
		rotResultingVector = vecAddition(rotDiffVec, [xDist, -yDist])
		#println(rotResultingVector)
		#println("right Branch")

		# check, if the x-value for the right branch is greter than zero -> robot should wait in this case (otherwise it lefts the predecessor)
		if rotResultingVector[1] > 0.1 
			return nothing
		end
    end
    # Currently the resultingVector relies on the rotatet coordinate system from R
    # check, if the y-value of the vector is below 0 --> robot should wait in this case
    if rotResultingVector[2] <= 0 
        return nothing
    end

    # rotate the rotResultingVector back into the world system
    resultingVector = R * rotResultingVector
	#println(resultingVector)
    # add resulting vector for the movement to the current position vector of the robot
    return Position(round(robotSelf.position.x+resultingVector[1], digits=2), round(robotSelf.position.y+resultingVector[2], digits=2))
end