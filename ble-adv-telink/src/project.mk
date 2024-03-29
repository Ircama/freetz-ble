PATH := ${PATH}:../SDK/tools/linux/tc32/bin

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
./app.c \
./main.c 

OBJS += \
$(OUT_PATH)/app.o \
$(OUT_PATH)/app_master.o \
$(OUT_PATH)/app_att.o \
$(OUT_PATH)/app_uart.o \
$(OUT_PATH)/at_cmd.o \
$(OUT_PATH)/at_cmdHandle.o \
$(OUT_PATH)/tokenize.o \
$(OUT_PATH)/main.o

# Each subdirectory must supply rules for building sources it contributes
$(OUT_PATH)/%.o: ./%.c
	@echo 'Building file: $<'
	@tc32-elf-gcc $(GCC_FLAGS) $(INCLUDE_PATHS) $(CFLAGS) -c -o"$@" "$<"
