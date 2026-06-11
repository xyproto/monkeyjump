package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// SGF loading

func (b *Board) LoadSGF(filename string) error {
	if filename != "" {
		b.filename = filename
	} else if b.filename != "" {
		filename = b.filename
	} else {
		return fmt.Errorf("no filename specified")
	}

	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}
	content := string(data)

	// Basic SGF validation
	if !strings.Contains(content, "(") || !strings.Contains(content, ")") {
		return fmt.Errorf("invalid SGF file: missing parentheses")
	}

	// Split on semicolons
	parts := strings.Split(content, ";")
	if len(parts) < 2 {
		return fmt.Errorf("invalid SGF: no nodes found")
	}

	// Clear the board
	b.Clear()

	// Parse settings from first node
	settings := parts[1]

	// SGF coordinates always use the alphabet including 'i' (a-s for 19x19).
	// The "withI" flag from the original code is for handling a non-standard
	// format. Standard SGF always uses 'i', so we default to true.
	withI := true

	// Place preset stones (AB = add black, AW = add white)
	b.placePresetStones(settings, "AB", Black, withI)
	b.placePresetStones(settings, "AW", White, withI)

	// Parse move sequence
	b.history = nil
	b.historyIndex = -1
	for _, part := range parts[2:] {
		part = strings.TrimSpace(part)
		// Remove trailing )
		part = strings.TrimRight(part, ") \t\n\r")
		move := b.extractSGFMove(part, withI)
		if move != "" {
			b.history = append(b.history, move)
		}
	}

	fmt.Printf("Loaded SGF: %s (%d moves)\n", filepath.Base(filename), len(b.history))
	return nil
}

func (b *Board) placePresetStones(settings, tag string, color StoneColor, withI bool) {
	idx := strings.Index(settings, tag+"[")
	if idx < 0 {
		return
	}
	rest := settings[idx+len(tag):]
	for strings.HasPrefix(rest, "[") {
		end := strings.Index(rest, "]")
		if end < 0 {
			break
		}
		coord := rest[1:end]
		if len(coord) >= 2 {
			x, y, err := b.SGFToNum(coord, withI)
			if err == nil {
				b.Stones[[2]int{x, y}] = color
				pos := b.NumToGTP(x, y)
				if color == Black {
					b.gtp.Send(fmt.Sprintf("play black %s", pos))
				} else {
					b.gtp.Send(fmt.Sprintf("play white %s", pos))
				}
			}
		}
		rest = rest[end+1:]
	}
}

func (b *Board) extractSGFMove(node string, withI bool) string {
	// Look for B[xx] or W[xx]
	for _, prefix := range []string{"B[", "W["} {
		idx := strings.Index(node, prefix)
		if idx < 0 {
			continue
		}
		rest := node[idx:]
		end := strings.Index(rest, "]")
		if end < 0 {
			continue
		}
		coord := rest[2:end]
		if len(coord) < 2 {
			continue
		}
		color := string(rest[0])
		x, y, err := b.SGFToNum(coord, withI)
		if err != nil {
			continue
		}
		gtpPos := b.NumToGTP(x, y)
		if gtpPos == "" {
			continue
		}
		return color + gtpPos
	}
	return ""
}
