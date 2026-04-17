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
write(socketWebApp, "MultiSpectator connected :)\n")

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
            "SUTxPos" => xPos,
            "SUTyPos" => yPos
        ))
        write(socket, goal * "\n")
    end
end

function sendMessageWebApp()
    # Monitoring
    monitoringTeams = getDynamicTeams(MonitoringTeam)
    monitoring_json = [
    Dict(
        "sut" => getObjectsOfRole(team, SUT)[1].color,
        "observer" => getObjectsOfRole(team, Observer)[1].name
    )
    for team in monitoringTeams]

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
function mapeLoop(webAppInput::String)
    global globalID
    println("run webapp input MAPE-Loop")

    # 1. get PerceivedRobot with the color
    percRobot = getPercRobotByColor(webAppInput)
    if percRobot === nothing
        println("SUT not found :(")
        return
    end

    # 2. Assign/Disassign MonitoringTeam (Toggle)
    # if Robot has already the Role of SUT --> disassign this team
    if hasRole(percRobot, SUT, MonitoringTeam)
        monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if team.color == percRobot.color 
                println("team disassigned again")
                observer = getObjectsOfRole(team, Observer)[1] # TODO: for all observers
                # PLAN + EXECUTE 
                exploration(observer)
                disassignRoles(MonitoringTeam, team.ID)
            end
        end
    # otherwise assign it as SUT and add the closest robot as observer TODO: receive Radius from Webapp 
    else
        robot = getRobotWithShortestDistanceToSUT(percRobot)
        if robot !== nothing
            globalID = globalID+1
            @assignRoles MonitoringTeam begin
                name = globalID
                color = webAppInput
                robot >> Observer(0.4)
                percRobot >> SUT()
            end

            # PLAN + EXECUTE
            sendMessageRobot(robot.port, percRobot.position.x, percRobot.position.y, "monitoring")
        else
            println("unfortunately no robot free for observation")
        end
    end
end


# MAPE-K loop running after an updated PerceivedRobot Position
#   checks, if the PercRobot is an SUT and send an updated goal message to the respective Observer(s)
function mapeLoop(percRobot::PerceivedRobot)
    # check, if perceived Robot is an SUT and has an Observer
    #println(getRoles(percRobot))
    #println(hasRole(percRobot, SUT, MonitoringTeam))
    if hasRole(percRobot, SUT, MonitoringTeam)
        # get Observer
        monitoringTeams = getDynamicTeams(MonitoringTeam)
        for team in monitoringTeams
            if getObjectsOfRole(team, SUT)[1] == percRobot
                observer = getObjectsOfRole(team, Observer)[1] # TODO: for all observers
                sendMessageRobot(observer.port, percRobot.position.x, percRobot.position.y, "monitoring")
                println("run update SUT MAPE-Loop")
            end
        end
    end
end


# Monitoring Step for the Messages Component
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
    # TODO: race condition in parallel threads!!!
    println(observation)
    # add new Discovered Robot
    robot = PerceivedRobot("didi", color, Position(get(observation, "xPos", 0), get(observation, "yPos", 0)))
    @changeRoles MultiSpectatorTeam 1 begin
        robot >> DiscoveredRobot()
    end
end

# ================= Multi-Connection Handling for Robots ============
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
        # initially trigger exploration
        exploration(robot)
    end

    # constantly update robots attributes
    while isopen(sock)
        msg = JSON.parse(readline(sock)) # busy wait for next message?
        robot.position = Position(get(get(msg, "robot", 0),"xPos",22), get(get(msg, "robot", 0),"yPos",22))

        # trigger Exploration if goal has been reached
        if !robot.goalReached && get(get(msg, "robot", 0),"goalReached", false)
            exploration(robot) # TODO: better trigger exploration by Hand from the Webapp??
        end
        robot.goalReached = get(get(msg, "robot", 0),"goalReached", false)
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


# Receive WebApp Goal Messages and trigger MAPE-Loop subsequently
Threads.@spawn while true
    global answer
    if isopen(socketWebApp)
		msg = JSON.parse(readline(socketWebApp))
        println(msg)
        mapeLoop(get(msg, "color", "black"))
	end
    sleep(0.5)
end




# =========================== MAIN-Loop ===============================
#   pubilshs current State to the Webapp
while true
    sleep(2)
    # TBD: execute exploration strategy
    sendMessageWebApp()
end




