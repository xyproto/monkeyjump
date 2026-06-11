# Monkeyjump Go

A Go port of [Monkeyjump](https://github.com/xyproto/monkeyjump) — a small program for playing Go against GNU Go in a compact window.

Uses SDL3 for rendering and communicates with GNU Go (or any GTP-compatible engine) via the Go Text Protocol.

## Requirements

- SDL3 and SDL3_image development libraries
- GNU Go (or another GTP-compatible Go engine)
- Go 1.22+

### Fedora

```sh
sudo dnf install SDL3-devel SDL3_image-devel gnugo
```

### Ubuntu/Debian

```sh
sudo apt install libsdl3-dev libsdl3-image-dev gnugo
```

## Build

```sh
go build
```

## Run

```sh
./monkeyjump        # default 9x9 board
./monkeyjump 19     # 19x19 board
./monkeyjump game.sgf  # load an SGF file
```

## Keybindings

| Key | Action |
|-----|--------|
| Arrow keys | Move cursor |
| Space | Play black + GnuGo responds as white |
| Tab | My play (analyzer/engine) as white |
| Return | Ask GnuGo to play white |
| m | Ask GnuGo to play black |
| w | Place white stone (no response) |
| b | Place black stone (no response) |
| u | Undo |
| a | Pass (black) |
| z | Pass (white) |
| g | Show last move |
| v | Show board (text) |
| e | Estimate score |
| f | Final score |
| n | Next move (SGF) |
| p | Previous move (SGF) |
| s | Save SGF |
| l | Reload SGF |
| i | Toggle illegal moves |
| c | GTP console |
| o | Show future white moves |
| t | Set time (5s) |
| x | Show move probabilities |
| y | Play 100 auto-moves |
| Numpad 1-9 | Jump to board positions |
| Numpad 0 | Set level 0 |
| 1-9, 0 | Set GnuGo level (0=level 10) |
| F1 | GnuGo engine info |
| F2 | Analyze (liberty-based move suggestion) |
| F3 | Show dragons |
| F12 | Save screenshot (BMP) |
| Backspace | Clear board |
| q / Escape | Quit |

### Mouse

| Button | Action |
|--------|--------|
| Left click | Play black at position |
| Middle click | New game as black |
| Right click | Show status (score + level) |

## Configuration

- `conf/gnugocmd.conf` — GTP engine command (default: `gnugo --mode gtp`)
- `conf/theme.conf` — Theme name (default: `uligo`)
- `conf/keybindings.conf` — Keybinding reference (read-only)
- `themes/` — Board and stone images (uligo, plain, spreadsheet)

## Themes

Three themes are included:
- **uligo** — Wooden board with realistic stones
- **plain** — Simple flat design
- **spreadsheet** — Minimalist grid style

## License

GPL-2.0
