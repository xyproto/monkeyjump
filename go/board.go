package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// Stone color
type StoneColor int

const (
	Empty StoneColor = iota
	Black
	White
)

// engineResult is sent from the genmove goroutine back to the main thread.
type engineResult struct {
	Color StoneColor
	Move  string // GTP move string (e.g. "D4") or "PASS" or "resign"
}

// Board manages the Go board state and communicates with GnuGo.
type Board struct {
	Size       int
	Stones     map[[2]int]StoneColor
	CursorX    int
	CursorY    int
	oldCursorX int
	oldCursorY int
	gtp        *GTP
	bCaptures  int
	wCaptures  int
	lastMove   [2]int
	hasLast    bool
	level      int
	illegalOK  bool
	lastPlayed string // "B" or "W"
	EngineCh   chan engineResult
	// SGF replay
	history      []string // e.g. "BD4", "WQ16"
	historyIndex int
	guessCounter int
	filename     string
}

// Letters used for Go coordinates (skipping 'I')
var letters = []byte("ABCDEFGHJKLMNOPQRST")

func NewBoard(size int, gtp *GTP) *Board {
	b := &Board{
		Size:         size,
		Stones:       make(map[[2]int]StoneColor),
		gtp:          gtp,
		level:        9,
		historyIndex: -1,
		lastPlayed:   "W",
		EngineCh:     make(chan engineResult, 1),
	}
	gtp.Send(fmt.Sprintf("boardsize %d", size))
	gtp.Send("clear_board")
	b.CursorX = size / 2
	b.CursorY = size / 2
	b.oldCursorX = b.CursorX
	b.oldCursorY = b.CursorY
	return b
}

// NumToGTP converts numeric board coords (0-based) to GTP format like "D4".
func (b *Board) NumToGTP(x, y int) string {
	if x < 0 || x >= b.Size || y < 0 || y >= b.Size {
		return ""
	}
	letter := letters[x]
	number := b.Size - y
	return fmt.Sprintf("%c%d", letter, number)
}

// GTPToNum converts GTP position like "D4" to numeric coords (0-based).
func (b *Board) GTPToNum(pos string) (int, int, error) {
	pos = strings.TrimSpace(strings.ToUpper(pos))
	if len(pos) < 2 {
		return 0, 0, fmt.Errorf("invalid position: %s", pos)
	}
	letter := pos[0]
	x := -1
	for i, l := range letters[:b.Size] {
		if l == letter {
			x = i
			break
		}
	}
	if x < 0 {
		return 0, 0, fmt.Errorf("invalid column: %c", letter)
	}
	num, err := strconv.Atoi(pos[1:])
	if err != nil {
		return 0, 0, fmt.Errorf("invalid row: %s", pos[1:])
	}
	y := b.Size - num
	if y < 0 || y >= b.Size {
		return 0, 0, fmt.Errorf("row out of range: %d", num)
	}
	return x, y, nil
}

// SGFToNum converts SGF coordinates like "dp" to numeric coords.
// In standard SGF, 'a'=0, 'b'=1, etc. The y-axis goes top to bottom.
// When withI is true, the alphabet includes 'i'. When false, 'i' is skipped
// (matching GTP column convention), but for SGF this is non-standard.
func (b *Board) SGFToNum(sgf string, withI bool) (int, int, error) {
	if len(sgf) < 2 {
		return 0, 0, fmt.Errorf("invalid SGF coord: %s", sgf)
	}
	var alpha string
	if withI {
		alpha = "abcdefghijklmnopqrs"
	} else {
		alpha = "abcdefghjklmnopqrst"
	}
	x := strings.IndexByte(alpha, sgf[0])
	y := strings.IndexByte(alpha, sgf[1])
	if x < 0 || y < 0 {
		return 0, 0, fmt.Errorf("invalid SGF coord: %s", sgf)
	}
	if x >= b.Size || y >= b.Size {
		return 0, 0, fmt.Errorf("SGF coord out of range: %s", sgf)
	}
	return x, y, nil
}

