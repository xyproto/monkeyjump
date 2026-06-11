.PHONY: all clean install uninstall run

PREFIX ?= /usr
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share/monkeyjump
MANDIR ?= $(PREFIX)/share/man/man6

BINARY = monkeyjump

all: $(BINARY)

$(BINARY):
	go build -o $(BINARY) .

clean:
	rm -f $(BINARY) $(BINARY)go

install: $(BINARY)
	install -Dm755 $(BINARY) $(DESTDIR)$(BINDIR)/$(BINARY)
	install -d $(DESTDIR)$(DATADIR)/conf
	install -Dm644 conf/gnugocmd.conf $(DESTDIR)$(DATADIR)/conf/gnugocmd.conf
	install -Dm644 conf/keybindings.conf $(DESTDIR)$(DATADIR)/conf/keybindings.conf
	install -Dm644 conf/theme.conf $(DESTDIR)$(DATADIR)/conf/theme.conf
	install -d $(DESTDIR)$(DATADIR)/themes/uligo
	install -d $(DESTDIR)$(DATADIR)/themes/plain
	install -d $(DESTDIR)$(DATADIR)/themes/spreadsheet
	install -Dm644 themes/uligo/board.png $(DESTDIR)$(DATADIR)/themes/uligo/board.png
	install -Dm644 themes/uligo/black.png $(DESTDIR)$(DATADIR)/themes/uligo/black.png
	install -Dm644 themes/uligo/white.png $(DESTDIR)$(DATADIR)/themes/uligo/white.png
	install -Dm644 themes/plain/board.png $(DESTDIR)$(DATADIR)/themes/plain/board.png
	install -Dm644 themes/plain/black.png $(DESTDIR)$(DATADIR)/themes/plain/black.png
	install -Dm644 themes/plain/white.png $(DESTDIR)$(DATADIR)/themes/plain/white.png
	install -Dm644 themes/spreadsheet/board.png $(DESTDIR)$(DATADIR)/themes/spreadsheet/board.png
	install -Dm644 themes/spreadsheet/black.png $(DESTDIR)$(DATADIR)/themes/spreadsheet/black.png
	install -Dm644 themes/spreadsheet/white.png $(DESTDIR)$(DATADIR)/themes/spreadsheet/white.png

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/$(BINARY)
	rm -rf $(DESTDIR)$(DATADIR)

run: $(BINARY)
	./$(BINARY) --tiny
