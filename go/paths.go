package main

import (
	"os"
	"path/filepath"
)

// dataDir is the resolved base directory for themes and config.
// Set at startup by resolveDataDir().
var dataDir string

// resolveDataDir finds the data directory containing themes/ and conf/.
// Search order:
//  1. Current working directory (development / running from source)
//  2. Directory of the executable (portable install)
//  3. $XDG_DATA_HOME/monkeyjump (typically ~/.local/share/monkeyjump)
//  4. /usr/share/monkeyjump (system install via "make install")
//  5. /usr/local/share/monkeyjump
func resolveDataDir() string {
	candidates := []string{"."}

	// Executable directory
	if exe, err := os.Executable(); err == nil {
		candidates = append(candidates, filepath.Dir(exe))
	}

	// XDG_DATA_HOME
	xdg := os.Getenv("XDG_DATA_HOME")
	if xdg == "" {
		if home, err := os.UserHomeDir(); err == nil {
			xdg = filepath.Join(home, ".local", "share")
		}
	}
	if xdg != "" {
		candidates = append(candidates, filepath.Join(xdg, "monkeyjump"))
	}

	// System paths
	candidates = append(candidates, "/usr/share/monkeyjump", "/usr/local/share/monkeyjump")

	for _, dir := range candidates {
		// Check for themes/ subdirectory as a marker
		if info, err := os.Stat(filepath.Join(dir, "themes")); err == nil && info.IsDir() {
			return dir
		}
	}

	// Fallback to cwd
	return "."
}

// dataPath returns the full path to a file within the data directory.
func dataPath(parts ...string) string {
	elems := append([]string{dataDir}, parts...)
	return filepath.Join(elems...)
}

func init() {
	dataDir = resolveDataDir()
}