func (b *Board) MoveCursor(dx, dy int) {
	b.oldCursorX = b.CursorX
	b.oldCursorY = b.CursorY
	b.CursorX += dx
	if b.CursorX < 0 {
		b.CursorX = b.Size - 1
	} else if b.CursorX >= b.Size {
		b.CursorX = 0
	}
	b.CursorY += dy
	if b.CursorY < 0 {
		b.CursorY = b.Size - 1
	} else if b.CursorY >= b.Size {
		b.CursorY = 0
	}
}

// PlayBlackThenEngine places a black stone and asks GnuGo to respond as white.
// The player's stone is placed synchronously; genmove runs in a goroutine so
// the event loop stays responsive. The result arrives via EngineCh.
func (b *Board) PlayBlackThenEngine(drawFn func()) {
	pos := b.NumToGTP(b.CursorX, b.CursorY)
	if pos == "" {
		return
	}
	if _, occupied := b.Stones[[2]int{b.CursorX, b.CursorY}]; occupied {
		return
	}
	// Don't allow moves while engine is thinking
	if b.EngineThinking() {
		return
	}
	resp := b.gtp.Send(fmt.Sprintf("play black %s", pos))
	if strings.Contains(resp, "illegal") || strings.HasPrefix(resp, "?") {
		if !b.illegalOK {
			fmt.Println("Illegal move:", pos)
			return
		}
		fmt.Println("Illegal move (forced):", pos)
	}
	b.Stones[[2]int{b.CursorX, b.CursorY}] = Black
	b.lastMove = [2]int{b.CursorX, b.CursorY}
	b.hasLast = true
	b.checkCaptures()
	if drawFn != nil {
		drawFn()
	}
	// Ask engine to respond asynchronously
	go func() {
		move := b.gtp.SendExtract("genmove white")
		b.EngineCh <- engineResult{Color: White, Move: strings.TrimSpace(move)}
	}()
}

// PlayWhiteThenEngine places a white stone and asks GnuGo to respond as black.
func (b *Board) PlayWhiteThenEngine(drawFn func()) {
	pos := b.NumToGTP(b.CursorX, b.CursorY)
	if pos == "" {
		return
	}
	if _, occupied := b.Stones[[2]int{b.CursorX, b.CursorY}]; occupied {
		return
	}
	if b.EngineThinking() {
		return
	}
	resp := b.gtp.Send(fmt.Sprintf("play white %s", pos))
	if strings.Contains(resp, "illegal") || strings.HasPrefix(resp, "?") {
		if !b.illegalOK {
			fmt.Println("Illegal move:", pos)
			return
		}
	}
	b.Stones[[2]int{b.CursorX, b.CursorY}] = White
	b.lastMove = [2]int{b.CursorX, b.CursorY}
	b.hasLast = true
	b.checkCaptures()
	if drawFn != nil {
		drawFn()
	}
	go func() {
		move := b.gtp.SendExtract("genmove black")
		b.EngineCh <- engineResult{Color: Black, Move: strings.TrimSpace(move)}
	}()
}

// EngineThinking returns true if the GTP engine is currently processing a command.
func (b *Board) EngineThinking() bool {
	return !b.gtp.Available()
}

// ApplyEngineMove checks the channel for a completed engine move and applies it.
// Returns true if a move was applied (caller should redraw).
func (b *Board) ApplyEngineMove() bool {
	select {
	case result := <-b.EngineCh:
		if result.Move == "PASS" || result.Move == "resign" {
			fmt.Printf("GnuGo (%v): %s\n", result.Color, result.Move)
			return true
		}
		b.placeGTPMove(result.Color, result.Move)
		b.checkCaptures()
		return true
	default:
		return false
	}
}

// ToggleBlack places a black stone at cursor (no engine response).
func (b *Board) ToggleBlack() bool {
	if b.EngineThinking() {
		return false
	}
	pos := b.NumToGTP(b.CursorX, b.CursorY)
	resp := b.gtp.Send(fmt.Sprintf("play black %s", pos))
	if (strings.Contains(resp, "illegal") || strings.HasPrefix(resp, "?")) && !b.illegalOK {
		return false
	}
	b.Stones[[2]int{b.CursorX, b.CursorY}] = Black
	b.lastMove = [2]int{b.CursorX, b.CursorY}
	b.hasLast = true
	b.checkCaptures()
	return true
}

