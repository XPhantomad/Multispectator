
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


function addObserver(team::MonitoringTeam, percRobot::PerceivedRobot)
	robot = getRobotWithShortestDistanceToSUT(percRobot)
	if robot !== nothing
		@changeRoles typeof(team) team.ID begin
			robot >> Observer(0.4)
		end
		# PLAN + EXECUTE
		sendMessageRobot(robot.port, percRobot.position.x, percRobot.position.y, "monitoring")
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
