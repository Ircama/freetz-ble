TEL_PATH ?= ./SDK
TOOLS_PATH := $(TEL_PATH)/tools/linux/
PATH := ${PATH}:../SDK/tools/linux/tc32/bin

all:
ifneq ($(TOOLS_PATH)/tc32_gcc_v2.0.tar.bz2, $(wildcard $(TOOLS_PATH)/tc32_gcc_v2.0.tar.bz2))
	@wget -P $(TOOLS_PATH) http://shyboy.oss-cn-shenzhen.aliyuncs.com/readonly/tc32_gcc_v2.0.tar.bz2 
	@tar -xvjf $(TOOLS_PATH)tc32_gcc_v2.0.tar.bz2 -C $(TOOLS_PATH)	
endif
	cd src; \
	$(MAKE)

clean:
	rm -rf SDK src/out
