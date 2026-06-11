package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// Binding represents a parsed keybinding: a key (scancode or mouse button) mapped to a command.
type Binding struct {
	Command string
	Args    []string
}

// Keybindings holds the parsed key and mouse bindings.
type Keybindings struct {
	Keys  map[int]Binding // scancode → binding
	Mouse map[int]Binding // button (1=left, 2=middle, 3=right) → binding
}

// keyNameToScancode maps conf key names to SDL scancodes.
var keyNameToScancode = map[string]int{
	"escape":    ScancodeEscape,
	"return":    ScancodeReturn,
	"space":     ScancodeSpace,
	"backspace": ScancodeBackspace,
	"tab":       ScancodeTab,
	"up":        ScancodeUp,
	"down":      ScancodeDown,
	"left":      ScancodeLeft,
	"right":     ScancodeRight,
	"a":         ScancodeA,
	"b":         ScancodeB,
	"c":         ScancodeC,
	"e":         ScancodeE,
	"f":         ScancodeF,
	"g":         ScancodeG,
	"i":         ScancodeI,
	"l":         ScancodeL,
	"m":         ScancodeM,
	"n":         ScancodeN,
	"o":         ScancodeO,
	"p":         ScancodeP,
	"q":         ScancodeQ,
	"s":         ScancodeS,
	"t":         ScancodeT,
	"u":         ScancodeU,
	"v":         ScancodeV,
	"w":         ScancodeW,
	"x":         ScancodeX,
	"y":         ScancodeY,
	"z":         ScancodeZ,
	"0":         Scancode0,
	"1":         Scancode1,
	"2":         Scancode2,
	"3":         Scancode3,
	"4":         Scancode4,
	"5":         Scancode5,
	"6":         Scancode6,
	"7":         Scancode7,
	"8":         Scancode8,
	"9":         Scancode9,
	"f1":        ScancodeF1,
	"f2":        ScancodeF2,
	"f3":        ScancodeF3,
	"f12":       ScancodeF12,
	"kp0":       ScancodeKP0,
	"kp1":       ScancodeKP1,
	"kp2":       ScancodeKP2,
	"kp3":       ScancodeKP3,
	"kp4":       ScancodeKP4,
	"kp5":       ScancodeKP5,
	"kp6":       ScancodeKP6,
	"kp7":       ScancodeKP7,
	"kp8":       ScancodeKP8,
	"kp9":       ScancodeKP9,
}

// mouseNameToButton maps conf mouse names to button numbers.
var mouseNameToButton = map[string]int{
	"lmouse": 1,
	"rmouse": 3,
	"mmouse": 2,
}

// LoadKeybindings parses a keybindings.conf file.
func LoadKeybindings(confDir string) *Keybindings {
	kb := &Keybindings{
		Keys:  make(map[int]Binding),
		Mouse: make(map[int]Binding),
	}

	path := filepath.Join(confDir, "keybindings.conf")
	data, err := os.ReadFile(path)
	if err != nil {
		// Fall back to defaults if file not found
		kb.loadDefaults()
		return kb
	}

	for line := range strings.SplitSeq(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Split into key name and command (separated by whitespace)
		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}
		keyName := strings.ToLower(fields[0])
		command := fields[1]
		args := fields[2:]

		binding := Binding{Command: command, Args: args}

		// Check if it's a mouse binding
		if btn, ok := mouseNameToButton[keyName]; ok {
			kb.Mouse[btn] = binding
			continue
		}

		// Check if it's a keyboard binding
		if scancode, ok := keyNameToScancode[keyName]; ok {
			kb.Keys[scancode] = binding
			continue
		}
	}

	return kb
}

