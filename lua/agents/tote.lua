local aim = require("lib.aim")

local M = aim.get_agent()

M.type = "tote"
M.number = TOTE_NUMBER

M.onEnter = function ()
	TOTE_NUMBER = TOTE_NUMBER + 1
end

return M

