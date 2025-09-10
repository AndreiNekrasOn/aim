-- In process.lua
local aim = require("lib.aim")

local source = aim.get_source()
source.frequency = 1000
source.tick = function ()
	local tote = require("agents.tote")
	source.spawn_agent(tote)
end

local conv = aim.get_conv()
conv.source = aim.get_conveyor_by_id("main_line_source")
conv.sink = aim.get_conveyor_by_id("main_line_source")

local sink = aim.get_sink()

source.connect(conv)
conv.connect(sink)

table.insert(aim.sources, source)


