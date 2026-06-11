package main

/*
#cgo pkg-config: sdl3
#cgo LDFLAGS: -lSDL3_image
#include <SDL3/SDL.h>
#include <SDL3_image/SDL_image.h>
#include <stdlib.h>
*/
import "C"
import (
	"fmt"
	"unsafe"
)

func sdlInit() error {
	if !C.SDL_Init(C.SDL_INIT_VIDEO) {
		return fmt.Errorf("SDL_Init: %s", C.GoString(C.SDL_GetError()))
	}
	return nil
}

func sdlQuit() {
	C.SDL_Quit()
}

type Window struct {
	w *C.SDL_Window
}

func createWindow(title string, width, height int) (*Window, error) {
	ct := C.CString(title)
	defer C.free(unsafe.Pointer(ct))
	w := C.SDL_CreateWindow(ct, C.int(width), C.int(height), 0)
	if w == nil {
		return nil, fmt.Errorf("SDL_CreateWindow: %s", C.GoString(C.SDL_GetError()))
	}
	return &Window{w: w}, nil
}

func (w *Window) Show() {
	C.SDL_ShowWindow(w.w)
}

func (w *Window) Raise() {
	C.SDL_RaiseWindow(w.w)
}

func (w *Window) Destroy() {
	if w.w != nil {
		C.SDL_DestroyWindow(w.w)
	}
}

type Renderer struct {
	r *C.SDL_Renderer
}

func createRenderer(w *Window) (*Renderer, error) {
	r := C.SDL_CreateRenderer(w.w, nil)
	if r == nil {
		return nil, fmt.Errorf("SDL_CreateRenderer: %s", C.GoString(C.SDL_GetError()))
	}
	return &Renderer{r: r}, nil
}

func (r *Renderer) Destroy() {
	if r.r != nil {
		C.SDL_DestroyRenderer(r.r)
	}
}

func (r *Renderer) SetDrawColor(red, green, blue, alpha uint8) {
	C.SDL_SetRenderDrawColor(r.r, C.Uint8(red), C.Uint8(green), C.Uint8(blue), C.Uint8(alpha))
}

func (r *Renderer) Clear() {
	C.SDL_RenderClear(r.r)
}

func (r *Renderer) Present() {
	C.SDL_RenderPresent(r.r)
}

func (r *Renderer) DrawLine(x1, y1, x2, y2 float32) {
	C.SDL_RenderLine(r.r, C.float(x1), C.float(y1), C.float(x2), C.float(y2))
}

func (r *Renderer) FillRect(x, y, w, h float32) {
	rect := C.SDL_FRect{x: C.float(x), y: C.float(y), w: C.float(w), h: C.float(h)}
	C.SDL_RenderFillRect(r.r, &rect)
}

func (r *Renderer) DrawRect(x, y, w, h float32) {
	rect := C.SDL_FRect{x: C.float(x), y: C.float(y), w: C.float(w), h: C.float(h)}
	C.SDL_RenderRect(r.r, &rect)
}

type Texture struct {
	t *C.SDL_Texture
	w int
	h int
}

func loadTexture(r *Renderer, path string) (*Texture, error) {
	cp := C.CString(path)
	defer C.free(unsafe.Pointer(cp))
	surf := C.IMG_Load(cp)
	if surf == nil {
		return nil, fmt.Errorf("IMG_Load(%s): %s", path, C.GoString(C.SDL_GetError()))
	}
	defer C.SDL_DestroySurface(surf)
	t := C.SDL_CreateTextureFromSurface(r.r, surf)
	if t == nil {
		return nil, fmt.Errorf("SDL_CreateTextureFromSurface: %s", C.GoString(C.SDL_GetError()))
	}
	return &Texture{t: t, w: int(surf.w), h: int(surf.h)}, nil
}

func (t *Texture) Destroy() {
	if t.t != nil {
		C.SDL_DestroyTexture(t.t)
	}
}

func (r *Renderer) RenderTexture(t *Texture, dx, dy, dw, dh float32) {
	dst := C.SDL_FRect{x: C.float(dx), y: C.float(dy), w: C.float(dw), h: C.float(dh)}
	C.SDL_RenderTexture(r.r, t.t, nil, &dst)
}

// Event polling
type EventType int

const (
	EventNone EventType = iota
	EventQuit
	EventKeyDown
	EventMouseMotion
	EventMouseButtonDown
	EventWindowEnter
)

type Event struct {
	Type   EventType
	Key    int // SDL scancode
	MouseX float32
	MouseY float32
	Button int // 1=left, 2=middle, 3=right
}

func pollEvent() (Event, bool) {
	var ev C.SDL_Event
	if C.SDL_PollEvent(&ev) {
		return translateEvent(&ev), true
	}
	return Event{}, false
}

