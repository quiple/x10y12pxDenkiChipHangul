PYTHON ?= python3
VENV ?= .venv
GLYPHS ?= $(VENV)/bin/glyphs
GLYPHS_APP ?= /Applications/Glyphs 4.app
GLYPHS_PYTHON ?= $(HOME)/Library/Application Support/Glyphs 4/Repositories/Python/Python.framework/Versions/Current/Python

FONT_NAME := x10y12pxDenkiChipHangul
SOURCE_DIR := sources
SOURCE := $(SOURCE_DIR)/$(FONT_NAME).glyphs
FONTS_DIR := fonts
OTF_DIR := $(FONTS_DIR)/otf
TTF_DIR := $(FONTS_DIR)/ttf
WEBFONTS_DIR := $(FONTS_DIR)/webfonts
BDF_DIR := $(FONTS_DIR)/bdf
BDF_SCRIPT := $(SOURCE_DIR)/export_bdf.py
BITMAP_SCRIPT := $(SOURCE_DIR)/embed_bitmap_strikes.py
CFF_MATRIX_SCRIPT := $(SOURCE_DIR)/fix_cff_font_matrix.py
BITMAP_SIZES := 12,24,36,48,60
EXPORT_CONFIG := $(SOURCE_DIR)/glyphs-export.json

OTF_FILE := $(OTF_DIR)/$(FONT_NAME).otf
TTF_FILE := $(TTF_DIR)/$(FONT_NAME).ttf
WOFF2_FILE := $(WEBFONTS_DIR)/$(FONT_NAME).woff2
BDF_FILE := $(BDF_DIR)/$(FONT_NAME).bdf
OUTPUTS := $(OTF_FILE) $(TTF_FILE) $(WOFF2_FILE) $(BDF_FILE)

.PHONY: all setup build check clean

all: build

setup:
	$(PYTHON) -m venv "$(VENV)"
	"$(VENV)/bin/python" -m pip install -r requirements.txt

build: check
	@mkdir -p "$(OTF_DIR)" "$(TTF_DIR)" "$(WEBFONTS_DIR)" "$(BDF_DIR)"
	PYTHONDONTWRITEBYTECODE=1 $(GLYPHS) export --app "$(GLYPHS_APP)" --plugins '' --config "$(EXPORT_CONFIG)" \
		--format cff --container standard --output "$(OTF_DIR)" "$(SOURCE)"
	"$(VENV)/bin/python" "$(CFF_MATRIX_SCRIPT)" "$(OTF_FILE)"
	PYTHONDONTWRITEBYTECODE=1 $(GLYPHS) export --app "$(GLYPHS_APP)" --plugins '' --config "$(EXPORT_CONFIG)" \
		--format tt --container standard --output "$(TTF_DIR)" "$(SOURCE)"
	PYTHONDONTWRITEBYTECODE=1 $(GLYPHS) export --app "$(GLYPHS_APP)" --plugins '' --config "$(EXPORT_CONFIG)" \
		--format tt --container woff2 --output "$(WEBFONTS_DIR)" "$(SOURCE)"
	PYTHONDONTWRITEBYTECODE=1 $(GLYPHS) run --app "$(GLYPHS_APP)" --python "$(GLYPHS_PYTHON)" --plugins BDF \
		"$(BDF_SCRIPT)" --input "$(SOURCE)" -- "$(BDF_FILE)"
	"$(VENV)/bin/python" "$(BITMAP_SCRIPT)" --font "$(TTF_FILE)" \
		--bdf "$(BDF_FILE)" --sizes "$(BITMAP_SIZES)"
	@for file in $(OUTPUTS); do \
		test -s "$$file" || { echo "Missing output: $$file" >&2; exit 1; }; \
	done
	@echo "Exported OTF, TTF, WOFF2, and BDF to format-specific directories under $(FONTS_DIR)/"

check:
	@command -v "$(GLYPHS)" >/dev/null 2>&1 || { \
		echo "glyphs-cli is required: run 'make setup' first" >&2; \
		exit 1; \
	}
	@"$(VENV)/bin/python" -c "import fontTools" >/dev/null 2>&1 || { \
		echo "fontTools is required: run 'make setup' first" >&2; \
		exit 1; \
	}
	@test -d "$(GLYPHS_APP)" || { \
		echo "Glyphs app not found: $(GLYPHS_APP)" >&2; \
		exit 1; \
	}
	@test -f "$(GLYPHS_PYTHON)" || { \
		echo "Glyphs Python framework not found: $(GLYPHS_PYTHON)" >&2; \
		echo "Install Python in Glyphs 4 or set GLYPHS_PYTHON to the framework's Python file." >&2; \
		exit 1; \
	}

clean:
	rm -f $(OUTPUTS)
