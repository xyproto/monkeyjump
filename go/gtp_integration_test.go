package main

import (
	"strings"
	"testing"
)

func TestGTPParsing(t *testing.T) {
	gtp, err := NewGTP("gnugo --mode gtp")
	if err != nil {
		t.Skipf("gnugo not available: %v", err)
	}
	defer gtp.Close()

	// Acknowledgements should return empty string
	resp := gtp.SendExtract("boardsize 9")
	if resp != "" {
		t.Errorf("boardsize: expected empty, got %q", resp)
	}

	resp = gtp.SendExtract("clear_board")
	if resp != "" {
		t.Errorf("clear_board: expected empty, got %q", resp)
	}

	// Play should return empty (acknowledgement)
	resp = gtp.SendExtract("play black D5")
	if resp != "" {
		t.Errorf("play black D5: expected empty, got %q", resp)
	}

	// genmove should return a position
	resp = gtp.SendExtract("genmove white")
	if len(resp) < 2 {
		t.Errorf("genmove white: expected position, got %q", resp)
	}

	// captures should return a number
	resp = gtp.SendExtract("captures black")
	if resp != "0" {
		t.Errorf("captures black: expected '0', got %q", resp)
	}

	// list_stones should return positions
	resp = gtp.SendExtract("list_stones black")
	if !strings.Contains(resp, "D5") {
		t.Errorf("list_stones black: expected to contain D5, got %q", resp)
	}

	// showboard should be multi-line
	resp = gtp.SendExtract("showboard")
	lines := strings.Split(resp, "\n")
	if len(lines) < 5 {
		t.Errorf("showboard: expected many lines, got %d: %q", len(lines), resp)
	}

	// estimate_score should return a score
	resp = gtp.SendExtract("estimate_score")
	if !strings.Contains(resp, "+") && !strings.Contains(resp, "0") {
		t.Errorf("estimate_score: unexpected %q", resp)
	}
}
