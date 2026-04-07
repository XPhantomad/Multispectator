include("MultiSpectatorCROM.jl")
using Sockets
using JSON
using DelimitedFiles

server = listen(3004) # TODO add another port, list, accept, ... for the observation messages
println("waiting for clients ...")

clients = Dict() # dictionary: port => client


dummy1 = Robot("dummy1", Position(40,40), 0.0, false, false, 40)
dummy2 = Robot("dummy2", Position(40,40), 0.0, false, false, 40)


# initialize MultiSpectator team
@assignRoles MultiSpectatorTeam begin
    name = 1
    dummy1 >> Exploration()
    dummy2 >> Exploration()
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
        #robots[name] = robot
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
        
        #name = get(get(msg, "robot", 0), "name", 0)
        #robot = robots[name]
        robot.position = Position(get(get(msg, "robot", 0),"xPos",22), get(get(msg, "robot", 0),"yPos",22))
        #robots[name] = robot
        sleep(1.1)
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

function sendMessageRobot(port, xPos, yPos, state)
    # get correct socket from the clients dicitonary
    socket = clients[port]

    # build the goal message
    goal = JSON.json(Dict(
        "xTarget" => 0.0,
        "yTarget" => 0.0,
        "state" => state,
        "SUTxPos" => xPos,
        "SUTyPos" => yPos
    ))
    write(socket, goal * "\n")

end

# color (later ID from QRCode) for the Discovered Robot and name for the Exploration Robot 
webAppInput = ("red", "fb_1")

while true
    sleep(3)
    println(getRolesOfTeam(getDynamicTeam(MultiSpectatorTeam, 1)))
    # WARNING: unsafe
    robots = getObjectsOfRole(getDynamicTeam(MultiSpectatorTeam, 1), Exploration)
    for r in robots
        if r.name == "fb_1"
            sendMessageRobot(r.port, 2,2, "monitoring")
        end
    end


    # Monitoring Request --> Iterate over all Exploration Robots, which is closest to the target --> get Port and perform dispatch
    
    # ANALYSE = determine whether the target is a SUT or a Position
        # determine if the SUT position has changed --> send new Message in the Execute Step

    # Plan = get xPos and build message 

end




