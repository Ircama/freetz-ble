#include "tl_common.h"
#include "at_cmd.h"
#include "drivers.h"

#include "stack/ble/ble.h"
#include "vendor/common/blt_soft_timer.h"

#include "tinyFlash/tinyFlash.h"
#include "tinyFlash_Index.h"

//外部变量
extern u8 baud_buf[];
extern  const u8 tbl_scanRsp[];
extern u8 my_scanRsp[32];
extern u8 ATE;
extern u8  mac_public[6];
extern void lsleep_enable();

typedef struct _gpio {
	const char *cmd; /**< Command String. */
	const int gpio;
}_gpio_t;

_gpio_t gpio_ports[] =
{
    { "PA1", GPIO_PA1 },
    { "PA2", GPIO_PA2 },
    { "PA3", GPIO_PA3 },
    { "PA4", GPIO_PA4 },
    { "PA5", GPIO_PA5 },
    { "PA6", GPIO_PA6 },
    { "PA7", GPIO_PA7 },

    { "PB0", GPIO_PB0 },
    { "PB1", GPIO_PB1 },
    { "PB2", GPIO_PB2 },
    { "PB3", GPIO_PB3 },
    { "PB4", GPIO_PB4 },
    { "PB5", GPIO_PB5 },
    { "PB6", GPIO_PB6 },
    { "PB7", GPIO_PB7 },

    { "PC0", GPIO_PC0 },
    { "PC1", GPIO_PC1 },
    { "PC2", GPIO_PC2 },
    { "PC3", GPIO_PC3 },
    { "PC4", GPIO_PC4 },
    { "PC5", GPIO_PC5 },
    { "PC6", GPIO_PC6 },
    { "PC7", GPIO_PC7 },

    { "PD0", GPIO_PD0 },
    { "PD1", GPIO_PD1 },
    { "PD2", GPIO_PD2 },
    { "PD3", GPIO_PD3 },
    { "PD4", GPIO_PD4 },
    { "PD5", GPIO_PD5 },
    { "PD6", GPIO_PD6 },
    { "PD7", GPIO_PD7 },

    { "PE0", GPIO_PE0 },
    { "PE1", GPIO_PE1 },
    { "PE2", GPIO_PE2 },
    { "PE3", GPIO_PE3 },

	{0, 	0}
};

int str2hex(char * pbuf, int len)
{
	int i = 0;
	for(i = 0; i < len; i ++)
	{
		if(((pbuf[i] >= '0') && (pbuf[i] <= '9')) || ((pbuf[i] >= 'A') && (pbuf[i] <= 'F')))
		{
			if((pbuf[i] >= '0') && (pbuf[i] <= '9'))
			{
				pbuf[i] -= '0';
			}
			else
			{
				pbuf[i] -= 'A';
				pbuf[i] += 0x0A;
			}

			if(i%2)
			{
				pbuf[i/2] = (pbuf[i-1] << 4) | pbuf[i];
			}
		}
		else
		{
			return -1;
		}
	}

	return 0;
}

/* 经过data_process_parse函数分析执行下列函数 */

//关回显 回显即 将指令重复并输出结果
static unsigned char atCmd_ATE0(char *pbuf,  int mode, int length)
{
	ATE = 0;
	tinyFlash_Write(STORAGE_ATE, &ATE, 1);
	return 0;
}
//开回显 回显即 将指令重复并输出结果
static unsigned char atCmd_ATE1(char *pbuf,  int mode, int length)
{
	ATE = 1;
	tinyFlash_Write(STORAGE_ATE, &ATE, 1);
	return 0;
}
//获取AT版本
static unsigned char atCmd_GMR(char *pbuf,  int mode, int length)
{
	
	at_print("\r\n+VER:"AT_VERSION);
	return 0;
}
//重启
static unsigned char atCmd_Reset(char *pbuf,  int mode, int length)
{
	at_print("\r\nOK\r\n");
	start_reboot();
	return 0;
}
//睡眠
extern  GPIO_PinTypeDef UART_RX_PIN;
static unsigned char atCmd_Sleep(char *pbuf,  int mode, int length)
{
	at_print("\r\nOK\r\n");

	while(uart_tx_is_busy())//等待串口数据发送完成，不同波特率需要时间不同
	{
		sleep_us(10);
	};

	gpio_setup_up_down_resistor(UART_RX_PIN, PM_PIN_PULLUP_10K);
	cpu_set_gpio_wakeup (UART_RX_PIN, Level_Low, 1); 

	cpu_sleep_wakeup(DEEPSLEEP_MODE, PM_WAKEUP_PAD, 0);  //deepsleep
	return 0;
}