// loadDefaults sets up the default keybindings (matching keybindings.conf).
func (kb *Keybindings) loadDefaults() {
	// Cursor movement
	kb.Keys[ScancodeLeft] = Binding{Command: "left"}
	kb.Keys[ScancodeRight] = Binding{Command: "right"}
	kb.Keys[ScancodeUp] = Binding{Command: "up"}
	kb.Keys[ScancodeDown] = Binding{Command: "down"}
	kb.Keys[ScancodeKP1] = Binding{Command: "jumppos", Args: []string{"4", "16"}}
	kb.Keys[ScancodeKP2] = Binding{Command: "jumppos", Args: []string{"10", "16"}}
	kb.Keys[ScancodeKP3] = Binding{Command: "jumppos", Args: []string{"16", "16"}}
	kb.Keys[ScancodeKP4] = Binding{Command: "jumppos", Args: []string{"4", "10"}}
	kb.Keys[ScancodeKP5] = Binding{Command: "jumppos", Args: []string{"10", "10"}}
	kb.Keys[ScancodeKP6] = Binding{Command: "jumppos", Args: []string{"16", "10"}}
	kb.Keys[ScancodeKP7] = Binding{Command: "jumppos", Args: []string{"4", "4"}}
	kb.Keys[ScancodeKP8] = Binding{Command: "jumppos", Args: []string{"10", "4"}}
	kb.Keys[ScancodeKP9] = Binding{Command: "jumppos", Args: []string{"16", "4"}}

	// Placing stones and playing
	kb.Keys[ScancodeTab] = Binding{Command: "myplay", Args: []string{"white"}}
	kb.Keys[ScancodeSpace] = Binding{Command: "playblack"}
	kb.Keys[ScancodeM] = Binding{Command: "gnugoblack"}
	kb.Keys[ScancodeReturn] = Binding{Command: "gnugowhite"}
	kb.Keys[ScancodeW] = Binding{Command: "togglewhite"}
	kb.Keys[ScancodeB] = Binding{Command: "toggleblack"}
	kb.Keys[ScancodeU] = Binding{Command: "undo"}
	kb.Keys[ScancodeA] = Binding{Command: "passblack"}
	kb.Keys[ScancodeZ] = Binding{Command: "passwhite"}
	kb.Keys[ScancodeG] = Binding{Command: "showlastmove"}

	// SGF-related
	kb.Keys[ScancodeS] = Binding{Command: "savesgf", Args: []string{"saved.sgf"}}
	kb.Keys[ScancodeL] = Binding{Command: "reloadsgf"}
	kb.Keys[ScancodeN] = Binding{Command: "next"}
	kb.Keys[ScancodeP] = Binding{Command: "passblack"}

	// GnuGo commands
	kb.Keys[ScancodeF1] = Binding{Command: "gnugoinfo"}
	kb.Keys[ScancodeV] = Binding{Command: "showboard"}
	kb.Keys[ScancodeKP0] = Binding{Command: "level", Args: []string{"0"}}
	kb.Keys[Scancode1] = Binding{Command: "level", Args: []string{"1"}}
	kb.Keys[Scancode2] = Binding{Command: "level", Args: []string{"2"}}
	kb.Keys[Scancode3] = Binding{Command: "level", Args: []string{"3"}}
	kb.Keys[Scancode4] = Binding{Command: "level", Args: []string{"4"}}
	kb.Keys[Scancode5] = Binding{Command: "level", Args: []string{"5"}}
	kb.Keys[Scancode6] = Binding{Command: "level", Args: []string{"6"}}
	kb.Keys[Scancode7] = Binding{Command: "level", Args: []string{"7"}}
	kb.Keys[Scancode8] = Binding{Command: "level", Args: []string{"8"}}
	kb.Keys[Scancode9] = Binding{Command: "level", Args: []string{"9"}}
	kb.Keys[Scancode0] = Binding{Command: "level", Args: []string{"10"}}
	kb.Keys[ScancodeT] = Binding{Command: "time", Args: []string{"5", "0", "0"}}
	kb.Keys[ScancodeY] = Binding{Command: "play100moves"}
	kb.Keys[ScancodeO] = Binding{Command: "futurewhite"}
	kb.Keys[ScancodeF2] = Binding{Command: "analyze"}

	// GTP commands
	kb.Keys[ScancodeE] = Binding{Command: "gtp", Args: []string{"estimate_score"}}
	kb.Keys[ScancodeF] = Binding{Command: "gtp", Args: []string{"final_score"}}
	kb.Keys[ScancodeX] = Binding{Command: "multigtp", Args: []string{"move_probabilities"}}
	kb.Keys[ScancodeF3] = Binding{Command: "multigtp", Args: []string{"show_dragons"}}

	// Special functions
	kb.Keys[ScancodeEscape] = Binding{Command: "quit", Args: []string{"0"}}
	kb.Keys[ScancodeI] = Binding{Command: "toggleillegal"}
	kb.Keys[ScancodeQ] = Binding{Command: "quit", Args: []string{"0"}}
	kb.Keys[ScancodeBackspace] = Binding{Command: "clear"}
	kb.Keys[ScancodeC] = Binding{Command: "console"}
	kb.Keys[ScancodeF12] = Binding{Command: "save", Args: []string{"goboard.bmp"}}

	// Mouse
	kb.Mouse[1] = Binding{Command: "playblack"}
	kb.Mouse[3] = Binding{Command: "status"}
	kb.Mouse[2] = Binding{Command: "newasblack"}
}

// ExecuteBinding runs a binding command. Returns true if the app should quit.
func (a *App) ExecuteBinding(b Binding, drawFn func()) bool {
	switch b.Command {
	// Cursor movement (always allowed)
	case "left":
		a.board.MoveCursor(-1, 0)
	case "right":
		a.board.MoveCursor(1, 0)
	case "up":
		a.board.MoveCursor(0, -1)
	case "down":
		a.board.MoveCursor(0, 1)
	case "jumppos":
		if len(b.Args) >= 2 {
			x, _ := strconv.Atoi(b.Args[0])
			y, _ := strconv.Atoi(b.Args[1])
			a.board.JumpPos(x, y)
		}

	// Quit is always allowed
	case "quit":
		a.board.ShowBoard()
		return true

	// Non-GTP commands (always allowed)
	case "showlastmove":
		a.board.ShowLastMove()
	case "previous":
		a.board.PreviousMove()
	case "next":
		a.board.NextMove()
	case "nextorload":
		a.board.NextOrLoad()
	case "guessorplace":
		a.board.GuessOrPlace()
	case "toggleillegal":
		a.board.ToggleIllegal()
	case "save":
		fn := "goboard.bmp"
		if len(b.Args) > 0 {
			fn = b.Args[0]
		}
		if err := a.renderer.SaveScreenshot(fn); err != nil {
			fmt.Fprintf(os.Stderr, "Screenshot failed: %v\n", err)
		} else {
			fmt.Println("Saved:", fn)
		}

	default:
		// All other commands require GTP access — skip if engine is busy
		if a.board.EngineThinking() {
			return false
		}
		a.executeGTPBinding(b, drawFn)
	}
	return false
}

