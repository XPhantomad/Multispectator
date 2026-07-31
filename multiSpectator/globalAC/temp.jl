include("MultiSpectatorCROM.jl")
include("functions.jl")
using Sockets
using JSON
using DelimitedFiles    
    

for i in 2:2
    println("test")
end

globalID = 1

dummy1 = Robot("dummy1", Position(2,2), 0.0, false, false, 401)
dummy3 = Robot("dummy3", Position(2,5), 0.0, false, false, 403)
dummy4 = PerceivedRobot("dummy4", "blue", Position(30,4))
dummy2 = PerceivedRobot("dummy2", "red", Position(3,4))

# initialize MultiSpectator team
@assignRoles MultiSpectatorTeam begin
    name = 1
    dummy1 >> Exploration()
    dummy3 >> Exploration()
    dummy2 >> Uninteresting()
    dummy2 >> Interesting()
    #dummy4 >> Uninteresting()
end
println(getRole(dummy1, getDynamicTeam(MultiSpectatorTeam, 1)))
println("test")
println(filter(r -> typeof(r) == DiscoveredRobot, getRolesOfTeam(getDynamicTeam(MultiSpectatorTeam, 1))))

# initialize MultiSpectator team

@assignRoles MonitoringTeam begin
    name = 1
    color = "red"
    dummy3 >> Observer(9.5)
    dummy4 >> SUT()
end

# println(hasRole(dummy2, SUT, MonitoringTeam))
# if hasRole(dummy2, SUT, MonitoringTeam)
#     # get Observer
#     partner = getTeamPartners(nothing, dummy2, SUT, MonitoringTeam)[1][Observer]
#     println(partner)
# end


println(length(getObjectsOfRole(getDynamicTeam(MonitoringTeam, 1), Observer)))

println("mylength")
team = getDynamicTeam(MonitoringTeam, 1)
@changeRoles typeof(team) team.ID begin
    dummy1 >> Observer(3)
end

team2 = @assignRoles MonitoringTeam begin
    name = 5
    color = "green"
    dummy1 >> Observer(5)
    dummy2 >> SUT()
end

println(team2)

function mapeLoop(webAppInput::String)
    global globalID

    # 1. get PerceivedRobot with the color
    percRobot = getPercRobotByColor(webAppInput)
    if percRobot == nothing
        println("robot not found :(")
        return
    end
    # 2. Assign/Disassign MonitoringTeam
    # if Robot has already the Role of SUT --> disassign this team
    if hasRole(percRobot, SUT, MonitoringTeam)
        monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if team.color == percRobot.color 
                println("team disassigned again")
                observer = getObjectsOfRole(team, Observer)[1] # TODO: for all observers
                #sendMessageRobot(observer.port, 1.0, 2.0, "driving")
                println("driving")
                disassignRoles(MonitoringTeam, team.ID)
            end
        end
    # assign it as SUT and add the closest robot as observer TODO: receive Radius from Webapp 
    else
        robot = getRobotWithShortestDistanceToSUT(percRobot)
        if robot != nothing
            globalID = globalID+1
            @assignRoles MonitoringTeam begin
                name = globalID
                color = webAppInput
                robot >> Observer(0.4)
                percRobot >> SUT()
            end
            # INFO- send new Target-Message
            println("monitoring")
            println(robot.port)
            #sendMessageRobot(robot.port, percRobot.position.x, percRobot.position.y, "monitoring")
        end
    end
end
mapeLoop("red")

function mapeLoop(percRobot::PerceivedRobot)
    # check, if perceived Robot is an SUT and has an Observer
    println(getRoles(percRobot))
    if hasRole(percRobot, SUT, MonitoringTeam)
        # get Observer
        monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if getObjectsOfRole(team, SUT)[1] == percRobot
                observer = getObjectsOfRole(team, Observer)[1] # TODO: for all observers
                #sendMessageRobot(observer.port, percRobot.position.x, percRobot.position.y, "monitoring")
                println("run update MAPE-Loop")
            end
        end
    end
end

mapeLoop(dummy2)
println(getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration))
explorer = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
explorer_json   = [Dict(
    "name" => r.name,
    "x" => r.position.x,
    "y" => r.position.y,
    "port" => r.port
) for r in explorer]
println(explorer_json)


function sendMessageWebApp()
    # Monitoring
    monitoringDict = Dict()
    monitoringTeams = getDynamicTeams(MonitoringTeam)
    monitoring_json = [
    Dict(
        "sut" => getObjectsOfRole(team, SUT)[1].color,
        "observer" => getObjectsOfRole(team, Observer)[1].name
    )
    for team in monitoringTeams]

    # for team in monitoringTeams
    #     monitoringDict[getObjectsOfRole(getDynamicTeam(MonitoringTeam, 1), SUT)[1]] = getObjectsOfRole(getDynamicTeam(MonitoringTeam, 1), Observer)[1]
    # end

    # Discovered Robots
    discRobots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), DiscoveredRobot)
    discRobots_json = [Dict(
        "name" => r.name,
        "x" => r.position.x,
        "y" => r.position.y,
        "color" => r.color
    ) for r in discRobots]

    # Exploration Robots
    explorer = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
    explorer_json   = [Dict(
        "name" => r.name,
        "x" => r.position.x,
        "y" => r.position.y,
        "port" => r.port
    ) for r in explorer]

    msg = Dict(
        "monitoring" => monitoring_json,
        "discoveredRobots" => discRobots_json,
        "explorers" => explorer_json
    )

    json_msg = JSON.json(msg)
    println(msg)
    println(json_msg)
    
    
    # # get correct socket from the clients dicitonary
    # if haskey(clients, port)
    #     socket = clients[port]
    #     # build the goal message
    #     goal = JSON.json(Dict(
    #         "xTarget" => xPos,
    #         "yTarget" => yPos,
    #         "state" => state,
    #         "SUTxPos" => xPos,
    #         "SUTyPos" => yPos
    #     ))
    #     write(socket, goal * "\n")
    # end
end

sendMessageWebApp()