//轻度睡眠，保持蓝牙及连接功能
extern u8 lsleep_model;
static unsigned char  atCmd_LSleep(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		if(lsleep_model == 1)
		{
			at_print("\r\n+LSLEEP:1");
		}
		else
		{
			at_print("\r\n+LSLEEP:0");
		}
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		if(pbuf[0] == '1') lsleep_model = 1;
		else lsleep_model = 0;
		tinyFlash_Write(STORAGE_LSLEEP, &lsleep_model, 1);
		return 0;
	}
	else if(mode == AT_CMD_MODE_EXECUTION)
	{
		at_print("\r\nOK\r\n");
		lsleep_enable();
		return 0xFF;
	}
	else
	{
		return 2;
	}
}
//恢复出厂设置并重启
static unsigned char atCmd_Restore(char *pbuf,  int mode, int length)
{
	tinyFlash_Format();
	at_print("\r\nOK\r\n");
	start_reboot();
	return 0;
}
//波特率
static unsigned char atCmd_Baud(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+BAUD:%d",baud_buf[0]);
		return 0;
	}

	if(mode == AT_CMD_MODE_SET)
	{
		if((pbuf[0] >= '0') && (pbuf[0] <= '9'))
		{
			pbuf[0] -= '0';
			tinyFlash_Write(STORAGE_BAUD, (unsigned char*)pbuf, 1);
			return 0;
		}
		else
		{
			return 2;
		}
	}
	return 1;
}
//名字
static unsigned char atCmd_Name(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		at_print("\r\n+NAME:");

		if(my_scanRsp[1] == 0x09) //客户自定义的蓝牙设备名称
		{
			at_send((char *) (my_scanRsp+2), my_scanRsp[0] -1);
		}
		else
		{
			at_send((char *) (tbl_scanRsp+2), 10);
		}

		return 0;
	}

	if(mode == AT_CMD_MODE_SET)
	{
		tinyFlash_Write(STORAGE_NAME, (unsigned char*)pbuf, length);
		return 0;
	}
	return 1;
}
//MAC地址
static unsigned char atCmd_Mac(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+MAC:%02X%02X%02X%02X%02X%02X", mac_public[5], mac_public[4], mac_public[3], mac_public[2], mac_public[1], mac_public[0] );
		return 0;
	}

	if(mode == AT_CMD_MODE_SET)
	{
		if(length != 12) 
		{
			at_print("len error\r\n");
			return 2;
		}

		if(str2hex(pbuf, 12) == -1 ) return 2;

		pbuf[6] = pbuf[0];
		pbuf[0] = pbuf[5];
		pbuf[5] = pbuf[6];

		pbuf[6] = pbuf[1];
		pbuf[1] = pbuf[4];
		pbuf[4] = pbuf[6];

		pbuf[6] = pbuf[2];
		pbuf[2] = pbuf[3];
		pbuf[3] = pbuf[6];

		flash_erase_sector (CFG_ADR_MAC);
		flash_write_page (CFG_ADR_MAC, 8, (unsigned char*)pbuf);
		
		return 0;
	}

	return 1;
}

