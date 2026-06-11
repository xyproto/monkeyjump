package main

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// Analyzer provides move suggestions using liberty-based heuristics with blur algorithms.
type Analyzer struct {
	board *Board
	size  int
	black [][2]int
	white [][2]int
	empty [][2]int
}

func NewAnalyzer(board *Board) *Analyzer {
	a := &Analyzer{board: board, size: board.Size}
	a.classifyPositions()
	return a
}

func (a *Analyzer) classifyPositions() {
	a.black = nil
	a.white = nil
	a.empty = nil
	for x := 0; x < a.size; x++ {
		for y := 0; y < a.size; y++ {
			pos := [2]int{x, y}
			switch a.board.Stones[pos] {
			case Black:
				a.black = append(a.black, pos)
			case White:
				a.white = append(a.white, pos)
			default:
				a.empty = append(a.empty, pos)
			}
		}
	}
}

func (a *Analyzer) hasSpace(pos [2]int) bool {
	if _, ok := a.board.Stones[pos]; ok {
		return false
	}
	for _, dx := range []int{1, -1} {
		for _, dy := range []int{1, -1} {
			check := [2]int{pos[0] + dx, pos[1] + dy}
			if c, ok := a.board.Stones[check]; ok && c != Empty {
				return false
			}
		}
	}
	return true
}

func (a *Analyzer) findFriends(pos [2]int) float64 {
	friends := 0.0
	offsets := []int{1, -1, 2, -2, 3, -3, 4, -4}
	for _, dx := range offsets {
		for _, dy := range offsets {
			check := [2]int{pos[0] + dx, pos[1] + dy}
			if a.board.Stones[check] == Black {
				if math.Abs(float64(dx)) > 2 || math.Abs(float64(dy)) > 2 {
					friends += 0.5
				} else {
					friends++
				}
			}
		}
	}
	return friends
}

func (a *Analyzer) findEnemies(pos [2]int) float64 {
	enemies := 0.0
	offsets := []int{1, -1, 2, -2, 3, -3, 4, -4}
	for _, dx := range offsets {
		for _, dy := range offsets {
			check := [2]int{pos[0] + dx, pos[1] + dy}
			if a.board.Stones[check] == White {
				if math.Abs(float64(dx)) > 2 || math.Abs(float64(dy)) > 2 {
					enemies += 0.5
				} else {
					enemies++
				}
			}
		}
	}
	return enemies
}

// Surface is a simple 2D grid of RGB values.
type Surface struct {
	w    int
	data [][3]float64
}

func newSurface(w int) *Surface {
	return &Surface{w: w, data: make([][3]float64, w*w)}
}

func (s *Surface) getAt(x, y int) [3]float64 {
	if x < 0 || x >= s.w || y < 0 || y >= s.w {
		return [3]float64{0, 0, 0}
	}
	return s.data[y*s.w+x]
}

func (s *Surface) setAt(x, y int, c [3]float64) {
	if x >= 0 && x < s.w && y >= 0 && y < s.w {
		s.data[y*s.w+x] = c
	}
}

type posSet map[[2]int]bool

func makeSet(positions [][2]int) posSet {
	s := make(posSet, len(positions))
	for _, p := range positions {
		s[p] = true
	}
	return s
}

func (a *Analyzer) getLiberties(pos [2]int) int {
	gtpPos := a.board.NumToGTP(pos[0], pos[1])
	resp := a.board.gtp.SendExtract(fmt.Sprintf("countlib %s", gtpPos))
	n, err := strconv.Atoi(strings.TrimSpace(resp))
	if err != nil {
		return 0
	}
	return n
}

func (a *Analyzer) blackLiberties() (*Surface, posSet) {
	surface := newSurface(a.size)
	maxLib := 1
	liberties := make(map[[2]int]int)
	for _, pos := range a.black {
		lib := a.getLiberties(pos)
		liberties[pos] = lib
		if lib > maxLib {
			maxLib = lib
		}
	}
	for pos, lib := range liberties {
		r := (float64(lib) / float64(maxLib)) * 255.0
		surface.setAt(pos[0], pos[1], [3]float64{r, 0, 0})
	}
	return surface, makeSet(a.white)
}