func translateEvent(ev *C.SDL_Event) Event {
	etype := *(*C.Uint32)(unsafe.Pointer(ev))
	switch etype {
	case C.SDL_EVENT_QUIT:
		return Event{Type: EventQuit}
	case C.SDL_EVENT_KEY_DOWN:
		kev := (*C.SDL_KeyboardEvent)(unsafe.Pointer(ev))
		return Event{Type: EventKeyDown, Key: int(kev.scancode)}
	case C.SDL_EVENT_MOUSE_MOTION:
		mev := (*C.SDL_MouseMotionEvent)(unsafe.Pointer(ev))
		return Event{Type: EventMouseMotion, MouseX: float32(mev.x), MouseY: float32(mev.y)}
	case C.SDL_EVENT_MOUSE_BUTTON_DOWN:
		bev := (*C.SDL_MouseButtonEvent)(unsafe.Pointer(ev))
		return Event{Type: EventMouseButtonDown, MouseX: float32(bev.x), MouseY: float32(bev.y), Button: int(bev.button)}
	case C.SDL_EVENT_WINDOW_MOUSE_ENTER,
		C.SDL_EVENT_WINDOW_FOCUS_GAINED,
		C.SDL_EVENT_WINDOW_EXPOSED,
		C.SDL_EVENT_WINDOW_SHOWN,
		C.SDL_EVENT_WINDOW_RESTORED:
		var mx, my C.float
		C.SDL_GetMouseState(&mx, &my)
		return Event{Type: EventWindowEnter, MouseX: float32(mx), MouseY: float32(my)}
	}
	return Event{Type: EventNone}
}

func sdlDelay(ms uint32) {
	C.SDL_Delay(C.Uint32(ms))
}

// SaveScreenshot captures the current render output and saves it as a BMP file.
func (r *Renderer) SaveScreenshot(filename string) error {
	surf := C.SDL_RenderReadPixels(r.r, nil)
	if surf == nil {
		return fmt.Errorf("SDL_RenderReadPixels: %s", C.GoString(C.SDL_GetError()))
	}
	defer C.SDL_DestroySurface(surf)
	cname := C.CString(filename)
	defer C.free(unsafe.Pointer(cname))
	if !C.SDL_SaveBMP(surf, cname) {
		return fmt.Errorf("SDL_SaveBMP: %s", C.GoString(C.SDL_GetError()))
	}
	return nil
}

// SDL3 scancodes
const (
	ScancodeEscape    = C.SDL_SCANCODE_ESCAPE
	ScancodeReturn    = C.SDL_SCANCODE_RETURN
	ScancodeSpace     = C.SDL_SCANCODE_SPACE
	ScancodeBackspace = C.SDL_SCANCODE_BACKSPACE
	ScancodeTab       = C.SDL_SCANCODE_TAB
	ScancodeUp        = C.SDL_SCANCODE_UP
	ScancodeDown      = C.SDL_SCANCODE_DOWN
	ScancodeLeft      = C.SDL_SCANCODE_LEFT
	ScancodeRight     = C.SDL_SCANCODE_RIGHT
	ScancodeA         = C.SDL_SCANCODE_A
	ScancodeB         = C.SDL_SCANCODE_B
	ScancodeC         = C.SDL_SCANCODE_C
	ScancodeE         = C.SDL_SCANCODE_E
	ScancodeF         = C.SDL_SCANCODE_F
	ScancodeG         = C.SDL_SCANCODE_G
	ScancodeI         = C.SDL_SCANCODE_I
	ScancodeL         = C.SDL_SCANCODE_L
	ScancodeM         = C.SDL_SCANCODE_M
	ScancodeN         = C.SDL_SCANCODE_N
	ScancodeO         = C.SDL_SCANCODE_O
	ScancodeP         = C.SDL_SCANCODE_P
	ScancodeQ         = C.SDL_SCANCODE_Q
	ScancodeS         = C.SDL_SCANCODE_S
	ScancodeT         = C.SDL_SCANCODE_T
	ScancodeU         = C.SDL_SCANCODE_U
	ScancodeV         = C.SDL_SCANCODE_V
	ScancodeW         = C.SDL_SCANCODE_W
	ScancodeX         = C.SDL_SCANCODE_X
	ScancodeY         = C.SDL_SCANCODE_Y
	ScancodeZ         = C.SDL_SCANCODE_Z
	Scancode0         = C.SDL_SCANCODE_0
	Scancode1         = C.SDL_SCANCODE_1
	Scancode2         = C.SDL_SCANCODE_2
	Scancode3         = C.SDL_SCANCODE_3
	Scancode4         = C.SDL_SCANCODE_4
	Scancode5         = C.SDL_SCANCODE_5
	Scancode6         = C.SDL_SCANCODE_6
	Scancode7         = C.SDL_SCANCODE_7
	Scancode8         = C.SDL_SCANCODE_8
	Scancode9         = C.SDL_SCANCODE_9
	ScancodeF1        = C.SDL_SCANCODE_F1
	ScancodeF2        = C.SDL_SCANCODE_F2
	ScancodeF3        = C.SDL_SCANCODE_F3
	ScancodeF12       = C.SDL_SCANCODE_F12
	ScancodeKP0       = C.SDL_SCANCODE_KP_0
	ScancodeKP1       = C.SDL_SCANCODE_KP_1
	ScancodeKP2       = C.SDL_SCANCODE_KP_2
	ScancodeKP3       = C.SDL_SCANCODE_KP_3
	ScancodeKP4       = C.SDL_SCANCODE_KP_4
	ScancodeKP5       = C.SDL_SCANCODE_KP_5
	ScancodeKP6       = C.SDL_SCANCODE_KP_6
	ScancodeKP7       = C.SDL_SCANCODE_KP_7
	ScancodeKP8       = C.SDL_SCANCODE_KP_8
	ScancodeKP9       = C.SDL_SCANCODE_KP_9
)