/*读取某片Flash数据到全局变量，主要用于调试tinyFlash*/
unsigned long r_addr = 0;
static unsigned char atCmd_Read(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_SET)
	{

		if((pbuf[0] >= '0') && (pbuf[0] <= '9'))
		{
			pbuf[0] -= '0';
		}
		else if((pbuf[0] >= 'A') && (pbuf[0] <= 'F'))
		{
			pbuf[0] -= ('A' -10);
		}
		

		if((pbuf[1] >= '0') && (pbuf[1] <= '9'))
		{
			pbuf[1] -= '0';
		}
		else if((pbuf[1] >= 'A') && (pbuf[1] <= 'F'))
		{
			pbuf[1] -= ('A' -10);
		}

		pbuf[0] = pbuf[0] *16 + pbuf[1];

		r_addr = pbuf[0] * 256;

		r_addr += 0x70000;

		tinyFlash_Debug(r_addr);
		return 0;
	}
	else
	{
		return 1;
	}
}

extern u32 device_in_connection_state; //从机状态下已被连接标志位
extern u32 cur_conn_device_hdl;//主机状态下已建立连接标志位
static unsigned char atCmd_State(char *pbuf,  int mode, int length)
{
	if((device_in_connection_state ==0) && (cur_conn_device_hdl == 0))
	{
		at_print("\r\n+STATE:0");
	}
	else
	{
		at_print("\r\n+STATE:1");
	}
	return 0;
}

//设置主机模式或者从机模式 0:从机模式，1:主机模式,重启后生效
extern u32 device_mode;
static unsigned char atCmd_Mode(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		if(device_mode == 1) 
			at_print("\r\n+MODE:1");
		else if(device_mode == 2) 
			at_print("\r\n+MODE:2");
		else
			at_print("\r\n+MODE:0");
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		if((pbuf[0] >= '0') && (pbuf[0] <= '2'))
		{
			pbuf[0] -= '0';
			tinyFlash_Write(STORAGE_MODE, (unsigned char*)pbuf, 1);
			return 0;
		}
		else
		{
			return 2;
		}
	}
	else
	{
		return 2;
	}
	return 0;
}

static unsigned char atCmd_Gpio(char *pbuf,  int mode, int length)
{
    const _gpio_t *cmd_ptr = NULL;
    char gpio_name[6];

	if(mode == AT_CMD_MODE_READ)
	{
        cmd_ptr = gpio_ports;
        printf("\r\n");
        for(; cmd_ptr->cmd; cmd_ptr++)
            printf("+GPIO,%s:%d\r\n", cmd_ptr->cmd, gpio_read(cmd_ptr->gpio));
        return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
        if ( (strlen(pbuf) == 4) && (pbuf[3] == '?') )
        {
            strcpy(gpio_name, pbuf);
            gpio_name[3] = '\0';
            cmd_ptr = gpio_ports;
            for(; cmd_ptr->cmd; cmd_ptr++)
            {
                if(strxcmp(cmd_ptr->cmd, gpio_name)) continue;   
                gpio_set_func(cmd_ptr->gpio, AS_GPIO);
                gpio_set_output_en(cmd_ptr->gpio, 0);//disable output
                gpio_set_input_en(cmd_ptr->gpio, 1);//enable input
                printf("\r\n+GPIO,%s:%d\r\n", cmd_ptr->cmd, gpio_read(cmd_ptr->gpio));
                return 0;
            }
            printf("\r\n+GPIO_ERROR: invalid port\r\n");
            return 2;
        }
        if (strlen(pbuf) != 5)
        {
            printf("\r\n+GPIO_ERROR: invalid command length\r\n");
            return 2;
        }
        if ( (pbuf[3] == '^') && ( (pbuf[4] == '0') || (pbuf[4] == '1') || (pbuf[4] == '2') || (pbuf[4] == '3') ) )
        {
            strcpy(gpio_name, pbuf);
            gpio_name[3] = '\0';
            cmd_ptr = gpio_ports;
            for(; cmd_ptr->cmd; cmd_ptr++)
            {
                if(strxcmp(cmd_ptr->cmd, gpio_name)) continue;   
                printf("\r\n+GPIO,%s^%d\r\n", cmd_ptr->cmd, (pbuf[4] - '0'));
                gpio_setup_up_down_resistor(cmd_ptr->gpio, (pbuf[4] - '0'));
                return 0;
            }
            printf("\r\n+GPIO_ERROR: invalid port for up/down reseistor\r\n");
            return 2;
        }
        if ( (pbuf[3] == ':') && ( (pbuf[4] == '0') || (pbuf[4] == '1')) )
            {
            strcpy(gpio_name, pbuf);
            gpio_name[3] = '\0';
            cmd_ptr = gpio_ports;
            for(; cmd_ptr->cmd; cmd_ptr++)
            {
                if(strxcmp(cmd_ptr->cmd, gpio_name)) continue;   
                printf("\r\n+GPIO,%s:%d\r\n", cmd_ptr->cmd, (pbuf[4] == '1'));
                gpio_set_func(cmd_ptr->gpio, AS_GPIO);
                gpio_set_output_en(cmd_ptr->gpio, 1);//enable output
                gpio_set_input_en(cmd_ptr->gpio, 0);//disable input
                gpio_write(cmd_ptr->gpio, (pbuf[4] == '1'));
                return 0;
            }
            printf("\r\n+GPIO_ERROR: invalid assigned port\r\n");
            return 2;
        }
        printf("\r\n+GPIO_ERROR: invalid syntax\r\n");
        return 2;
	}
    return 2;
}

