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

mutable struct PerceivedRobot <: AbstractRobot
	name::String
	position::Position
end




@newDynamicTeam MultiSpectator begin
	@IDAttribute ID::Int64
	@role Leader << AbstractRobot [0..1] begin end
	@role Deputy << AbstractRobot [0..1] begin	end
	@role Follower << AbstractRobot [0..Inf] begin end
	@role Goal << Position [0..1] begin end
end
