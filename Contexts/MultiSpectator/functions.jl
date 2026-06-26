using Colors

function getDistance(pos1, pos2)
	return abs(hypot((pos1.x - pos2.x),(pos1.y-pos2.y)))
end


function int_to_color(n::Int)
    l = 50 + 20 * sin(n * 1.3)
    a = 40 * sin(n * 2.1)
    b = 40 * cos(n * 1.7)

    return "#" * hex(RGB(Lab(l, a, b)))
end

function getRobotByName(name)
	robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
    robot = findfirst(obj -> obj.name == name, robots)
    return robot !== nothing ? robots[robot] : nothing
end

function getPercRobotByColor(color)
	percRobots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Uninteresting)
    percRobot = findfirst(obj -> obj.color == color, percRobots)
    return percRobot !== nothing ? percRobots[percRobot] : nothing
end

function getRobotWithShortestDistanceToSUT(percRobot)

	robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
	println(robots)
	closestRobot = nothing
	for robot in robots 
		#IMPORTANT: consider only the exploration robots
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

function getRobotWithShortestDistanceToPosition(position)

	robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
	println(robots)
	closestRobot = nothing
	for robot in robots 
		#IMPORTANT: consider only the exploration robots
		if !hasRole(robot, Observer, MonitoringTeam)
			# only for the first iteration
			if closestRobot == nothing
				closestRobot = robot
				continue
			end

			if getDistance(robot.position, position) < getDistance(closestRobot.position, position)
				closestRobot = robot
			end
		end
	end
	return closestRobot
end

# function getSUTByColor(color)

# 	percRobots = getObjectsOfRole(getDynamicTeam(MonitoringTeam, 1), Uninteresting)
#     percRobot = findfirst(obj -> obj.color == color, percRobots)
#     return percRobot !== nothing ? percRobots[percRobot] : nothing
# end


function getMonitoringTeamBySUTColor(color)
	monitoringTeams = getDynamicTeams(MonitoringTeam)
	for team in monitoringTeams
		if team.color == color 
			return team
		end
	end
	return nothing

end

# only once, when robot switches from interesting to uninteresting
function disassignMonitoringTeam(percRobot)
	# robot is already in a Monitoring Team
	if hasRole(percRobot, SUT, MonitoringTeam)
		monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if getObjectsOfRole(team, SUT)[1] == percRobot
				# command all robots to exploration, before disassigning the monitoring team
				for observer in getObjectsOfRole(team, Observer)
					exploration(observer)
				end
				disassignRoles(team)
			end
		end
	end
end


function addObserverToPercRobot(percRobot)
	# robot is already in a Monitoring Team
	if hasRole(percRobot, SUT, MonitoringTeam)
		monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if getObjectsOfRole(team, SUT)[1] == percRobot
				return addObserver(team)
			end
		end
	else
		return assignNewMonitoringTeam(percRobot)
	end
end

function assignNewMonitoringTeam(XUT)
	global globalID 

	# handle the case, if XUT is a Robot not a Position
	position = XUT
	color = color = int_to_color(globalID)
	if typeof(XUT) != Position
		position = XUT.position
		color = XUT.color
	end


    robot = getRobotWithShortestDistanceToPosition(position)
	if robot !== nothing
		globalID = globalID+1
		MTteam = @assignRoles MonitoringTeam begin
			name = globalID
			color = color
			robot >> Observer(0.4)
			XUT >> SUT()
		end
		# PLAN + EXECUTE
		sendMessageRobot(robot.port, position.x, position.y, "monitoring")
		return MTteam
	end
	return 1
end

function addObserver(team::MonitoringTeam)

	XUT = getObjectsOfRole(team, SUT)[1]
	position = XUT
	if typeof(XUT) != Position
		position = XUT.position
	end

	robot = getRobotWithShortestDistanceToPosition(position)
	if robot !== nothing
		@changeRoles typeof(team) team.ID begin
			robot >> Observer(0.4)
		end
		# PLAN + EXECUTE
		sendMessageRobot(robot.port, position.x, position.y, "monitoring")
		return robot
	else
		println("unfortunately no robot free for observation")
		return 1
	end
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
