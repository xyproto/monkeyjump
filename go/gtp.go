package main

import (
	"bufio"
	"fmt"
	"io"
	"os/exec"
	"strings"
	"sync"
)

// GTP communicates with a GTP-compatible Go engine (e.g., GnuGo).
type GTP struct {
	cmd    *exec.Cmd
	stdin  io.WriteCloser
	stdout *bufio.Reader
	mu     sync.Mutex
	cmdNum int
}

// Available returns true if the GTP engine is not currently processing a command.
func (g *GTP) Available() bool {
	if g.mu.TryLock() {
		g.mu.Unlock()
		return true
	}
	return false
}

func NewGTP(command string) (*GTP, error) {
	parts := strings.Fields(command)
	if len(parts) == 0 {
		return nil, fmt.Errorf("empty GTP command")
	}
	cmd := exec.Command(parts[0], parts[1:]...)
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	cmd.Stderr = nil
	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("failed to start GTP engine %q: %w", command, err)
	}
	return &GTP{
		cmd:    cmd,
		stdin:  stdin,
		stdout: bufio.NewReader(stdout),
		cmdNum: 1,
	}, nil
}

func (g *GTP) Send(command string) string {
	g.mu.Lock()
	defer g.mu.Unlock()

	cmd := fmt.Sprintf("%d %s\n", g.cmdNum, command)
	fmt.Print(">> ", cmd)
	_, err := io.WriteString(g.stdin, cmd)
	if err != nil {
		fmt.Printf("GTP write error: %v\n", err)
		return ""
	}

	// GTP response format: "=id response\n\n" or "?id error\n\n"
	// The response starts with = or ? and is terminated by a blank line.
	var response strings.Builder
	started := false
	for {
		line, err := g.stdout.ReadString('\n')
		if err != nil {
			break
		}
		trimmed := strings.TrimSpace(line)

		if !started {
			// Skip blank lines before the response begins
			if trimmed == "" {
				continue
			}
			// Response must start with = or ?
			if strings.HasPrefix(trimmed, "=") || strings.HasPrefix(trimmed, "?") {
				started = true
				response.WriteString(trimmed)
				response.WriteByte('\n')
			}
			continue
		}

		// After the response starts, a blank line terminates it
		if trimmed == "" {
			break
		}
		response.WriteString(trimmed)
		response.WriteByte('\n')
	}

	g.cmdNum++
	result := strings.TrimSpace(response.String())
	fmt.Println("<<", result)
	return result
}

// SendExtract sends a command and extracts the value after "=id ".
// For multi-line responses, returns all content after the "=id" first line.
func (g *GTP) SendExtract(command string) string {
	resp := g.Send(command)
	if resp == "" {
		return ""
	}
	lines := strings.Split(resp, "\n")
	first := strings.TrimSpace(lines[0])

	if !strings.HasPrefix(first, "=") && !strings.HasPrefix(first, "?") {
		return resp
	}

	// Strip the "=" or "?" prefix
	rest := first[1:]

	// Strip the numeric command ID
	i := 0
	for i < len(rest) && rest[i] >= '0' && rest[i] <= '9' {
		i++
	}
	// After the ID, there might be a space followed by the value
	afterID := rest[i:]
	firstLineValue := strings.TrimSpace(afterID)

	if len(lines) > 1 {
		// Multi-line response: combine first-line value with remaining lines
		remaining := strings.TrimSpace(strings.Join(lines[1:], "\n"))
		if firstLineValue != "" && remaining != "" {
			return firstLineValue + "\n" + remaining
		} else if remaining != "" {
			return remaining
		}
		return firstLineValue
	}
	return firstLineValue
}

func (g *GTP) Close() {
	g.Send("quit")
	g.stdin.Close()
	g.cmd.Wait()
}
