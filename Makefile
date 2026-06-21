#---------------------------------------------------------------------------------
# Clear the implicit built-in rules
#---------------------------------------------------------------------------------
.SUFFIXES:

#---------------------------------------------------------------------------------
# Target configuration
#---------------------------------------------------------------------------------
TARGET		:=	pwa2nx
BUILD		:=	build
SOURCES		:=	source
DATA		:=	data
INCLUDES	:=	include

#---------------------------------------------------------------------------------
# Platform configuration details
#---------------------------------------------------------------------------------
ARCH		:=	-march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE

CFLAGS		:=	-g -Wall -O2 -ffunction-sections \
				$(ARCH) -D__SWITCH__

CFLAGS		+=	$(INCLUDE) -I$(CURDIR)/$(SOURCES) -I$(PORTLIBS)/include

CXXFLAGS	:=	$(CFLAGS) -fno-rtti -fno-exceptions

ASFLAGS		:=	-g $(ARCH)
LDFLAGS		=	-specs=$(DEVKITPRO)/libnx/switch.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)

LIBS	:=	-lcurl -lssl -lcrypto -lswkbd -lpsel -lnx -lz

#---------------------------------------------------------------------------------
# Tools configuration
#---------------------------------------------------------------------------------
PREFIX	:=	aarch64-none-elf-
CC		:=	$(PREFIX)gcc
CXX		:=	$(PREFIX)g++
AR		:=	$(PREFIX)ar
OBJCOPY	:=	$(PREFIX)objcopy
STRIP	:=	$(PREFIX)strip
NM		:=	$(PREFIX)nm

#---------------------------------------------------------------------------------
# libnx tools
#---------------------------------------------------------------------------------
NACP	:=	nacp
ELF2NRO	:=	elf2nro

#---------------------------------------------------------------------------------
# Build definitions
#---------------------------------------------------------------------------------
OUTPUT	:=	$(TARGET)
NROFILE	:=	$(OUTPUT).nro
ELFFILE	:=	$(OUTPUT).elf
NACPFILE	:=	$(OUTPUT).nacp

APP_TITLE	:=	PWA Wrapper
APP_AUTHOR	:=	pwa2nx Team
APP_VERSION	:=	1.0.0

#---------------------------------------------------------------------------------
# Find files
#---------------------------------------------------------------------------------
CFILES		:=	$(wildcard $(SOURCES)/*.c)
CPPFILES	:=	$(wildcard $(SOURCES)/*.cpp)
OFILES		:=	$(CFILES:$(SOURCES)/%.c=$(BUILD)/%.o) $(CPPFILES:$(SOURCES)/%.cpp=$(BUILD)/%.o)

#---------------------------------------------------------------------------------
# Rules
#---------------------------------------------------------------------------------
.PHONY: all clean

all: $(NROFILE)

$(NROFILE): $(ELFFILE) $(NACPFILE)
	@echo Creating NRO...
	@$(ELF2NRO) $< $@ --nacp=$(NACPFILE) --icon=$(SOURCES)/icon.png

$(ELFFILE): $(OFILES)
	@echo Linking ELF...
	@$(CC) $(LDFLAGS) $^ $(LIBS) -o $@

$(NACPFILE):
	@echo Creating NACP...
	@$(NACP) -c --name="$(APP_TITLE)" --author="$(APP_AUTHOR)" --version="$(APP_VERSION)" $@

$(BUILD)/%.o: $(SOURCES)/%.c
	@mkdir -p $(dir $@)
	@echo Compiling $<...
	@$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: $(SOURCES)/%.cpp
	@mkdir -p $(dir $@)
	@echo Compiling $<...
	@$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	@echo Cleaning...
	@rm -rf $(BUILD) $(NROFILE) $(ELFFILE) $(NACPFILE) *.map
