include("../src/Contexts.jl")
using .Contexts

abstract type AbstractXUT end

mutable struct Position <: AbstractXUT
	x:: Float64
	y:: Float64

	# to round automatically to 2 digits
	function Position(x::Real, y::Real)
        new(round(Float64(x), digits=2), round(Float64(y), digits=2))
    end
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
	lastUpdateTime::Float64  # if this time is by 5 seconds greater
	diameter::Float64 # diameter of the robot/MRS; if empty: default radius is selected for the observers
end

# case 1: incoming >0 intern 0 --> update diameter and position (because it is the midpoint)
# case 2: incoming 0 intern 0 --> no MRS
# case 2.5: incoming 0 intern 0 but first IF fires --> MRS detected by multiple MoRS --> calculate Midpoint and Diameter
# case 3: incoming 0 intern >0 --> MRS with new single observation --> calculate new diameter and take it, if it is greater than the one before and calculate midpoint
# case 3.5 incoming 0 intern >0 but first IF fires --> MRS detected by multiple MoRS --> calculate Midpoint and Diameter
# case 4: incoming >0 intern >0 --> MRS, compare diameter and take the greatest 
function setPos!(robot::PerceivedRobot, pos::Position, diameter::Float64; time::Real = time())
	# case 3 and 3.5 and 2.5 
	if (getDistance(pos, robot.position) >= 0.5 && time-robot.lastUpdateTime <= 1) || (robot.diameter > 0.0 && diameter == 0.0) # TODO: shift hardcoded Thresholds to the top
		robot.diameter = maximum([getDistance(pos, robot.position), robot.diameter, diameter])
		robot.position = Position((robot.position.x + pos.x)/2, (robot.position.y + pos.y)/2)
		robot.lastUpdateTime = time

		return
	end
	
	if robot.diameter == 0 
		robot.diameter = diameter
	end
	# case 1,4: take the greatest diameter of all these three (calculated, incoming, existing)
	if robot.diameter > 0
		robot.diameter = maximum([getDistance(pos, robot.position), robot.diameter, diameter])
	end
	# normal: set position - either the single position or the midpoint already calculated in the observation component 
    robot.position = pos
	robot.lastUpdateTime = time
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


abstract type DiscoveredRobot <: Role end

@newDynamicTeam MultiSpectatorTeam begin
	@IDAttribute ID::Int64
	@role Monitoring << MonitoringTeam [0..Inf] begin end
	@role Exploration << Robot [0..Inf] begin end

	# add other team of Detected Objects, which can have the role interesting or uninteresting
	@role Uninteresting << PerceivedRobot <: DiscoveredRobot [0..Inf] begin end
	@role Interesting << PerceivedRobot <: DiscoveredRobot [0..Inf] begin end
end
