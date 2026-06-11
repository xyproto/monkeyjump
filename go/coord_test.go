package main

import "testing"

func TestCoordConversion(t *testing.T) {
	gtp, err := NewGTP("gnugo --mode gtp")
	if err != nil {
		t.Skipf("gnugo not available: %v", err)
	}
	defer gtp.Close()

	b := NewBoard(9, gtp)

	// Test NumToGTP
	tests := []struct {
		x, y int
		want string
	}{
		{0, 0, "A9"}, // top-left
		{8, 8, "J1"}, // bottom-right
		{3, 4, "D5"}, // center-ish
		{0, 8, "A1"}, // bottom-left
		{8, 0, "J9"}, // top-right
	}
	for _, tc := range tests {
		got := b.NumToGTP(tc.x, tc.y)
		if got != tc.want {
			t.Errorf("NumToGTP(%d,%d) = %q, want %q", tc.x, tc.y, got, tc.want)
		}
	}

	// Test GTPToNum (round-trip)
	for _, tc := range tests {
		x, y, err := b.GTPToNum(tc.want)
		if err != nil {
			t.Errorf("GTPToNum(%q): %v", tc.want, err)
			continue
		}
		if x != tc.x || y != tc.y {
			t.Errorf("GTPToNum(%q) = (%d,%d), want (%d,%d)", tc.want, x, y, tc.x, tc.y)
		}
	}

	// Test SGFToNum (standard SGF uses 'i', a=0, b=1, ..., i=8)
	sgfTests := []struct {
		sgf  string
		x, y int
	}{
		{"aa", 0, 0}, // top-left
		{"ii", 8, 8}, // bottom-right
		{"de", 3, 4}, // D5 equivalent
		{"ai", 0, 8}, // bottom-left
		{"ia", 8, 0}, // top-right
	}
	for _, tc := range sgfTests {
		x, y, err := b.SGFToNum(tc.sgf, true)
		if err != nil {
			t.Errorf("SGFToNum(%q, true): %v", tc.sgf, err)
			continue
		}
		if x != tc.x || y != tc.y {
			t.Errorf("SGFToNum(%q, true) = (%d,%d), want (%d,%d)", tc.sgf, x, y, tc.x, tc.y)
		}
	}
}
