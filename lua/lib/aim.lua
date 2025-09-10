local M = {}
M.cn = {
	conveyors = {},
	nodes = {},
	hooks = {}
}
M.sources = {}

function M.get_conveyor_by_id(id)
	for _, conv in ipairs(M.cn.conveyors) do
		if conv.id == id then
			return conv
		end
	end
	error("Conveyor with id " .. id .. " not found")
end

function M.get_agent()
	return {
		type = "",
		onSpawn = function() end,
		onDestroy = function() end
	}
end

---- blocks ----

function M.get_source()  -- FIXED: typo "sorce" → "source"
	local connections = {}
	return {
		frequency = 1,
		tick = function () end,
		connections = connections,
		connect = function(block)
			table.insert(connections, block)  -- FIXED: table.insert
		end
	}
end

function M.get_conv()
	local connections = {}
	return {
		source = {},
		sink = {},
		path = {},
		connections = connections,
		connect = function(block)
			table.insert(connections, block)  -- FIXED: table.insert
		end
	}
end

function M.get_sink()
	return {}
end

return M

