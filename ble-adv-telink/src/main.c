/********************************************************************************************************
 * @file     main.c
 *
 * @brief    for TLSR chips
 *
 * @author	 public@telink-semi.com;
 * @date     Sep. 18, 2018
 *
 * @par      Copyright (c) Telink Semiconductor (Shanghai) Co., Ltd.
 *           All rights reserved.
 *
 *			 The information contained herein is confidential and proprietary property of Telink
 * 		     Semiconductor (Shanghai) Co., Ltd. and is available under the terms
 *			 of Commercial License Agreement between Telink Semiconductor (Shanghai)
 *			 Co., Ltd. and the licensee in separate contract or the terms described here-in.
 *           This heading MUST NOT be removed from this file.
 *
 * 			 Licensees are granted free, non-transferable use of the information in this
 *			 file under Mutual Non-Disclosure Agreement. NO WARRENTY of ANY KIND is provided.
 *
 *******************************************************************************************************/

#include "tl_common.h"
#include "drivers.h"
#include "stack/ble/ble.h"
#include "vendor/common/user_config.h"
#include "vendor/common/blt_soft_timer.h"
#include "tinyFlash/tinyFlash.h"
#include "tinyFlash_Index.h"
#include "app_uart.h"

u32 device_mode;

// from in app_uart.c
extern u8 ATE;
extern u8 baud_buf[];
extern void app_uart_loop();
extern void my_gpio_init(void);
extern void app_uart_init(AT_BAUD baud);
extern void app_uart_irq_proc(void);
extern int watchdog();

// from in app_master.c
extern void ble_master_mainloop(void);
extern void ble_master_init_normal(void);
extern _attribute_ram_code_ void ble_master_init_deepRetn(void);

// from in app.c
extern u8 scan_type;
extern void ble_slave_init_normal(void);
extern _attribute_ram_code_ void ble_slave_init_deepRetn(void);

_attribute_ram_code_ void irq_handler(void)
{
	app_uart_irq_proc();

	irq_blt_sdk_handler();
}

_attribute_ram_code_ int main (void)    //must run in ramcode
{
	blc_pm_select_internal_32k_crystal();

	cpu_wakeup_init();

	int deepRetWakeUp = pm_is_MCU_deepRetentionWakeup();  //MCU deep retention wakeUp

	rf_drv_init(RF_MODE_BLE_1M);

	gpio_init( !deepRetWakeUp );  //analog resistance will keep available in deepSleep mode, so no need initialize again

#if (CLOCK_SYS_CLOCK_HZ == 16000000)
	clock_init(SYS_CLK_16M_Crystal);
#elif (CLOCK_SYS_CLOCK_HZ == 24000000)
	clock_init(SYS_CLK_24M_Crystal);
#elif (CLOCK_SYS_CLOCK_HZ == 32000000)
	clock_init(SYS_CLK_32M_Crystal);
#endif

	blc_app_loadCustomizedParameters();  //load customized freq_offset cap value

	tinyFlash_Init(0x70000,0x4000); //初始化KV存储系统

	if(!deepRetWakeUp )
	{
		u8 len =1;

		tinyFlash_Read(STORAGE_BAUD, baud_buf, &len); //读取波特率

		tinyFlash_Read(STORAGE_ATE, &ATE, &len); //读取ATE
		
		len =1;
		tinyFlash_Read(STORAGE_MODE, (unsigned char *)&device_mode, &len); //读取ATE
	}
	app_uart_init(baud_buf[0]);  //初始化串口

	my_gpio_init(); //初始化GPIO

	blt_soft_timer_init(); // 初始化定时器
	

	if( deepRetWakeUp )
	{
		if(device_mode == 1) //master mode
		{
			ble_master_init_deepRetn();
		}
		else //slave or iBeacon
		{
			ble_slave_init_deepRetn();
		}
	}
	else
	{
		if(device_mode == 1) //master mode
		{
			ble_master_init_normal();
		}
		else //slave or iBeacon
		{
			ble_slave_init_normal();
		}
		//WaitMs(10);
		printf("    \r\nIRCAMA Ai-Thinker BLE AT "AT_VERSION"\r\n+READY\r\n");
	}

	irq_enable();

    u8 buff_len = 1;
    if(tinyFlash_Read(STORAGE_SCAN, &scan_type, &buff_len) == 0)
    {
        printf("\r\n+SCAN_TYPE_INIT:%d\r\n", scan_type);
        if ((scan_type == 2) || (scan_type == 3)) {

            gpio_set_func(GPIO_PC2, AS_GPIO);
            gpio_set_func(GPIO_PC3, AS_GPIO);
            gpio_set_func(GPIO_PC4, AS_GPIO);
            gpio_set_output_en(GPIO_PC2, 1);//enable output
            gpio_set_output_en(GPIO_PC3, 1);//enable output
            gpio_set_output_en(GPIO_PC4, 1);//enable output
            gpio_set_input_en(GPIO_PC2, 0);//disenable input
            gpio_set_input_en(GPIO_PC3, 0);//disenable input
            gpio_set_input_en(GPIO_PC4, 0);//disenable input

            blc_ll_setScanParameter(SCAN_TYPE_PASSIVE, SCAN_INTERVAL_100MS, SCAN_INTERVAL_100MS, OWN_ADDRESS_PUBLIC, SCAN_FP_ALLOW_ADV_ANY);
            blc_ll_setScanEnable (BLC_SCAN_ENABLE, DUP_FILTER_DISABLE);
            blt_soft_timer_add((blt_timer_callback_t) watchdog, 3000000);  // 3 seconds
        }
    }

	while (1) //main_loop
	{
#if (MODULE_WATCHDOG_ENABLE)
		wd_clear(); //clear watch dog
#endif
		blt_sdk_main_loop();

		if(device_mode == 1) //master mode
		{
			ble_master_mainloop();
		}

		// ////////////////////////////////////// PM Process /////////////////////////////////
		// blt_pm_proc();

		app_uart_loop();

		blt_soft_timer_process(MAINLOOP_ENTRY);
	
	}
}

 