void Scan_Stop()
{
	at_print("OK\r\n");
	blt_soft_timer_delete((blt_timer_callback_t) Scan_Stop);
	blc_ll_setScanEnable (BLC_SCAN_DISABLE, DUP_FILTER_DISABLE);
}
//蓝牙主机模式开始扫描
extern u8 scan_type;
static unsigned char atCmd_Scan(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_SET)
	{
        scan_type = 0;
		if(pbuf[0] == '1') {
            scan_type = 1;
            printf("\r\n+SCAN_SET_CONTINUOUS:%d\r\n", scan_type);
        }
		if(pbuf[0] == '2') {
            scan_type = 2;
            printf("\r\n+SCAN_SET_AUTO:%d\r\n", scan_type);
        }
		if(pbuf[0] == '3') {
            scan_type = 3;
            printf("\r\n+SCAN_SET_AUTO_FILTER:%d\r\n", scan_type);
        }
        tinyFlash_Write(STORAGE_SCAN, &scan_type, 1);
    }
    u8 buff_len = 1;
    if(tinyFlash_Read(STORAGE_SCAN, &scan_type, &buff_len) == 0)
    {
        printf("\r\n+SCAN_TYPE:%d\r\n", scan_type);
    }

	if(device_mode == 1)
	{
		//set scan parameter and scan enable
		//blc_ll_setScanParameter(SCAN_TYPE_ACTIVE, SCAN_INTERVAL_100MS, SCAN_INTERVAL_100MS, OWN_ADDRESS_PUBLIC, SCAN_FP_ALLOW_ADV_ANY);
		blc_ll_setScanParameter(SCAN_TYPE_PASSIVE, SCAN_INTERVAL_100MS, SCAN_INTERVAL_100MS, OWN_ADDRESS_PUBLIC, SCAN_FP_ALLOW_ADV_ANY);
		//blc_ll_setScanEnable (BLC_SCAN_ENABLE, DUP_FILTER_ENABLE);
		blc_ll_setScanEnable (BLC_SCAN_ENABLE, DUP_FILTER_DISABLE);

		if (!scan_type)
            blt_soft_timer_add((blt_timer_callback_t) Scan_Stop, 3000000);//3S
		return 0xff;
	}
    at_print("\r\n+ERR:WRONG_DEVICE_MODE\r\n");

	return 2;
}
//主动断开连接
static unsigned char atCmd_Disconnect(char *pbuf,  int mode, int length)
{
	if(device_mode == 0)  //从机模式
	{
		bls_ll_terminateConnection(HCI_ERR_REMOTE_USER_TERM_CONN);
	}
	else if(device_mode == 1) //主机模式
	{
		blm_ll_disconnect(cur_conn_device_hdl, HCI_ERR_REMOTE_USER_TERM_CONN);
	}
	
	return 0;
}
//主动连接
static unsigned char atCmd_Connect(char *pbuf,  int mode, int length)
{
	//只有是主机模式且未建立连接才能发起连接
	if((mode == AT_CMD_MODE_SET) && (device_mode == 1) && (cur_conn_device_hdl == 0))
	{
		if(length != 12) 
		{
			at_print("len error\r\n");
			return 2;
		}

		if(str2hex(pbuf, 12) == -1 ) return 2;

		pbuf[6] = pbuf[0];
		pbuf[0] = pbuf[5];
		pbuf[5] = pbuf[6];

		pbuf[6] = pbuf[1];
		pbuf[1] = pbuf[4];
		pbuf[4] = pbuf[6];

		pbuf[6] = pbuf[2];
		pbuf[2] = pbuf[3];
		pbuf[3] = pbuf[6];

		blc_ll_createConnection( SCAN_INTERVAL_100MS, SCAN_INTERVAL_100MS, INITIATE_FP_ADV_SPECIFY,  \
								0, (unsigned char *)pbuf, BLE_ADDR_PUBLIC, \
								CONN_INTERVAL_10MS, CONN_INTERVAL_10MS, 0, CONN_TIMEOUT_4S, \
								0, 0xFFFF);
	}
	else
	{
		return 2;
	}

	at_print("Connecting... ...\r\n");
	return 0xff;
}


