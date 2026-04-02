include("MultiSpectatirCROM.jl")
using Sockets
using JSON
using DelimitedFiles

server = listen(3004) # TODO add another port, list, accept, ... for the observation messages
println("waiting for clients ...")

clients = Dict() # dictionary: port => client
robots = Dict()

assign


function handle_client_robot(sock)
    global clients, robots
    client_ip, client_port = getpeername(sock)
    println("Handling client ", client_ip, ":", client_port)

    # save socket in a dict to use it later for sending
    clients[client_port] = sock
    println(readline(sock))
    if isopen(sock) 
        msg = JSON.parse(readline(sock))       
        # add new robot to model 
        name = get(get(msg, "robot", 0), "name", 0)
        robot = Robot(name, Position(4,40), 0.0, false, false, client_port)
        robots[name] = robot
        println(robots)
    end

    while isopen(sock)
        msg = JSON.parse(readline(sock)) # busy wait for next message?
        println("received: ", msg)
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


while true
    sleep(3)
    println(robots)
    
end




