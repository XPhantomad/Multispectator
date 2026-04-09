include("MultiSpectatorCROM.jl")
include("functions.jl")
using Sockets
using JSON
using DelimitedFiles

server = listen(3004) # TODO add another port, list, accept, ... for the observation messages
serverO = listen(3005)
println("waiting for clients ...")

clients = Dict() # dictionary: port => client
globalID = 1

dummy1 = Robot("dummy1", Position(20,2), 0.0, false, false, 40)
dummy2 = Robot("dummy2", Position(30,4), 0.0, false, false, 40)

# initialize MultiSpectator team
@assignRoles MultiSpectatorTeam begin
    name = 1
    dummy1 >> Exploration()
    dummy2 >> Exploration()
end

function sendMessageRobot(port, xPos, yPos, state)
    # get correct socket from the clients dicitonary
    if haskey(clients, port)
        socket = clients[port]

        # build the goal message
        goal = JSON.json(Dict(
            "xTarget" => xPos,
            "yTarget" => yPos,
            "state" => state,
            "SUTxPos" => xPos,
            "SUTyPos" => yPos
        ))
        write(socket, goal * "\n")
    end

end



function handle_client_robot(sock)
    global clients
    client_ip, client_port = getpeername(sock)
    println("Handling client ", client_ip, ":", client_port)

    # save socket in a dict to use it later for sending
    clients[client_port] = sock
    println(readline(sock))

    # initially add new robot
    if isopen(sock) 
        msg = JSON.parse(readline(sock))       
        # add new robot to model 
        name = get(get(msg, "robot", 0), "name", 0)
        robot = Robot(name, Position(4,40), 0.0, false, false, client_port)
        @changeRoles MultiSpectatorTeam 1 begin
            robot >> Exploration()
        end
    end

    # constantly update robots attributes
    while isopen(sock)
        msg = JSON.parse(readline(sock)) # busy wait for next message?
        #println("received: ", msg)
        # TODO: process message here
        # MONITOR Step -> write Data into model
        
        robot.position = Position(get(get(msg, "robot", 0),"xPos",22), get(get(msg, "robot", 0),"yPos",22))
    end
end


# mape loop running after an updated PercRobot Position
function mapeLoop(percRobot::PerceivedRobot)
    # check, if perceived Robot is an SUT and has an Observer
    println(getRoles(percRobot))
    println(hasRole(percRobot, SUT, MonitoringTeam))
    if hasRole(percRobot, SUT, MonitoringTeam)
        # get Observer
        monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if getObjectsOfRole(team, SUT)[1] == percRobot
                observer = getObjectsOfRole(team, Observer)[1] # TODO: for all observers
                sendMessageRobot(observer.port, percRobot.position.x, percRobot.position.y, "monitoring")
                println("run update MAPE-Loop")
            end
        end
    end
end

function addORupdatePerceivedRobot(observation)
    color = get(observation, "color", "black")
    discoveredRobots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), DiscoveredRobot)
    for r in discoveredRobots
        if r.color == color
            r.position = Position(get(observation, "xPos", 0), get(observation, "yPos", 0))
            println("updated")
            # trigger Update of the Observer Robots, if the Perceived Robot is an SUT
            mapeLoop(r)
            return
        end
    end
    
    println(observation)
    # add new Discovered Robot
    robot = PerceivedRobot("didi", color, Position(get(observation, "xPos", 0), get(observation, "yPos", 0)))
    @changeRoles MultiSpectatorTeam 1 begin
        robot >> DiscoveredRobot()
    end
end


function handle_client_observation(sock)
    global clients
    client_ip, client_port = getpeername(sock)
    println("Handling client ", client_ip, ":", client_port)

    # save socket in a dict to use it later for sending
    clients[client_port] = sock

    # constantly update robots attributes
    while isopen(sock)
        msg = JSON.parse(readline(sock)) # busy wait for next message?

        # IMPORTANT: can not be moved to MAPE-K because it runs for each socket connection individually
        observationList = get(msg, "observation", 0)

        for observation in observationList
            addORupdatePerceivedRobot(observation)
        end
    end
end

# accept incoming robot control client requests
Threads.@spawn while true
    global clients
    client = accept(server)
    println("client connected: ", client)

    @async begin
        try
            handle_client_robot(client) # performs a new async function call at each iteration
        catch e
            println("client error: ", e)
        finally
            x, client_port = getpeername(client)
            clients = delete!(clients, client_port)  
            close(client)
            println("client closed")
        end
    end
end

# accept incoming observation client requests
Threads.@spawn while true
    global clients
    client = accept(serverO)
    println("client connected: ", client)

    @async begin
        try
            handle_client_observation(client) # performs a new async function call at each iteration
        catch e
            println("client error: ", e)
        finally
            x, client_port = getpeername(client)
            clients = delete!(clients, client_port)  
            close(client)
            println("client closed")
        end
    end