//AT+SEND=46,4646464646546\r\n
static unsigned char atCmd_Send(char *pbuf,  int mode, int length)
{
	if((device_in_connection_state == 0) && (cur_conn_device_hdl == 0)) //如果蓝牙未连接,或者未开启Notify
	{
		return 2;
	}

	char *tmp = strchr(pbuf,',');
	int len =0;

	if((tmp != NULL) && ((tmp - pbuf) < 4))
	{
		char *data = tmp + 1; //要发送的数据的指针
		char *len_p = pbuf;	 //数据长度指针
		//解析数据长度
		while(tmp != len_p)
		{
			len = len * 10 + (len_p[0] - '0');
			len_p++;
		}

		//检验长度是否一致
		if((len + (data - pbuf)) != length)
		{
			return 2;
		}

		if(device_mode == 0)//当前为从机模式，发送数据到主机
		{
			bls_att_pushNotifyData(SPP_SERVER_TO_CLIENT_DP_H, (u8*)data, len);
		}
		else //当前为主机模式，发送数据到从机
		{
			blc_gatt_pushWriteComand(cur_conn_device_hdl, SPP_SERVER_TO_CLIENT_DP_H,  (u8*)data, len);
		}
		return 0;
	}
	else
	{
		return 2;
	}
}

extern u8 tbl_advData[];
static unsigned char atCmd_Advdata(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		at_print("\r\n+ADVDATA:");
		at_send((char *)(tbl_advData+15), tbl_advData[13] -1);
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		if(length > 16) return 2;
		tinyFlash_Write(STORAGE_ADVDATA, (unsigned char *)pbuf, length);
		return 0;
	}
    return -1;
}

//设置关闭间隙
extern u16 user_adv_interval_ms;
static unsigned char atCmd_Advintv(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+ADVINTV:%d", user_adv_interval_ms);
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		u16 interval = 0;
		while(length--)
		{
			interval = interval * 10 + (pbuf[0] - '0');
			pbuf++;
		}
		tinyFlash_Write(STORAGE_ADVINTV, (unsigned char *)&interval, 2);
		return 0;
	}
    return -1;
}

