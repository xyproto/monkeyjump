package main

import (
	"fmt"
	"math"
	"path/filepath"
)

// BoardRenderer handles drawing the board, stones, and cursor.
type BoardRenderer struct {
	renderer  *Renderer
	boardTex  *Texture
	blackTex  *Texture
	whiteTex  *Texture
	boardSize int
	windowW   int
	windowH   int
	tiny      bool
}

func NewBoardRenderer(r *Renderer, boardSize, windowW, windowH int, themeDir string, tiny bool) (*BoardRenderer, error) {
	br := &BoardRenderer{
		renderer:  r,
		boardSize: boardSize,
		windowW:   windowW,
		windowH:   windowH,
		tiny:      tiny,
	}

	boardPath := filepath.Join(themeDir, "board.png")
	blackPath := filepath.Join(themeDir, "black.png")
	whitePath := filepath.Join(themeDir, "white.png")

	var err error
	br.boardTex, err = loadTexture(r, boardPath)
	if err != nil {
		return nil, fmt.Errorf("loading board texture: %w", err)
	}
	br.blackTex, err = loadTexture(r, blackPath)
	if err != nil {
		return nil, fmt.Errorf("loading black stone texture: %w", err)
	}
	br.whiteTex, err = loadTexture(r, whitePath)
	if err != nil {
		return nil, fmt.Errorf("loading white stone texture: %w", err)
	}

	return br, nil
}

func (br *BoardRenderer) Destroy() {
	if br.boardTex != nil {
		br.boardTex.Destroy()
	}
	if br.blackTex != nil {
		br.blackTex.Destroy()
	}
	if br.whiteTex != nil {
		br.whiteTex.Destroy()
	}
}

func (br *BoardRenderer) cellSize() (float32, float32) {
	cw := float32(br.windowW) / float32(br.boardSize)
	ch := float32(br.windowH) / float32(br.boardSize)
	return cw, ch
}

func (br *BoardRenderer) margin() float32 {
	cw, _ := br.cellSize()
	return cw / 2.0
}

func (br *BoardRenderer) Draw(board *Board) {
	r := br.renderer

	// Clear the background
	r.SetDrawColor(0, 0, 0, 255)
	r.Clear()

	// Draw board background
	if br.tiny {
		r.SetDrawColor(160, 160, 160, 255)
		r.FillRect(0, 0, float32(br.windowW), float32(br.windowH))
	} else {
		r.RenderTexture(br.boardTex, 0, 0, float32(br.windowW), float32(br.windowH))
	}

	cw, ch := br.cellSize()
	margin := br.margin()

	// Draw grid lines
	r.SetDrawColor(0, 0, 0, 255)
	for i := 0; i < br.boardSize; i++ {
		x := margin + float32(i)*cw
		y := margin + float32(i)*ch
		// Vertical line
		r.DrawLine(x, margin, x, float32(br.windowH)-margin)
		// Horizontal line
		r.DrawLine(margin, y, float32(br.windowW)-margin, y)
	}

	// Draw star points
	starPoints := br.getStarPoints()
	starRadius := cw * 0.1
	if starRadius < 1.0 {
		starRadius = 1.0
	}
	for _, sp := range starPoints {
		sx := margin + float32(sp[0])*cw
		sy := margin + float32(sp[1])*ch
		br.drawFilledCircle(sx, sy, starRadius)
	}

	// Draw stones
	stoneSize := cw * 0.9
	for pos, color := range board.Stones {
		sx := margin + float32(pos[0])*cw - stoneSize/2
		sy := margin + float32(pos[1])*ch - stoneSize/2
		if color == Black {
			r.RenderTexture(br.blackTex, sx, sy, stoneSize, stoneSize)
		} else if color == White {
			r.RenderTexture(br.whiteTex, sx, sy, stoneSize, stoneSize)
		}
	}

	// Draw cursor
	cx := margin + float32(board.CursorX)*cw
	cy := margin + float32(board.CursorY)*ch
	cursorSize := cw * 0.4
	r.SetDrawColor(64, 128, 255, 200)
	r.DrawRect(cx-cursorSize/2, cy-cursorSize/2, cursorSize, cursorSize)

	// Draw last move marker
	if board.hasLast {
		lx := margin + float32(board.lastMove[0])*cw
		ly := margin + float32(board.lastMove[1])*ch
		markerSize := cw * 0.2
		r.SetDrawColor(255, 0, 0, 200)
		r.FillRect(lx-markerSize/2, ly-markerSize/2, markerSize, markerSize)
	}

	r.Present()
}

func (br *BoardRenderer) drawFilledCircle(cx, cy, radius float32) {
	r := br.renderer
	for dy := -radius; dy <= radius; dy++ {
		dx := float32(math.Sqrt(float64(radius*radius - dy*dy)))
		r.DrawLine(cx-dx, cy+dy, cx+dx, cy+dy)
	}
}

func (br *BoardRenderer) getStarPoints() [][2]int {
	var points [][2]int
	switch br.boardSize {
	case 19:
		coords := []int{3, 9, 15}
		for _, x := range coords {
			for _, y := range coords {
				points = append(points, [2]int{x, y})
			}
		}
	case 13:
		coords := []int{3, 6, 9}
		for _, x := range coords {
			for _, y := range coords {
				points = append(points, [2]int{x, y})
			}
		}
	case 9:
		points = append(points, [2]int{2, 2}, [2]int{6, 2}, [2]int{4, 4}, [2]int{2, 6}, [2]int{6, 6})
	}
	return points
}

// ScreenToBoard converts pixel coordinates to board coordinates.
func (br *BoardRenderer) ScreenToBoard(mx, my float32) (int, int) {
	cw, ch := br.cellSize()
	margin := br.margin()
	x := int((mx - margin + cw/2) / cw)
	y := int((my - margin + ch/2) / ch)
	if x < 0 {
		x = 0
	}
	if x >= br.boardSize {
		x = br.boardSize - 1
	}
	if y < 0 {
		y = 0
	}
	if y >= br.boardSize {
		y = br.boardSize - 1
	}
	return x, y
}