// executeGTPBinding handles commands that may use the GTP engine.
// Must only be called when the engine is not busy.
func (a *App) executeGTPBinding(b Binding, drawFn func()) {
	switch b.Command {
	// Placing stones and playing
	case "playblack":
		experimental := len(b.Args) > 0 && b.Args[0] == "experimental"
		if experimental {
			if a.board.ToggleBlack() {
				if drawFn != nil {
					drawFn()
				}
				a.board.MyPlay("white", drawFn)
			}
		} else {
			a.board.PlayBlackThenEngine(drawFn)
		}
	case "playwhite":
		experimental := len(b.Args) > 0 && b.Args[0] == "experimental"
		if experimental {
			if a.board.ToggleWhite() {
				if drawFn != nil {
					drawFn()
				}
				a.board.MyPlay("black", drawFn)
			}
		} else {
			a.board.PlayWhiteThenEngine(drawFn)
		}
	case "myplay":
		color := "white"
		if len(b.Args) > 0 {
			color = b.Args[0]
		}
		a.board.MyPlay(color, drawFn)
	case "gnugowhite":
		a.board.GnuGoWhite()
	case "gnugoblack":
		a.board.GnuGoBlack()
	case "togglewhite":
		a.board.ToggleWhite()
	case "toggleblack":
		a.board.ToggleBlack()
	case "undo":
		a.board.Undo()
	case "passblack":
		a.board.PassBlack()
	case "passwhite":
		a.board.PassWhite()

	// SGF-related
	case "savesgf":
		fn := "saved.sgf"
		if len(b.Args) > 0 {
			fn = b.Args[0]
		}
		a.board.SaveSGF(fn)
	case "reloadsgf":
		if a.board.filename != "" {
			a.board.LoadSGF(a.board.filename)
		}
	case "loadsgf":
		fn := ""
		if len(b.Args) > 0 {
			fn = b.Args[0]
		}
		a.board.LoadSGF(fn)

	// GnuGo commands
	case "gnugoinfo":
		a.board.GnuGoInfo()
	case "showboard":
		a.board.ShowBoard()
	case "level":
		if len(b.Args) > 0 {
			lvl, _ := strconv.Atoi(b.Args[0])
			a.board.SetLevel(lvl)
		}
	case "time":
		main, byo, stones := 5, 0, 0
		if len(b.Args) >= 1 {
			main, _ = strconv.Atoi(b.Args[0])
		}
		if len(b.Args) >= 2 {
			byo, _ = strconv.Atoi(b.Args[1])
		}
		if len(b.Args) >= 3 {
			stones, _ = strconv.Atoi(b.Args[2])
		}
		a.board.TimeSettings(main, byo, stones)
	case "play100moves":
		a.board.Play100Moves(drawFn)
	case "futurewhite":
		a.board.FutureWhite()
	case "analyze":
		a.board.Analyze(drawFn)

	// GTP commands
	case "gtp":
		if len(b.Args) > 0 {
			cmd := strings.Join(b.Args, " ")
			result := a.board.gtp.SendExtract(cmd)
			fmt.Println(result)
		}
	case "multigtp":
		if len(b.Args) > 0 {
			cmd := strings.Join(b.Args, " ")
			a.board.MultiGTP(cmd)
		}

	// Special functions
	case "clear":
		a.board.Clear()
	case "console":
		a.board.Console()
	case "liststones":
		a.board.ListStones()
	case "playguess":
		a.board.PlayGuess()

	// Game management
	case "newasblack":
		experimental := len(b.Args) > 0 && b.Args[0] == "experimental"
		a.board.Clear()
		a.board.NextLevel()
		if drawFn != nil {
			drawFn()
		}
		if experimental {
			a.board.MyPlay("white", drawFn)
		} else {
			go func() {
				move := a.board.gtp.SendExtract("genmove white")
				a.board.EngineCh <- engineResult{Color: White, Move: strings.TrimSpace(move)}
			}()
		}
	case "newaswhite":
		experimental := len(b.Args) > 0 && b.Args[0] == "experimental"
		a.board.Clear()
		a.board.NextLevel()
		if drawFn != nil {
			drawFn()
		}
		if experimental {
			a.board.MyPlay("black", drawFn)
		} else {
			go func() {
				move := a.board.gtp.SendExtract("genmove black")
				a.board.EngineCh <- engineResult{Color: Black, Move: strings.TrimSpace(move)}
			}()
		}
	case "status":
		a.board.Status()
	}
}