// ToggleWhite places a white stone at cursor (no engine response).
func (b *Board) ToggleWhite() bool {
	if b.EngineThinking() {
		return false
	}
	pos := b.NumToGTP(b.CursorX, b.CursorY)
	resp := b.gtp.Send(fmt.Sprintf("play white %s", pos))
	if (strings.Contains(resp, "illegal") || strings.HasPrefix(resp, "?")) && !b.illegalOK {
		return false
	}
	b.Stones[[2]int{b.CursorX, b.CursorY}] = White
	b.lastMove = [2]int{b.CursorX, b.CursorY}
	b.hasLast = true
	b.checkCaptures()
	return true
}

func (b *Board) GnuGoWhite() {
	move := b.gtp.SendExtract("genmove white")
	move = strings.TrimSpace(move)
	if move == "PASS" || move == "resign" {
		fmt.Println("GnuGo (white):", move)
		return
	}
	b.placeGTPMove(White, move)
}

func (b *Board) GnuGoBlack() {
	move := b.gtp.SendExtract("genmove black")
	move = strings.TrimSpace(move)
	if move == "PASS" || move == "resign" {
		fmt.Println("GnuGo (black):", move)
		return
	}
	b.placeGTPMove(Black, move)
}

func (b *Board) placeGTPMove(color StoneColor, pos string) {
	x, y, err := b.GTPToNum(pos)
	if err != nil {
		fmt.Printf("Error parsing GTP move %q: %v\n", pos, err)
		return
	}
	b.Stones[[2]int{x, y}] = color
	b.lastMove = [2]int{x, y}
	b.hasLast = true
	b.checkCaptures()
	fmt.Printf("GnuGo plays: %s (%d,%d)\n", pos, x, y)
}

// checkCaptures queries the engine for captures and resyncs the board if any occurred.
func (b *Board) checkCaptures() {
	bResp := b.gtp.SendExtract("captures black")
	wResp := b.gtp.SendExtract("captures white")
	bc, _ := strconv.Atoi(strings.TrimSpace(bResp))
	wc, _ := strconv.Atoi(strings.TrimSpace(wResp))
	if bc != b.bCaptures || wc != b.wCaptures {
		b.bCaptures = bc
		b.wCaptures = wc
		b.syncFromEngine()
	}
}

// syncFromEngine reloads the board state from GnuGo.
func (b *Board) syncFromEngine() {
	b.Stones = make(map[[2]int]StoneColor)
	blackStones := b.gtp.SendExtract("list_stones black")
	whiteStones := b.gtp.SendExtract("list_stones white")
	for pos := range strings.FieldsSeq(blackStones) {
		if x, y, err := b.GTPToNum(pos); err == nil {
			b.Stones[[2]int{x, y}] = Black
		}
	}
	for pos := range strings.FieldsSeq(whiteStones) {
		if x, y, err := b.GTPToNum(pos); err == nil {
			b.Stones[[2]int{x, y}] = White
		}
	}
}

func (b *Board) Undo() {
	if b.EngineThinking() {
		return
	}
	// Undo the engine's last move and the player's last move
	resp := b.gtp.Send("undo")
	if strings.Contains(resp, "cannot") {
		return
	}
	// Try to undo the player's move too (undo a full turn)
	resp2 := b.gtp.Send("undo")
	if strings.Contains(resp2, "cannot") {
		// Only one move to undo, that's fine
	}
	b.syncFromEngine()
}

func (b *Board) PassBlack() {
	if b.EngineThinking() {
		return
	}
	b.gtp.Send("play black PASS")
	go func() {
		move := b.gtp.SendExtract("genmove white")
		b.EngineCh <- engineResult{Color: White, Move: strings.TrimSpace(move)}
	}()
}

func (b *Board) PassWhite() {
	if b.EngineThinking() {
		return
	}
	b.gtp.Send("play white PASS")
	go func() {
		move := b.gtp.SendExtract("genmove black")
		b.EngineCh <- engineResult{Color: Black, Move: strings.TrimSpace(move)}
	}()
}

func (b *Board) Clear() {
	b.Stones = make(map[[2]int]StoneColor)
	b.gtp.Send("clear_board")
	b.bCaptures = 0
	b.wCaptures = 0
	b.history = nil
	b.historyIndex = -1
	b.CursorX = b.Size / 2
	b.CursorY = b.Size / 2
}

