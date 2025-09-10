local aim = require("lib.aim")

local conveyor = {
	id = "main_line_source",
	width = 5,
	height = 0.1,
	length = 20,
	start_point = {0,0,0},
	direction = {1, 0, 0},
	radius = 0,
	agent_type = "tote",
}

table.insert(aim.cn.conveyors, conveyor)

