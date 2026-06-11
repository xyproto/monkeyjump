package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"strings"
)

const (
	defaultBoardSize = 9
	defaultWinSize   = 512
	version          = "1.0.0"
)

func init() {
	// SDL requires all calls to happen from the same OS thread.
	runtime.LockOSThread()
}

func main() {
	boardSize := defaultBoardSize
	winSize := defaultWinSize
	tiny := false
	var filename string

	for _, arg := range os.Args[1:] {
		switch arg {
		case "--help", "-h":
			fmt.Print(`Monkeyjump Go - Play Go against GNU Go

Usage:
  monkeyjump [OPTIONS] [BOARD_SIZE | SGF_FILE]

Options:
  --help, -h       Show this help message
  --version, -v    Show version information
  --tiny           Render at 1/10th size (tiny window)

Arguments:
  BOARD_SIZE       Board size (9, 13, or 19; default: 9)
  SGF_FILE         Load an SGF file

Keybindings:
  Arrow keys       Move cursor
  Space            Play black + GnuGo responds as white
  Tab              My play (analyzer/engine) as white
  Return           Ask GnuGo to play white
  m                Ask GnuGo to play black
  w/b              Place white/black stone (no engine response)
  u                Undo
  a/z              Pass (black/white)
  g                Show last move
  v                Show board (text in terminal)
  e/f              Estimate / final score
  n/p              Next / previous SGF move
  s                Save SGF
  l                Reload SGF
  i                Toggle illegal moves
  c                GTP console (interactive)
  o                Show future white moves
  t                Set time (5s main)
  x                Show move probabilities
  y                Play 100 auto-moves
  Numpad 1-9       Jump to board positions
  1-9, 0           Set GnuGo level (0 = level 10)
  F1               GnuGo engine info
  F2               Analyze (liberty-based move suggestion)
  F3               Show dragons
  F12              Save screenshot (BMP)
  Backspace        Clear board
  q / Escape       Quit

Mouse:
  Left click       Play black at cursor
  Middle click     New game as black
  Right click      Show status (score + level)

Configuration:
  conf/gnugocmd.conf       GTP engine command
  conf/theme.conf          Theme directory name
  conf/keybindings.conf    Keybinding reference
`)
			os.Exit(0)
		case "--version", "-v":
			fmt.Printf("monkeyjump %s\n", version)
			os.Exit(0)
		case "--tiny":
			winSize = 100
			tiny = true
		default:
			if n, err := strconv.Atoi(arg); err == nil {
				boardSize = n
			} else {
				filename = arg
			}
		}
	}

	if filename != "" {
		data, err := os.ReadFile(filename)
		if err == nil {
			s := string(data)
			switch {
			case strings.Contains(s, "SZ[9]"):
				boardSize = 9
			case strings.Contains(s, "SZ[13]"):
				boardSize = 13
			case strings.Contains(s, "SZ[19]"):
				boardSize = 19
			}
		}
	}

	app, err := NewApp(boardSize, filename, winSize, tiny)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	defer app.Destroy()

	app.Run()
}
