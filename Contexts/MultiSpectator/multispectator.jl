include("MultiSpectatorCROM.jl")
include("functions.jl")
using Sockets
using JSON
using DelimitedFiles

# socket for connection to SRL-Loops of all Robots
server = listen(3004) 
# socket connection to Messages Component of all Robots
serverO = listen(3005)

println("waiting for webapp")

# TCP Socket for the webapp connection
socketWebApp = connect(ip"127.0.0.1", 4004)
#write(socketWebApp, "MultiSpectator connected :)\n")

println("waiting for clients ...")

clients = Dict() # dictionary: port => client
globalID = 1

# ============== Initialization ====================
dummy1 = Robot("dummy1", Position(20,2), 0.0, false, false, 40)
dummy2 = Robot("dummy2", Position(30,4), 0.0, false, false, 40)

# initialize MultiSpectator team
@assignRoles MultiSpectatorTeam begin
    name = 1
    dummy1 >> Exploration()
    dummy2 >> Exploration()
end

# ================= Message funcitons ===================

function sendMessageRobot(port, xPos, yPos, state)
    # get correct socket from the clients dicitonary
    if haskey(clients, port)
        socket = clients[port]
        # build the goal message
        goal = JSON.json(Dict(
            "xTarget" => xPos,
            "yTarget" => yPos,
            "state" => state,
        ))
        write(socket, goal * "\n")
    end
end

function sendMessageWebApp()
    # Monitoring
    monitoringTeams = getDynamicTeams(MonitoringTeam)
    monitoring_json = [
    Dict(
        "sut" => team.color,
        "observer" => [obj.name for obj in getObjectsOfRole(team, Observer)]
    )
    for team in monitoringTeams]

    # Discovered Robots
    discRobots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Uninteresting)
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
    println(json_msg)
    write(socketWebApp, json_msg * "\n")
end


# ================= Exploration Function ========== 

# Plan & Execute Step in Exploration case
function exploration(robot::Robot)
    # Exploration Area
    areaPos1 = Position(-2,0)
	areaPos2 = Position(5,2)
    
    nextPos = Position(rand(areaPos1.x:areaPos2.x), rand(areaPos1.y:areaPos2.y))
    # check, if robot cis to close to its next Exploration Position
    while getDistance(robot.position, nextPos) < 1
        nextPos = Position(rand(areaPos1.x:areaPos2.x), rand(areaPos1.y:areaPos2.y))
    end
    sendMessageRobot(robot.port, nextPos.x, nextPos.y, "driving")
end

# ======================= 2 Parallel MAPE-K Loops ================

# MAPE-K loop which handles new WebApp input
#   calculates next goal from input and current configuration
function mapeLoop(sutColor, numberOfObservers::Int64, targetxPos::Int64, targetyPos::Int64)
    global globalID
    println("run webapp input MAPE-Loop")
    println(sutColor)

    # A) Target Position given instead of color 
    if sutColor === nothing
        targetPosition = Position(targetxPos, targetyPos)
        if numberOfObservers > 0 #assign team with given numberOfObservers of robots
            print("herer")
            # 1. create team and assign first observer
            MTteam = assignNewMonitoringTeam(targetPosition)
            if MTteam == 1
                println("unfortunately no robot free for observation")
                return
            end

            # 2. assign more observers
            for i in 2:numberOfObservers
                println("add SECOND Observer")
                result = addObserver(MTteam)
                if result == 1
                    return
                end
            end
        end
        return
    end

    # Find monitoring team
    actualTeam = nothing
    monitoringTeams = getDynamicTeams(MonitoringTeam)
    for team in monitoringTeams
        if team.color == sutColor
            actualTeam = team
        end
    end

    println(numberOfObservers)

    # B) Exit monitoring and disassign monitoring team (handles both Target and SUT Monitoring)
    if actualTeam !== nothing 
        if numberOfObservers <= 0 
           	for observer in getObjectsOfRole(actualTeam, Observer)
                exploration(observer)
            end
			disassignRoles(actualTeam)
            println("dissasigned everything")
            
        # decrease Number of Observers
        elseif length(getObjectsOfRole(actualTeam, Observer)) > numberOfObservers
            # disassign observers until numbers match
            while length(getObjectsOfRole(actualTeam, Observer)) > numberOfObservers
                firstObserver = getObjectsOfRole(actualTeam, Observer)[1]
                @changeRoles typeof(actualTeam) actualTeam.ID begin
                   firstObserver << Observer
                end
                # PLAN + EXECUTE 
                exploration(firstObserver)
                println("decrease")
            end

        # increase Number of Observers
        elseif length(getObjectsOfRole(actualTeam, Observer)) < numberOfObservers
            # assign observers until numbers match
            while length(getObjectsOfRole(actualTeam, Observer)) < numberOfObservers
                result = addObserver(actualTeam)
                if result == 1
                    return 
                end
                println("increase")
            end
        end
        return
    end
        
    # Get PerceivedRobot with the color
    percRobot = getPercRobotByColor(sutColor)
    if percRobot === nothing
        println("SUT not found :(")
        return
    end

    # robot is not monitored
    if !hasRole(percRobot, SUT, MonitoringTeam)
        if numberOfObservers > 0 #assign team with given numberOfObservers of robots
            print("herer")
            
            # 1. assign initial monitoring team
            MTteam = assignNewMonitoringTeam(percRobot)
            if MTteam == 1
                println("unfortunately no robot free for observation")
                return
            end

            # 2. assign more observers
            for i in 2:numberOfObservers
                println("add SECOND Observer Accident UC")
                result = addObserver(MTteam)
                if result == 1
                    return
                end
            end
        end
    end