//设置发射功率
extern u8 user_rf_power_index;
void user_set_rf_power (u8 e, u8 *p, int n);
static unsigned char atCmd_rf_power(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+RFPWR:%d", user_rf_power_index);
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		u8 tmp =  (pbuf[0] - '0');

		if(tmp < 10)
		{
			user_rf_power_index = tmp;
			user_set_rf_power(0,0,0);
			tinyFlash_Write(STORAGE_RFPWR, &user_rf_power_index, 1);
			return 0;
		}
		return 2;
	}
    return -1;
}

 extern u8 ibeacon_data[30];
//设置或者查询iBeacon UUID
static unsigned char atCmd_Ibeacon_UUID(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+IBCNIIUD:%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X", 
										ibeacon_data[ 9], ibeacon_data[10], ibeacon_data[11],ibeacon_data[12],
										ibeacon_data[13], ibeacon_data[14], ibeacon_data[15],ibeacon_data[16],
										ibeacon_data[17], ibeacon_data[18], ibeacon_data[19],ibeacon_data[20],
										ibeacon_data[21], ibeacon_data[22], ibeacon_data[23],ibeacon_data[24]
		);
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		if(length != 32) return 2;

		if(str2hex(pbuf, 32) == -1 ) return 2;

		memcpy(ibeacon_data+9, pbuf, 16);

		tinyFlash_Write(STORAGE_IUUID, (unsigned char *)pbuf, 16);
		return 0;
	}
    return -1;
}

//设置或者查询iBeacon Major
static unsigned char atCmd_Major(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+MAJOR:%02X%02X", ibeacon_data[25], ibeacon_data[26]);
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		if(length != 4) return 2;

		if(str2hex(pbuf, 4) == -1 ) return 2;

		memcpy(ibeacon_data+25, pbuf, 2);

		tinyFlash_Write(STORAGE_IMAJOR, (unsigned char *)pbuf, 2);
		return 0;
	}
    return -1;
}

//设置后者查询iBeacon Minor
static unsigned char atCmd_Minor(char *pbuf,  int mode, int length)
{
	if(mode == AT_CMD_MODE_READ)
	{
		printf("\r\n+MINOR:%02X%02X", ibeacon_data[27],ibeacon_data[28]);
		return 0;
	}
	else if(mode == AT_CMD_MODE_SET)
	{
		if(length != 4) return 2;

		if(str2hex(pbuf, 4) == -1 ) return 2;

		memcpy(ibeacon_data+27, pbuf, 2);
		tinyFlash_Write(STORAGE_IMONOR, (unsigned char *)pbuf, 2);
		return 0;
	}
    return -1;
}

