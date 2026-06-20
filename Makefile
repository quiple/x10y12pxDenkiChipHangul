# Variables
JAR_URL = https://github.com/kreativekorp/bitsnpicas/releases/latest/download/BitsNPicas.jar
TOOLS_DIR = tools
DIST_DIR = fonts
JAR_FILE = $(TOOLS_DIR)/BitsNPicas.jar
SRC_FILE = src/x8y12pxDenkiChipHangul.kbitx

TTF_FILE = $(DIST_DIR)/x8y12pxDenkiChipHangul.ttf
BDF_FILE = $(DIST_DIR)/x8y12pxDenkiChipHangul.bdf
WOFF2_FILE = $(DIST_DIR)/x8y12pxDenkiChipHangul.woff2

FONTTOOLS = python3 -m fontTools.ttLib.woff2

# Default target
all: $(TTF_FILE) $(BDF_FILE) $(WOFF2_FILE)

# Ensure directories exist
$(TOOLS_DIR):
	mkdir -p $(TOOLS_DIR)

$(DIST_DIR):
	mkdir -p $(DIST_DIR)

# Download BitsNPicas.jar
$(JAR_FILE): | $(TOOLS_DIR)
	curl -L -o $(JAR_FILE) $(JAR_URL)

# Build TTF
$(TTF_FILE): $(SRC_FILE) $(JAR_FILE) | $(DIST_DIR)
	java -jar $(JAR_FILE) convertbitmap -f ttf -o $(TTF_FILE) $(SRC_FILE)

# Build BDF
$(BDF_FILE): $(SRC_FILE) $(JAR_FILE) | $(DIST_DIR)
	java -jar $(JAR_FILE) convertbitmap -f bdf -o $(BDF_FILE) $(SRC_FILE)

# Build WOFF2
$(WOFF2_FILE): $(TTF_FILE) | $(DIST_DIR)
	$(FONTTOOLS) compress -o $(WOFF2_FILE) $(TTF_FILE)

# Clean target
clean:
	rm -rf $(DIST_DIR)

.PHONY: all clean