end


# MAPE-K loop running after an updated PerceivedRobot Position
#   checks, if the PercRobot is an SUT and send an updated goal message to the respective Observer(s)
function mapeLoop(percRobot::PerceivedRobot)
    global globalID
    # check, if perceived Robot is an SUT and has an Observer
    if hasRole(percRobot, SUT, MonitoringTeam)
        # get Observer
        monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if getObjectsOfRole(team, SUT)[1] == percRobot
                observers = getObjectsOfRole(team, Observer)
                for observer in observers
                    sendMessageRobot(observer.port, percRobot.position.x, percRobot.position.y, "monitoring")
                    println("run update SUT MAPE-Loop")
                end 
            end
        end
    end
end


# Monitoring Step for the Messages Component 
function addORupdatePerceivedRobot(observation) #receives single observations
    global globalID
    color = get(observation, "color", "black")
    discoveredRobots = [getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Uninteresting); getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Interesting)] # TODO get all Robots with the abstract roletype DiscoveredRobot
    
    # iterate over all existing robots to update the respective position
    for r in discoveredRobots
        if r.color == color
            # update each perc robots position if it is observed by the robot
            r.position = Position(get(observation, "xPos", 0), get(observation, "yPos", 0))
            if hasRole(r, Uninteresting, MultiSpectatorTeam) && get(observation, "interesting", 0) == true
                @changeRoles MultiSpectatorTeam 1 begin
                    r << Uninteresting
                    r >> Intersting()
                end
                addObserverToPercRobot(r) # assign new MonitoringTeam, if it not already exists
                # INFO: messages to the robots will be send in the MAPE Loop call below
            end
            if hasRole(r, Interesting, MultiSpectatorTeam) && get(observation, "interesting", 0) == false
                @changeRoles MultiSpectatorTeam 1 begin
                    r << Interesting
                    r >> Unintersting()
                end
                disassignMonitoringTeam(r)
            end
            println("updated")
            mapeLoop(r)
            return
        end
    end

    # TODO: race condition in parallel threads!!!
    # add new Discovered Robot
    globalID = globalID+1
    percRobot = PerceivedRobot("robot " * string(globalID), color, Position(get(observation, "xPos", 0), get(observation, "yPos", 0)))
    if get(observation, "interesting", 0) == false
        @changeRoles MultiSpectatorTeam 1 begin
            percRobot >> Uninteresting()
        end
    else 
        @changeRoles MultiSpectatorTeam 1 begin
            percRobot >> Interesting()
        end
        assignNewMonitoringTeam(percRobot)
    end
end

# ================= Multi-Connection Handling for Robots ============
function handle_client_robot(sock)
    global clients
    client_ip, client_port = getpeername(sock)
    println("Handling client ", client_ip, ":", client_port)

    # save socket in a dict to use it later for sending
    clients[client_port] = sock
    #println(readline(sock))

    # initially add new robot
    if isopen(sock) 
        msg = JSON.parse(readline(sock))       
        # add new robot to model 
        name = get(get(msg, "robot", 0), "name", 0)
        robot = Robot(name, Position(4,40), 0.0, false, false, client_port)
        @changeRoles MultiSpectatorTeam 1 begin
            robot >> Exploration()
        end
        # initially trigger exploration
        exploration(robot)
    end

    # constantly update robots attributes
    while isopen(sock)
        msg = JSON.parse(readline(sock)) # busy wait for next message?
        
        # Monitor
        robot.position = Position(get(get(msg, "robot", 0),"xPos",22), get(get(msg, "robot", 0),"yPos",22))
        
        # PLAN: trigger Exploration if goal has been reached
        if !robot.goalReached && get(get(msg, "robot", 0),"goalReached", false)
            exploration(robot) # TODO: better trigger exploration by Hand from the Webapp??
        end
        # Monitor
        robot.goalReached = get(get(msg, "robot", 0),"goalReached", false)

        # Plan:
        # - get current Role and Team of the Robot --> send new Target to the Robot (if required)

        # sendMessageRobot
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
        println(msg)
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


# Receive WebApp Goal Messages and trigger MAPE-Loop subsequently
Threads.@spawn while true
    global answer
    if isopen(socketWebApp)
		msg = JSON.parse(readline(socketWebApp))
        println(msg)
        try
            mapeLoop(get(msg, "color", nothing), get(msg, "observers", 0), get(msg, "xTarget", 0), get(msg, "yTarget", 0))
        catch e
            @error "Thread failed" exception=(e, catch_backtrace())
        finally
            println("Web app connection down")
        end
	end
    sleep(0.1)
end




# =========================== MAIN-Loop ===============================
#   pubilshs current State to the Webapp
while true
    sleep(2)
    sendMessageWebApp()
end




