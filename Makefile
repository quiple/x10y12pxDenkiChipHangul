# Variables
JAR_URL = https://github.com/kreativekorp/bitsnpicas/releases/latest/download/BitsNPicas.jar
TOOLS_DIR = tools
FONTS_DIR = fonts
JAR_FILE = $(TOOLS_DIR)/BitsNPicas.jar
SRC_FILE = src/x8y12pxDenkiChipHangul.kbitx

TTF_FILE = $(FONTS_DIR)/x8y12pxDenkiChipHangul.ttf
BDF_FILE = $(FONTS_DIR)/x8y12pxDenkiChipHangul.bdf
WOFF2_FILE = $(FONTS_DIR)/x8y12pxDenkiChipHangul.woff2

FONTTOOLS = python3 -m fontTools.ttLib.woff2

# Default target
all: $(TTF_FILE) $(BDF_FILE) $(WOFF2_FILE)

# Ensure directories exist
$(TOOLS_DIR):
	mkdir -p $(TOOLS_DIR)

$(FONTS_DIR):
	mkdir -p $(FONTS_DIR)

# Download BitsNPicas.jar
$(JAR_FILE): | $(TOOLS_DIR)
	curl -L -o $(JAR_FILE) $(JAR_URL)

# Build TTF
$(TTF_FILE): $(SRC_FILE) $(JAR_FILE) | $(FONTS_DIR)
	rm -f $(TTF_FILE)
	java -jar $(JAR_FILE) convertbitmap -f ttf -o $(TTF_FILE) $(SRC_FILE)

# Build BDF
$(BDF_FILE): $(SRC_FILE) $(JAR_FILE) | $(FONTS_DIR)
	rm -f $(BDF_FILE)
	java -jar $(JAR_FILE) convertbitmap -f bdf -o $(BDF_FILE) $(SRC_FILE)

# Build WOFF2
$(WOFF2_FILE): $(TTF_FILE) | $(FONTS_DIR)
	rm -f $(WOFF2_FILE)
	$(FONTTOOLS) compress -o $(WOFF2_FILE) $(TTF_FILE)

# Clean target
clean:
	rm -f $(TTF_FILE) $(BDF_FILE) $(WOFF2_FILE)

.PHONY: all clean
