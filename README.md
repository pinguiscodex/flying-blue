# flying-blue

WebSocket-Anwendung mit getrenntem Server, Sender und Receiver. Der Server nimmt
Nachrichten vom Sender an und leitet sie an alle verbundenen Receiver weiter.

## Entwicklung

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Server starten:

```bash
python src/server.py --host 0.0.0.0 --port 8765
```

Receiver starten (in einem zweiten Terminal):

```bash
python src/receiver.py --host 0.0.0.0 --port 8765
```

Sender starten (in einem dritten Terminal):

```bash
python src/sender.py --host 127.0.0.1 --port 8765
```

Alternativ ist der Paket-Entry-Point verfügbar:

```bash
python -m flying_blue server
python -m flying_blue sender
python -m flying_blue receiver
```

## PyInstaller

Für reproduzierbare One-Folder-Builds:

```bash
pyinstaller --clean build/sender.spec
pyinstaller --clean build/receiver.spec
pyinstaller --clean build/server.spec
```

Die Artefakte werden als Linux-Executables in `dist/Sender`, `dist/Receiver`
und `dist/Server` erzeugt.
Alle drei Executables werden ohne Terminalfenster gestartet und können dadurch
im Hintergrund laufen.