//用于测试开发板
static unsigned char atCmd_Board_test(char *pbuf,  int mode, int length)
{
	gpio_set_func(GPIO_PC2, AS_GPIO);
	gpio_set_func(GPIO_PC3, AS_GPIO);
	gpio_set_func(GPIO_PC4, AS_GPIO);
	gpio_set_func(GPIO_PB4, AS_GPIO);
	gpio_set_func(GPIO_PB5, AS_GPIO);

	gpio_set_output_en(GPIO_PC2, 1);//enable output
	gpio_set_output_en(GPIO_PC3, 1);//enable output
	gpio_set_output_en(GPIO_PC4, 1);//enable output
	gpio_set_output_en(GPIO_PB4, 1);//enable output
	gpio_set_output_en(GPIO_PB5, 1);//enable output

	gpio_set_input_en(GPIO_PC2, 0);//disenable input
	gpio_set_input_en(GPIO_PC3, 0);//disenable input
	gpio_set_input_en(GPIO_PC4, 0);//disenable input
	gpio_set_input_en(GPIO_PB4, 0);//disenable input
	gpio_set_input_en(GPIO_PB5, 0);//disenable input

	while(1)
	{
		gpio_write(GPIO_PC2,1);
		gpio_write(GPIO_PC3,0);
		gpio_write(GPIO_PC4,0);
		gpio_write(GPIO_PB4,0);
		gpio_write(GPIO_PB5,0); WaitMs(200);

		gpio_write(GPIO_PC2,0);
		gpio_write(GPIO_PC3,1);
		gpio_write(GPIO_PC4,0);
		gpio_write(GPIO_PB4,0);
		gpio_write(GPIO_PB5,0); WaitMs(200);

		gpio_write(GPIO_PC2,0);
		gpio_write(GPIO_PC3,0);
		gpio_write(GPIO_PC4,1);
		gpio_write(GPIO_PB4,0);
		gpio_write(GPIO_PB5,0); WaitMs(200);

		gpio_write(GPIO_PC2,0);
		gpio_write(GPIO_PC3,0);
		gpio_write(GPIO_PC4,0);
		gpio_write(GPIO_PB4,1);
		gpio_write(GPIO_PB5,0); WaitMs(200);

		gpio_write(GPIO_PC2,0);
		gpio_write(GPIO_PC3,0);
		gpio_write(GPIO_PC4,0);
		gpio_write(GPIO_PB4,0);
		gpio_write(GPIO_PB5,1); WaitMs(200);
	}
    return 0;
}
//读写命令
_at_command_t gAtCmdTb_writeRead[] =
{ 
	{ "GPIO", 	atCmd_Gpio,	"Write/Read GPIO\r\n"},
	{ "BAUD", 	atCmd_Baud,	"Set/Read BT Baud\r\n"},
	{ "NAME", 	atCmd_Name,	"Set/Read BT Name\r\n"},
	{ "MAC", 	atCmd_Mac,	"Set/Read BT MAC\r\n"},
	{ "READ", 	atCmd_Read,	"Read Flash Data\r\n"},
	{ "MODE", 	atCmd_Mode, "Set/Read BT Mode\r\n"},
	{ "STATE",  atCmd_State,  "State\r\n"},
	{ "SEND", 	atCmd_Send, "Send data to phone\r\n"},
	{ "CONNECT",atCmd_Connect,"Connect other slave device\r\n"},
	{ "ADVDATA",atCmd_Advdata,"Set/Read Adv Data\r\n"},
	{ "ADVINTV",atCmd_Advintv,"Set/Read Adv interval\r\n"},
	{ "LSLEEP", atCmd_LSleep, "Sleep\r\n"},
	{ "RFPWR",  atCmd_rf_power, "RF Power\r\n"},
	{ "IBCNUUID",atCmd_Ibeacon_UUID, "iBeacon UUID\r\n"},
	{ "SCAN",   atCmd_Scan,   "Scan\r\n"},
	{ "MAJOR",  atCmd_Major, "iBeacon Major\r\n"},
	{ "MINOR",  atCmd_Minor, "iBeacon Minor\r\n"},
	{0, 	0,	0}
};
//控制命令
_at_command_t gAtCmdTb_exe[] =
{
	{ "1", 		atCmd_ATE1, "ATE1\r\n"},  //ATE1
	{ "0", 		atCmd_ATE0, "ATE0\r\n"},  //ATE0
	{ "GMR", 	atCmd_GMR,  "GMR\r\n"}, 
	{ "RST", 	atCmd_Reset, "RESET\r\n"}, 
	{ "SLEEP", 	atCmd_Sleep, "Sleep\r\n"}, 	
	{ "LSLEEP", atCmd_LSleep, "Sleep\r\n"},
	{ "RESTORE",atCmd_Restore,"RESTORE\r\n"},
	{ "SCAN",   atCmd_Scan,   "Scan\r\n"},
	{ "DISCONN",atCmd_Disconnect,"disconnect\r\n"},
	{ "BTEST",  atCmd_Board_test,"Board_test\r\n"},
	{0, 	0,	0}
};
