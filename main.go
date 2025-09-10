package main

import (
	"fmt"
	"log"

	lua "github.com/yuin/gopher-lua"
)

func main() {
	L := lua.NewState()
	defer L.Close()

	packageTable := L.GetGlobal("package")
	if packageTable == lua.LNil {
		log.Fatal("global 'package' not found")
	}

	currentPathValue := L.GetField(packageTable, "path")

	// Configure path to resolve:
	//   require("lib.aim") → lua/lib/aim.lua
	//   require("globals") → lua/globals.lua
	newPath := fmt.Sprintf("lua/?.lua;lua/?/init.lua;lua/lib/?.lua;%s", currentPathValue.String())
	L.SetField(packageTable, "path", lua.LString(newPath))

	// Optional: Debug output
	finalPath := L.ToStringMeta(L.GetField(packageTable, "path"))
	fmt.Println("Resolved Lua package.path:", finalPath)
	// ---

	// Load and run setup.lua
	if err := L.DoFile("lua/setup.lua"); err != nil {
		log.Fatal("Failed to load setup.lua:", err)
	}

	// Get returned table: { aim.cn, aim.sources }
	ret := L.Get(-1) // top of stack
	if tbl, ok := ret.(*lua.LTable); ok {
		// First return value: aim.cn
		cn := L.GetTable(tbl, lua.LNumber(1))
		if cnTbl, ok := cn.(*lua.LTable); ok {
			// Get cn.conveyors
			conveyors := L.GetField(cnTbl, "conveyors")
			if convTbl, ok := conveyors.(*lua.LTable); ok {
				fmt.Println("\n=== Conveyor IDs ===")
				convTbl.ForEach(func(key lua.LValue, value lua.LValue) {
					if conv, ok := value.(*lua.LTable); ok {
						id := L.GetField(conv, "id")
						if idStr, ok := id.(lua.LString); ok {
							fmt.Println("Conveyor ID:", string(idStr))
						}
					}
				})
			}
		}

		// Second return value: aim.sources
		sources := L.GetTable(tbl, lua.LNumber(2))
		if srcTbl, ok := sources.(*lua.LTable); ok {
			fmt.Println("\n=== Source Block Chains ===")
			srcTbl.ForEach(func(key lua.LValue, value lua.LValue) {
				if src, ok := value.(*lua.LTable); ok {
					chainLen := countChain(L, src, 0)
					fmt.Printf("Source chain length: %d\n", chainLen)
				}
			})
		}
	} else {
		log.Fatal("setup.lua did not return a table")
	}
}

// Recursively count connected blocks
func countChain(L *lua.LState, block *lua.LTable, depth int) int {
	connections := L.GetField(block, "connections")
	if connTbl, ok := connections.(*lua.LTable); ok {
		if connTbl.Len() == 0 {
			return depth
		}
		firstConn := L.GetTable(connTbl, lua.LNumber(1))
		if nextBlock, ok := firstConn.(*lua.LTable); ok {
			return countChain(L, nextBlock, depth+1)
		}
	}
	return depth
}