end


# color (later ID from QRCode) for the Discovered Robot and name for the Exploration Robot 
#webAppInput = "red"



function mapeLoop(webAppInput::String)
    global globalID
    println("run webapp input MAPE-Loop")
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
                sendMessageRobot(observer.port, 1.0, 2.0, "driving")
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
            println(robot.name)
            sendMessageRobot(robot.port, percRobot.position.x, percRobot.position.y, "monitoring")
        end
    end
end

# case1: SUT Position updated
# --> send updated new Target to the respective client
# 1. trigger MAPE
# 2. select Observer Robot, build message, send message

# case2: New Monitoring Goal Config from Webapp 
# --> send updated Target to the respective Client (quit monitoring/hire robot for monitoring)
# 1. adapt runtimemodel
# 2. choose Observer Robot/Former Observer Robot 
# 3. build its new message, send message

# --> Eventbased MAPE-K activation

while true

    # if new message from the webapp or from the messages component arrives --> update corresponding robot and send messages only for it
    # trigger MAPE-Loop per robot??

    global webAppInput, globalID

    # Analyse: create new MonitoringTeam with the received SUT and Observer
    # identifier of the MonitoringTeam corresponds to the SUT 
    # increase team ID at each allocation



    # # 1. get PerceivedRobot with the color
    # percRobot = getPercRobotByColor(webAppInput)
    
    # # 2. Assign/Disassign MonitoringTeam
    # # if Robot has already the Role of SUT --> disassign this team
    # if percRobot != nothing && hasRole(percRobot, SUT, MonitoringTeam)
    #     monitoringTeams = getDynamicTeams(MonitoringTeam)
    #     for team in monitoringTeams
    #         if team.color == percRobot.color 
    #             println("team disassigned again")
    #             disassignRoles(MonitoringTeam, team.id)
    #         end
    #     end
    # # assign it as SUT and add the closest robot as observer TODO: receive Radius from Webapp 
    # else
    #     robot = getRobotWithShortestDistanceToSUT(percRobot)
    #     if robot != nothing
    #         globalID = globalID+1
    #         @assignRoles MonitoringTeam begin
    #             name = globalID
    #             color = webAppInput
    #             robot >> Observer(0.4)
    #             percRobot >> SUT()
    #         end
    #         # INFO- send new Target-Message
    #     end
    # end
        
    #sut = getSUTByColor(webAppInput)
    #     monitoringTeam = getMonitoringTeamBySUTColor(webAppInput)
    #     if monitoringTeam != nothing
    #         disassignRoles(monitoringTeam)
    #     end
    # end

    # 2. get robot with the shortest distance to the SUT
    # if percRobot != nothing &&  getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration) != nothing
    #     robot = getRobotWithShortestDistanceToSUT(percRobot)

    # # 3. check that currently no other Monitoring Team with this objects exists
    # if length(keys(getRoles(robotSelf)[nothing])) == 1 && length(keys(getRoles(percRobot)[nothing])) == 1

    # @assignRoles MonitoringTeam begin
    #     name = 1
    #     dummy1 >> Exploration()
    #     dummy2 >> Exploration()
    # end

    sleep(40)
    mapeLoop("red")
    #println(getRolesOfTeam(getDynamicTeam(MultiSpectatorTeam, 1)))
    # WARNING: unsafe
    # robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
    # percRobots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), DiscoveredRobot)
    # target = findfirst(obj -> obj.color == "red", percRobots)
    # target = target !== nothing ? percRobots[target] : nothing
    # #println(target)
    # if target !== nothing
    #     for r in robots
    #         if r.name == "fb_0"
    #             # TODO: send only, if something has changed in the position of the SUT
    #             sendMessageRobot(r.port, target.position.x,target.position.y, "monitoring")
    #         end
    #     end
    # end

    # Execute MAPE-K Loop only, if WebApp Request occurs or if SUT moves

    # Monitor
    # get webapp request, get changed information from Messages and Runtimemodel
    # set new robot or SUT position --> already done in receive functions
    
    # ANALYSE = determine whether the target is a SUT or a Position
        # set the new Observer-SUT-Pair in the runtimemodel (--> Iterate over all Exploration Robots, which is closest to the target --> get Port and perform dispatch)
        # determine if the position of an SUT has changed --> send new Message in the Execute Step

    # Plan = get TargetPos and build Messages

    # iterate over all Discovered Robots and 
        #check which of them have the SUT Role 
        #(check if the Position has been changed recently)
        # get tho observer to the SUT and with that the client Port 
        # --> build message with client port and target position

    # percRobots = getObjectsOfRole(getDynamicTeam(MultiSpectator, 1), DiscoveredRobot)
    # for robot in percRobots
    #     if hasRole(robot, MonitoringTeam, SUT)
    #         getDynamicTeam()
    #     end

    # end

    # Execute: Send Status message to Webapp 

end