func (a *Analyzer) whiteLiberties() (*Surface, posSet) {
	surface := newSurface(a.size)
	maxLib := 1
	liberties := make(map[[2]int]int)
	for _, pos := range a.white {
		lib := a.getLiberties(pos)
		liberties[pos] = lib
		if lib > maxLib {
			maxLib = lib
		}
	}
	for pos, lib := range liberties {
		b := (float64(lib) / float64(maxLib)) * 255.0
		surface.setAt(pos[0], pos[1], [3]float64{0, 0, b})
	}
	return surface, makeSet(a.black)
}

func (a *Analyzer) voidLiberties() (*Surface, posSet) {
	surface := newSurface(a.size)
	occupied := make(posSet)
	for _, p := range a.black {
		occupied[p] = true
	}
	for _, p := range a.white {
		occupied[p] = true
	}

	for _, pos := range a.empty {
		liberties := 4
		neighbors := [][2]int{
			{pos[0] - 1, pos[1]}, {pos[0] + 1, pos[1]},
			{pos[0], pos[1] - 1}, {pos[0], pos[1] + 1},
		}
		for _, n := range neighbors {
			if n[0] < 0 || n[0] >= a.size || n[1] < 0 || n[1] >= a.size {
				liberties--
			} else if occupied[n] {
				liberties--
			}
		}
		g := (float64(liberties) / 4.0) * 255.0
		surface.setAt(pos[0], pos[1], [3]float64{0, g, 0})
	}
	return surface, makeSet(a.black)
}

func (a *Analyzer) blur4(surface *Surface, exclude posSet, divnum float64) *Surface {
	w := a.size
	result := newSurface(w)
	for x := range w {
		for y := range w {
			if exclude[[2]int{x, y}] {
				continue
			}
			var r, g, b float64
			for _, n := range [][2]int{{x, y}, {x - 1, y}, {x + 1, y}, {x, y - 1}, {x, y + 1}} {
				if exclude[n] || n[0] < 0 || n[0] >= w || n[1] < 0 || n[1] >= w {
					continue
				}
				c := surface.getAt(n[0], n[1])
				r += c[0]
				g += c[1]
				b += c[2]
			}
			result.setAt(x, y, [3]float64{r / divnum, g / divnum, b / divnum})
		}
	}
	return result
}

func (a *Analyzer) combine(red, green, blue *Surface) *Surface {
	w := a.size
	result := newSurface(w)
	for x := range w {
		for y := range w {
			r := red.getAt(x, y)[0]
			g := green.getAt(x, y)[1]
			b := blue.getAt(x, y)[2]
			result.setAt(x, y, [3]float64{r, g, b})
		}
	}
	return result
}

func (a *Analyzer) blurmore(surface *Surface, repeat int, divnum float64) (*Surface, *[2]int) {
	const (
		origBias   = 2.4
		cornerBias = 1.0
		spaceBias  = 7.9
		friendBias = 1.5
		enemyBias  = 0.9
		threshold  = 590.0
		sideBias   = 20.0
	)

	w := a.size
	var gpos *[2]int
	var oldGpos *[2]int
	bestcount := 0

	for range repeat {
		surface = a.blur4(surface, nil, divnum)
		if gpos != nil {
			oldGpos = gpos
		}
		greenest := 0.0
		gpos = nil
		oldBestcount := bestcount
		bestcount = 0

		for x := range w {
			for y := range w {
				c := surface.getAt(x, y)
				g := (255.0 - c[0]*-0.1 + c[1]*0.8 + (255.0 - c[2]*-0.1)) / 3.0
				g *= origBias

				if cornerBias != 0 {
					center := float64(w) / 2.0
					dist := math.Sqrt(math.Pow(center-float64(x), 2) + math.Pow(center-float64(y), 2))
					g += dist * cornerBias
				}
				if sideBias != 0 {
					center := float64(w) / 2.0
					horiz := math.Abs(center-float64(x)) / center
					verti := math.Abs(center-float64(y)) / center
					g += math.Max(horiz, verti) * sideBias
				}
				if spaceBias != 0 {
					if a.hasSpace([2]int{x, y}) {
						g += spaceBias
					} else {
						g -= spaceBias
					}
				}
				if friendBias != 0 {
					friends := a.findFriends([2]int{x, y})
					switch {
					case friends == 0:
						g -= friendBias * 5
					case friends == 1:
						g += friendBias * 5
					case friends == 2:
						g += friendBias * 2
					case friends == 3:
						g += friendBias
					case friends > 3:
						g -= friendBias * friends
					}
				}
				if enemyBias != 0 {
					enemies := a.findEnemies([2]int{x, y})
					g -= math.Pow(enemyBias, enemies)
				}

				if g > greenest {
					greenest = g
					pos := [2]int{x, y}
					gpos = &pos
				} else if g == greenest {
					bestcount++
				}
			}
		}

		value := greenest / float64(bestcount+1)
		if gpos != nil {
			fmt.Printf("gpos (%d,%d) value %.1f\n", gpos[0], gpos[1], value)
		}

		if value < threshold {
			if oldGpos == nil {
				continue
			}
			gpos = oldGpos
			bestcount = oldBestcount
			fmt.Printf("Finished! GPOS (%d,%d) VALUE %.1f BESTCOUNT %d\n", gpos[0], gpos[1], greenest, bestcount)
			return surface, gpos
		}
	}
	return surface, gpos
}