func (b *Board) ShowBoard() {
	b.gtp.Send("showboard")
}

func (b *Board) EstimateScore() string {
	return b.gtp.SendExtract("estimate_score")
}

func (b *Board) FinalScore() string {
	return b.gtp.SendExtract("final_score")
}

func (b *Board) SetLevel(level int) {
	b.level = level
	b.gtp.Send(fmt.Sprintf("level %d", level))
}

func (b *Board) ShowLastMove() {
	if b.hasLast {
		b.CursorX = b.lastMove[0]
		b.CursorY = b.lastMove[1]
	}
}

func (b *Board) ToggleIllegal() {
	b.illegalOK = !b.illegalOK
	if b.illegalOK {
		fmt.Println("Illegal moves: allowed")
	} else {
		fmt.Println("Illegal moves: blocked")
	}
}

func (b *Board) SaveSGF(filename string) {
	b.gtp.Send(fmt.Sprintf("printsgf %s", filename))
	fmt.Println("Saved:", filename)
}

// NextMove advances in the SGF history.
func (b *Board) NextMove() {
	if len(b.history) == 0 {
		return
	}
	b.historyIndex++
	if b.historyIndex >= len(b.history) {
		b.historyIndex = len(b.history) - 1
		return
	}
	colorPos := b.history[b.historyIndex]
	if len(colorPos) < 2 {
		return
	}
	color := string(colorPos[0])
	pos := colorPos[1:]
	if color == "B" {
		b.gtp.Send(fmt.Sprintf("play black %s", pos))
	} else {
		b.gtp.Send(fmt.Sprintf("play white %s", pos))
	}
	x, y, err := b.GTPToNum(pos)
	if err == nil {
		if color == "B" {
			b.Stones[[2]int{x, y}] = Black
		} else {
			b.Stones[[2]int{x, y}] = White
		}
		b.CursorX = x
		b.CursorY = y
		b.lastMove = [2]int{x, y}
		b.hasLast = true
	}
	b.checkCaptures()
}

// PreviousMove goes back in the SGF history.
func (b *Board) PreviousMove() {
	if b.historyIndex < 0 {
		return
	}
	b.historyIndex--
	b.gtp.Send("undo")
	b.syncFromEngine()
}

// JumpPos jumps the cursor to a specific board position (1-based).
func (b *Board) JumpPos(x, y int) {
	bx := x - 1
	by := y - 1
	if bx < 0 {
		bx = 0
	}
	if bx >= b.Size {
		bx = b.Size - 1
	}
	if by < 0 {
		by = 0
	}
	if by >= b.Size {
		by = b.Size - 1
	}
	b.CursorX = bx
	b.CursorY = by
}

// TimeSettings sets time controls.
func (b *Board) TimeSettings(mainTime, byoYomiTime, byoYomiStones int) {
	b.gtp.Send(fmt.Sprintf("time_settings %d %d %d", mainTime, byoYomiTime, byoYomiStones))
	fmt.Printf("Time settings: main=%d byo_yomi=%d stones=%d\n", mainTime, byoYomiTime, byoYomiStones)
}

// NextLevel cycles through GnuGo difficulty levels.
func (b *Board) NextLevel() {
	b.level += 3
	if b.level > 9 {
		b.level = 0
	}
	b.SetLevel(b.level)
	fmt.Println("Level:", b.level)
}

// FutureWhite shows top engine moves as gray markers.
func (b *Board) FutureWhite() {
	// Generate a move, get top candidates, then undo
	b.gtp.Send("genmove white")
	topMoves := b.gtp.SendExtract("top_moves_white")
	b.gtp.Send("undo")

	// Parse positions (format: "D4 0.85 E5 0.72 ...")
	fields := strings.Fields(topMoves)
	for i := 0; i < len(fields); i += 2 {
		pos := fields[i]
		x, y, err := b.GTPToNum(pos)
		if err == nil {
			// Mark with a special "gray" stone to indicate suggestion
			if _, exists := b.Stones[[2]int{x, y}]; !exists {
				b.Stones[[2]int{x, y}] = Empty // placeholder for marker
			}
		}
	}
	// Actually just print them; rendering markers would need a new stone type
	fmt.Println("Top moves (white):", topMoves)
}

