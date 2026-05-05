include("../src/Contexts.jl")
using .Contexts

abstract type AbstractXUT end

mutable struct Position <: AbstractXUT
	x:: Float64
	y:: Float64
end

Base.:(==)(a::Position, b::Position) = a.x == b.x && a.y == b.y

mutable struct Robot
	name::String
	position::Position
	theta::Float64
	waiting::Bool
	goalReached::Bool
	port::Int64
end


# generalize this to Oservation, to include also Object and let roles define, which type it is
mutable struct PerceivedRobot <: AbstractXUT
	name::String
	color::String
	position::Position
end


@newDynamicTeam MonitoringTeam begin
	@IDAttribute ID::Int64
	@relationalAttributes begin
		color::String
	end
	@role Observer << Robot [1..6] begin
		radius::Float64
	end

	# currently not implemented
	@role CamControlledObserver << Robot [0..1] begin end     
	@role ManualControlledObserver << Robot [0..1] begin end  
	@role AccidentInspection << Robot [0..10] begin end
	
	# Plan to switch role, if SUT moves and fall back to Hexagonal Observation only when SUT stands for X seconds   
	# @role Follow SUT << Robot [1..6]  begin end 
	
	@role SUT << AbstractXUT [1] begin
		
	end
end


#abstract type DiscoveredRobot <: Role end

@newDynamicTeam MultiSpectatorTeam begin
	@IDAttribute ID::Int64
	@role Monitoring << MonitoringTeam [0..Inf] begin end
	@role Exploration << Robot [0..Inf] begin end

	# add other team of Detected Objects, which can have the role interesting or uninteresting
	@role DiscoveredRobot << PerceivedRobot [0..Inf] begin end
end
