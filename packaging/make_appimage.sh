#!/usr/bin/env bash
# Empaqueta el binario PyInstaller (onefile) en un AppImage.
# Uso: ./packaging/make_appimage.sh [binario] [salida.AppImage]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-$ROOT/dist/CryptoBro}"
OUT="${2:-$ROOT/dist/CryptoBro-x86_64.AppImage}"

# rutas absolutas (si cd a dist, una OUT relativa crea dist/dist/…)
[[ "$BIN" = /* ]] || BIN="$ROOT/$BIN"
[[ "$OUT" = /* ]] || OUT="$ROOT/$OUT"
mkdir -p "$(dirname "$OUT")"

APPDIR="$ROOT/dist/CryptoBro.AppDir"

if [[ ! -f "$BIN" ]]; then
  echo "No está el binario: $BIN" >&2
  exit 1
fi

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

cp "$BIN" "$APPDIR/usr/bin/CryptoBro"
chmod +x "$APPDIR/usr/bin/CryptoBro"

cp "$ROOT/src/assets/images/favicon.png" "$APPDIR/cryptobro.png"

cat > "$APPDIR/cryptobro.desktop" <<'EOF'
[Desktop Entry]
Name=CryptoBro
Exec=CryptoBro
Icon=cryptobro
Type=Application
Categories=Utility;System;Security;
Comment=Cifrado portable offline
Terminal=false
EOF

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/CryptoBro" "$@"
EOF
chmod +x "$APPDIR/AppRun"

ARCH="${ARCH:-x86_64}"
export ARCHITECTURE="$ARCH"
TOOL="$ROOT/dist/appimagetool-${ARCH}.AppImage"
if [[ ! -f "$TOOL" ]]; then
  curl -fsSL -o "$TOOL" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
  chmod +x "$TOOL"
fi

# Extraer tool en CI (FUSE no siempre disponible) y generar en abs path
if [[ -n "${CI:-}" ]] || ! "$TOOL" --appimage-extract-and-run --version >/dev/null 2>&1; then
  EXTRACT="$ROOT/dist/squashfs-root"
  rm -rf "$EXTRACT"
  cd "$ROOT/dist"
  "$TOOL" --appimage-extract
  "$EXTRACT/AppRun" "$APPDIR" "$OUT"
else
  "$TOOL" "$APPDIR" "$OUT"
fi

chmod +x "$OUT"
ls -lh "$OUT"
echo "AppImage → $OUT"