// Play100Moves plays 100 moves automatically (black via engine, white via engine).
func (b *Board) Play100Moves(drawFn func()) {
	for i := range 100 {
		b.GnuGoBlack()
		if drawFn != nil {
			drawFn()
		}
		score := b.gtp.SendExtract("estimate_score")
		fmt.Printf("Move %d: %s\n", i*2+1, score)
		b.GnuGoWhite()
		if drawFn != nil {
			drawFn()
		}
	}
	fmt.Println("Done with 100 moves")
}

// MultiGTP sends a command and prints multi-line results.
func (b *Board) MultiGTP(cmd string) {
	resp := b.gtp.SendExtract(cmd)
	fmt.Println(resp)
}

// NewAsBlack clears the board, cycles level, and has GnuGo play first as white.
func (b *Board) NewAsBlack(drawFn func()) {
	b.Clear()
	b.NextLevel()
	if drawFn != nil {
		drawFn()
	}
	go func() {
		move := b.gtp.SendExtract("genmove white")
		b.EngineCh <- engineResult{Color: White, Move: strings.TrimSpace(move)}
	}()
}

// NewAsWhite clears the board, cycles level, and has GnuGo play first as black.
func (b *Board) NewAsWhite(drawFn func()) {
	b.Clear()
	b.NextLevel()
	if drawFn != nil {
		drawFn()
	}
	go func() {
		move := b.gtp.SendExtract("genmove black")
		b.EngineCh <- engineResult{Color: Black, Move: strings.TrimSpace(move)}
	}()
}

// ListStones prints all stones on the board.
func (b *Board) ListStones() {
	fmt.Println("Black:", b.gtp.SendExtract("list_stones black"))
	fmt.Println("White:", b.gtp.SendExtract("list_stones white"))
}

// NextOrLoad advances in SGF history, or reloads the file if no history.
func (b *Board) NextOrLoad() {
	if len(b.history) > 0 {
		b.NextMove()
	} else if b.filename != "" {
		b.LoadSGF(b.filename)
	}
}

// GuessOrPlace either guesses the next SGF move or alternates stone placement.
func (b *Board) GuessOrPlace() {
	if len(b.history) > 0 {
		b.PlayGuess()
	} else {
		if b.lastPlayed == "B" {
			if b.ToggleWhite() {
				b.lastPlayed = "W"
			}
		} else {
			if b.ToggleBlack() {
				b.lastPlayed = "B"
			}
		}
	}
}

// PlayGuess checks if the cursor matches the next SGF move.
func (b *Board) PlayGuess() {
	if b.historyIndex+1 >= len(b.history) {
		return
	}
	colorPos := b.history[b.historyIndex+1]
	if len(colorPos) < 2 {
		return
	}
	expectedPos := colorPos[1:]
	cursorPos := b.NumToGTP(b.CursorX, b.CursorY)
	if cursorPos == expectedPos {
		if b.guessCounter > 1 {
			fmt.Printf("Guessed the next move in %d clicks!\n", b.guessCounter)
		}
		b.guessCounter = 0
		b.NextMove()
	} else {
		b.guessCounter++
	}
}

// Status shows the last move, score estimate, and level.
func (b *Board) Status() {
	b.ShowLastMove()
	score := b.EstimateScore()
	fmt.Printf("Score: %s | Level: %d\n", score, b.level)
}

// GnuGoInfo prints engine name, version, and settings.
func (b *Board) GnuGoInfo() {
	fmt.Println("Name:", b.gtp.SendExtract("name"))
	fmt.Println("Version:", b.gtp.SendExtract("version"))
	fmt.Println("Protocol:", b.gtp.SendExtract("protocol_version"))
	fmt.Println("Board size:", b.gtp.SendExtract("query_boardsize"))
	fmt.Println("Komi:", b.gtp.SendExtract("get_komi"))
}

// Console enters an interactive GTP command mode reading from stdin.
func (b *Board) Console() {
	fmt.Println("\nGTP Console (type 'exit' or 'quit' to return to game)")
	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("# ")
		if !scanner.Scan() {
			break
		}
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		if line == "exit" || line == "quit" {
			fmt.Println("Done with console.")
			break
		}
		resp := b.gtp.SendExtract(line)
		if resp != "" {
			fmt.Println(resp)
		}
	}
	b.syncFromEngine()
}