// Analyze runs the full analysis and plays the suggested move.
func (b *Board) Analyze(drawFn func()) {
	a := NewAnalyzer(b)

	redSurface, redExclude := a.blackLiberties()
	greenSurface, greenExclude := a.voidLiberties()
	blueSurface, _ := a.whiteLiberties()

	redBlur := a.blur4(redSurface, redExclude, 5.0)
	greenBlur := a.blur4(greenSurface, greenExclude, 5.0)
	blueBlur := a.blur4(blueSurface, makeSet(a.black), 5.0)

	stoneBlur := a.combine(redBlur, greenBlur, blueBlur)
	_, pos := a.blurmore(stoneBlur, 100, 5.0)

	if pos != nil {
		gtpPos := b.NumToGTP(pos[0], pos[1])
		fmt.Printf("Analyzer suggests: %s (%d,%d)\n", gtpPos, pos[0], pos[1])
		resp := b.gtp.Send(fmt.Sprintf("play black %s", gtpPos))
		if !strings.HasPrefix(resp, "?") {
			b.Stones[*pos] = Black
			b.lastMove = *pos
			b.hasLast = true
			b.checkCaptures()
			if drawFn != nil {
				drawFn()
			}
			b.GnuGoWhite()
		}
	} else {
		fmt.Println("Analyzer: no suggestion found, using GnuGo")
		b.GnuGoBlack()
	}
}

// MyPlay uses the analyzer for early game, GnuGo for later moves.
func (b *Board) MyPlay(color string, drawFn func()) {
	moveNum := len(b.Stones)
	if moveNum < 30 {
		a := NewAnalyzer(b)
		redSurface, redExclude := a.blackLiberties()
		greenSurface, greenExclude := a.voidLiberties()
		blueSurface, _ := a.whiteLiberties()
		redBlur := a.blur4(redSurface, redExclude, 5.0)
		greenBlur := a.blur4(greenSurface, greenExclude, 5.0)
		blueBlur := a.blur4(blueSurface, makeSet(a.black), 5.0)
		stoneBlur := a.combine(redBlur, greenBlur, blueBlur)
		_, pos := a.blurmore(stoneBlur, 30, 5.0)

		if pos != nil {
			if _, occupied := b.Stones[*pos]; !occupied {
				gtpPos := b.NumToGTP(pos[0], pos[1])
				fmt.Printf("My move: %s\n", gtpPos)
				playColor := "black"
				stoneColor := Black
				if color == "white" || color == "W" {
					playColor = "white"
					stoneColor = White
				}
				resp := b.gtp.Send(fmt.Sprintf("play %s %s", playColor, gtpPos))
				if !strings.HasPrefix(resp, "?") {
					b.Stones[*pos] = stoneColor
					b.lastMove = *pos
					b.hasLast = true
					b.checkCaptures()
					if drawFn != nil {
						drawFn()
					}
					return
				}
			}
		}
	}

	// Fall back to GnuGo
	if color == "white" || color == "W" {
		b.GnuGoWhite()
	} else {
		b.GnuGoBlack()
	}
}
