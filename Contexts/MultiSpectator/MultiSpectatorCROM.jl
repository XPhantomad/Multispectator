include("../src/Contexts.jl")
using .Contexts

abstract type AbstractRobot end

mutable struct Position
	x:: Float64
	y:: Float64
end

Base.:(==)(a::Position, b::Position) = a.x == b.x && a.y == b.y

mutable struct Robot <: AbstractRobot
	name::String
	position::Position
	theta::Float64
	waiting::Bool
	goalGiven::Bool
	port::Int64
end


# generalize this to Oservation, to include also Object and let roles define, which type it is
mutable struct PerceivedRobot <: AbstractRobot
	name::String
	position::Position
end


@newDynamicTeam MonitoringTeam begin
	@IDAttribute ID::Int64
	@role Observer << Robot [1..4] begin
		radius::Float64
	end
	@role SUT << PerceivedRobot [1] begin
		
	end
end

@newDynamicTeam MultiSpectatorTeam begin
	@IDAttribute ID::Int64
	@role Monitoring << MonitoringTeam [0..Inf] begin end
	@role Exploration << Robot [0..Inf] begin end

	# add other team of Detected Objects, which can have the role interesting or uninteresting
	@role DiscoveredRobot << PerceivedRobot [0..Inf] begin end
end
