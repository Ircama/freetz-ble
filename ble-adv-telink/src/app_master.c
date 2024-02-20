/********************************************************************************************************
 * @file     feature_data_len_extension.c
 *
 * @brief    for TLSR chips
 *
 * @author	 public@telink-semi.com;
 * @date     May. 10, 2018
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

#include <stack/ble/ble.h>
#include "tl_common.h"
#include "drivers.h"
#include "app_config.h"
#include "vendor/common/blt_common.h"


#define FEATURE_PM_ENABLE								0
#define FEATURE_DEEPSLEEP_RETENTION_ENABLE				0

//need define att handle same with slave(Here: we use 8258 feature_test/slave_dle demo as slave device)
#define			SPP_HANDLE_DATA_S2C			0x11
#define			SPP_HANDLE_DATA_C2S			0x15


#define MTU_SIZE_SETTING   			 		247
#define DLE_TX_SUPPORTED_DATA_LEN    		MAX_OCTETS_DATA_LEN_EXTENSION //264-12 = 252 > Tx max:251



#define RX_FIFO_SIZE						288  //rx-24   max:251+24 = 275  16 align-> 288
#define RX_FIFO_NUM							8

#define TX_FIFO_SIZE						264  //tx-12   max:251+12 = 263  4 align-> 264
#define TX_FIFO_NUM							8

MYFIFO_INIT(blt_rxfifo, RX_FIFO_SIZE, RX_FIFO_NUM);
MYFIFO_INIT(blt_txfifo, TX_FIFO_SIZE, TX_FIFO_NUM);

static u32 host_update_conn_param_req;
static u16 host_update_conn_min;
static u16 host_update_conn_latency;
static u16 host_update_conn_timeout;
static u32 connect_event_occurTick;
//static u32 mtuExchange_check_tick;
static u32 dle_started_flg;
static u32 mtuExchange_started_flg;
//static u32 dongle_pairing_enable;
//static u32 dongle_unpair_enable;
static u32 final_MTU_size = 23;
_attribute_data_retention_ u32 cur_conn_device_hdl; //conn_handle

// from app_uart.c:
extern void at_print_array(char * data, u32 len);
extern void at_send(char * data, u32 len);
extern void at_print(char * str);

#ifdef TEST_CODED_PHY
#define	APP_ADV_SETS_NUMBER						1			// Number of Supported Advertising Sets
#define APP_MAX_LENGTH_ADV_DATA					1024		// Maximum Advertising Data Length,   (if legacy ADV, max length 31 bytes is enough)
#define APP_MAX_LENGTH_SCAN_RESPONSE_DATA		31			// Maximum Scan Response Data Length, (if legacy ADV, max length 31 bytes is enough)

static	u8	app_adv_set_param[ADV_SET_PARAM_LENGTH * APP_ADV_SETS_NUMBER]; // struct ll_ext_adv_t
static	u8	app_primary_adv_pkt[MAX_LENGTH_PRIMARY_ADV_PKT * APP_ADV_SETS_NUMBER];
static	u8	app_secondary_adv_pkt[MAX_LENGTH_SECOND_ADV_PKT * APP_ADV_SETS_NUMBER];
static	u8	app_advData[APP_MAX_LENGTH_ADV_DATA	* APP_ADV_SETS_NUMBER];
static	u8	app_scanRspData[APP_MAX_LENGTH_SCAN_RESPONSE_DATA * APP_ADV_SETS_NUMBER];
#endif  //TEST_CODED_PHY

int app_l2cap_handler (u16 conn_handle, u8 *raw_pkt)
{
	
	//l2cap data packeted, make sure that user see complete l2cap data
	rf_packet_l2cap_t *ptrL2cap = blm_l2cap_packet_pack (conn_handle, raw_pkt);
	if (!ptrL2cap)
		return 0;

	//l2cap data channel id, 4 for att, 5 for signal, 6 for smp
	if(ptrL2cap->chanId == L2CAP_CID_ATTR_PROTOCOL)  //att data
	{
		rf_packet_att_t *pAtt = (rf_packet_att_t*)ptrL2cap;
#ifdef ATT_HANDLE
        u16 attHandle = pAtt->handle0 | pAtt->handle1<<8;
#endif
		if(pAtt->opcode == ATT_OP_EXCHANGE_MTU_REQ || pAtt->opcode == ATT_OP_EXCHANGE_MTU_RSP)
		{
			rf_packet_att_mtu_exchange_t *pMtu = (rf_packet_att_mtu_exchange_t*)ptrL2cap;

			if(pAtt->opcode ==  ATT_OP_EXCHANGE_MTU_REQ){
				blc_att_responseMtuSizeExchange(conn_handle, MTU_SIZE_SETTING);
			}

			u16 peer_mtu_size = (pMtu->mtu[0] | pMtu->mtu[1]<<8);
			final_MTU_size = min(MTU_SIZE_SETTING, peer_mtu_size);

			blt_att_setEffectiveMtuSize(cur_conn_device_hdl , final_MTU_size); //stack API, user can not change


			mtuExchange_started_flg = 1;   //set MTU size exchange flag here

			printf("Final MTU size:%d\n", final_MTU_size);
		}
		else if(pAtt->opcode == ATT_OP_HANDLE_VALUE_NOTI)  //slave handle notify
		{
#ifdef ATT_HANDLE
			if(attHandle == SPP_HANDLE_DATA_S2C)
			{
			 	u8 len = pAtt->l2capLen - 3;
			 	if(len > 0)
			 	{
			 		printf("RF_RX len: %d\ns2c:notify data: %d\n", pAtt->rf_len, len);
					array_printf(pAtt->dat, len);
			    }
			}
#endif
			u8 len = pAtt->l2capLen - 3;

			printf("+DATA:%d,", len);
			at_send((char *)pAtt->dat, len);
			at_print("\r\n");	
		}
	}
	else if(ptrL2cap->chanId == L2CAP_CID_SIG_CHANNEL)  //signal
	{
		if(ptrL2cap->opcode == L2CAP_CMD_CONN_UPD_PARA_REQ)  //slave send conn param update req on l2cap
		{
			rf_packet_l2cap_connParaUpReq_t  * req = (rf_packet_l2cap_connParaUpReq_t *)ptrL2cap;

			u32 interval_us = req->min_interval*1250;  //1.25ms unit
			u32 timeout_us = req->timeout*10000; //10ms unit
			u32 long_suspend_us = interval_us * (req->latency+1);

			//interval < 200ms, long suspend < 11S, interval * (latency +1)*2 <= timeout
			if( interval_us < 200000 && long_suspend_us < 20000000 && (long_suspend_us*2<=timeout_us) )
			{
				//when master host accept slave's conn param update req, should send a conn param update response on l2cap
				//with CONN_PARAM_UPDATE_ACCEPT; if not accpet,should send  CONN_PARAM_UPDATE_REJECT
				blc_l2cap_SendConnParamUpdateResponse(conn_handle, req->id, CONN_PARAM_UPDATE_ACCEPT);  //send SIG Connection Param Update Response

				printf("send SIG Connection Param Update accept\n");

				//if accept, master host should mark this, add will send  update conn param req on link layer later set a flag here, then send update conn param req in mainloop
				host_update_conn_param_req = clock_time() | 1 ; //in case zero value
				host_update_conn_min = req->min_interval;  //backup update param
				host_update_conn_latency = req->latency;
				host_update_conn_timeout = req->timeout;
			}
			else
			{
				blc_l2cap_SendConnParamUpdateResponse(conn_handle, req->id, CONN_PARAM_UPDATE_REJECT);  //send SIG Connection Param Update Response
				printf("send SIG Connection Param Update reject\n");
			}
		}
	}
	else if(ptrL2cap->chanId == L2CAP_CID_SMP) //smp
	{

	}
	
	return 0;
}

//////////////////////////////////////////////////////////
// event call back
//////////////////////////////////////////////////////////
extern u8 scan_type;
int controller_event_callback(u32 h, u8 *p, int n)
{
	// at_print_array(&h, 4);
	// at_print(" controller_event_callback\n");
    
    u8 found = 0;
#ifdef DEBUG_ADV
#pragma message ( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>> DEBUG_ADV enabled" )
    printf("ADV DEBUG - ");
    int adv_debug_type=0;
#endif

	if (h &HCI_FLAG_EVENT_BT_STD)		//ble controller hci event
	{
		u8 evtCode = h & 0xff;
#ifdef DEBUG_ADV
        u8 subEvt_code1 = p[0];
        adv_debug_type = 0;
        if (evtCode == HCI_EVT_LE_META)
            adv_debug_type = 1;
        if ( (subEvt_code1 == HCI_SUB_EVT_LE_ADVERTISING_REPORT) && (evtCode == HCI_EVT_LE_META) )
            adv_debug_type = 2;
        printf("%d, evtCode=%d, subEvt_code=%d, n=%d\n", adv_debug_type, evtCode, subEvt_code1, n);
#endif
		//------------ disconnect -------------------------------------
		if(evtCode == HCI_EVT_DISCONNECTION_COMPLETE)  //connection terminate
		{
			event_disconnection_t	*pd = (event_disconnection_t *)p;

			//terminate reason//connection timeout
			if(pd->reason == HCI_ERR_CONN_TIMEOUT){
			}
			//peer device(slave) send terminate cmd on link layer
			else if(pd->reason == HCI_ERR_REMOTE_USER_TERM_CONN){
			}
			//master host disconnect( blm_ll_disconnect(current_connHandle, HCI_ERR_REMOTE_USER_TERM_CONN) )
			else if(pd->reason == HCI_ERR_CONN_TERM_BY_LOCAL_HOST){
			}
			 //master create connection, send conn_req, but did not received acked packet in 6 connection event
			else if(pd->reason == HCI_ERR_CONN_FAILED_TO_ESTABLISH){ //send connection establish event to host(telink defined event)
			}
			else{
			}

			printf("+DISCONNECT(%x)\r\n", pd->reason);
			gpio_write(CONN_STATE_GPIO, 0);
			
			connect_event_occurTick = 0;
			host_update_conn_param_req = 0; //when disconnect, clear update conn flag
			cur_conn_device_hdl = 0;  //when disconnect, clear conn handle

			//MTU size exchange and data length exchange procedure must be executed on every new connection,
			//so when connection terminate, relative flags must be cleared
			dle_started_flg = 0;
			mtuExchange_started_flg = 0;

			//MTU size reset to default 23 bytes when connection terminated
			blt_att_resetEffectiveMtuSize(pd->handle | (pd->hh<<8));  //stack API, user can not change

			//should set scan mode again to scan slave adv packet
			//blc_ll_setScanParameter(SCAN_TYPE_PASSIVE, SCAN_INTERVAL_100MS, SCAN_INTERVAL_100MS, OWN_ADDRESS_PUBLIC, SCAN_FP_ALLOW_ADV_ANY);
			//blc_ll_setScanEnable (BLC_SCAN_ENABLE, DUP_FILTER_DISABLE);

		}
		else if(evtCode == HCI_EVT_LE_META)
		{
			u8 subEvt_code = p[0];

			//------hci le event: le connection establish event---------------------------------
			if(subEvt_code == HCI_SUB_EVT_LE_CONNECTION_ESTABLISH)  //connection establish(telink private event)
			{
				event_connection_complete_t *pCon = (event_connection_complete_t *)p;

				if (pCon->status == BLE_SUCCESS)	// status OK
				{
					gpio_write(CONN_STATE_GPIO, 1);
					at_print("OK\r\n");
					cur_conn_device_hdl = pCon->handle;   //mark conn handle, in fact this equals to BLM_CONN_HANDLE
					connect_event_occurTick = clock_time()|1;
				}
			}
			//--------hci le event: le adv report event ----------------------------------------
			else if (subEvt_code == HCI_SUB_EVT_LE_ADVERTISING_REPORT)	// ADV packet
			{
				//after controller is set to scan state, it will report all the adv packet it received by this event
				event_adv_report_t *pa = (event_adv_report_t *)p;
				s8 rssi = pa->data[pa->len];

				if(rssi == 0) return 1;

                found = 0;
                if ((pa->mac[5] == 0xA4) && (pa->mac[4] == 0xC1) && (pa->mac[3] == 0x38))  // Telink Semiconductor (Taipei) Co. Ltd
                {
                    found = 1;
                    gpio_write(GPIO_PC2,1);
                    gpio_write(GPIO_PC3,0);
                    gpio_write(GPIO_PC4,0);
                }
                else if ((pa->mac[5] == 0x54) && (pa->mac[4] == 0xEF) && (pa->mac[3] == 0x44))  // Lumi United Technology Co., Ltd
                {
                    found = 1;
                    gpio_write(GPIO_PC2,0);
                    gpio_write(GPIO_PC3,1);
                    gpio_write(GPIO_PC4,0);
                }
                else if ((pa->mac[5] == 0xE4) && (pa->mac[4] == 0xAA) && (pa->mac[3] == 0xEC))  // Tianjin Hualai Tech Co, Ltd
                {
                    found = 1;
                    gpio_write(GPIO_PC2,0);
                    gpio_write(GPIO_PC3,0);
                    gpio_write(GPIO_PC4,1);
                }
                else
                {
                    gpio_write(GPIO_PC2,0);
                    gpio_write(GPIO_PC3,0);
                    gpio_write(GPIO_PC4,0);
                }
                
                if ((scan_type != 3) || found) {
                    printf("+ADV:%d,%02X%02X%02X%02X%02X%02X,", rssi,pa->mac[5],pa->mac[4],pa->mac[3],pa->mac[2],pa->mac[1],pa->mac[0]);
                    at_print_array((char *)pa->data, pa->len);				
                    at_print("\r\n");
                }
			}
			//--------hci le event: le data length change event ----------------------------------------
			else if (subEvt_code == HCI_SUB_EVT_LE_DATA_LENGTH_CHANGE)
			{
#ifdef DATA_LENGTH_CHANGE
#pragma message ( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>> DATA_LENGTH_CHANGE enabled" )
                hci_le_dataLengthChangeEvt_t* dle_param = (hci_le_dataLengthChangeEvt_t*)p;
				printf("----- DLE exchange: -----\n");
				printf("Effective Max Rx Octets: %d\n", dle_param->maxRxOct);
				printf("Effective Max Tx Octets: %d\n", dle_param->maxTxOct);
#endif
				dle_started_flg = 1;
			}	
		}
	}
	
	return 0;
}

extern u8  mac_public[6];
extern u8  mac_random_static[6];
void ble_master_init_normal(void)
{
	//random number generator must be initiated here( in the beginning of user_init_nromal)
	//when deepSleep retention wakeUp, no need initialize again
	random_generator_init();  //this is must

	blc_initMacAddress(CFG_ADR_MAC, mac_public, mac_random_static);

	////// Controller Initialization  //////////
	blc_ll_initBasicMCU();
	blc_ll_initStandby_module(mac_public);				//mandatory
	blc_ll_initScanning_module(mac_public); 	//scan module: 		 mandatory for BLE master,
	blc_ll_initInitiating_module();			//initiate module: 	 mandatory for BLE master,
	blc_ll_initConnection_module();						//connection module  mandatory for BLE slave/master
	blc_ll_initMasterRoleSingleConn_module();			//master module: 	 mandatory for BLE master,


#ifdef TEST_CODED_PHY
#pragma message ( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>> TEST_CODED_PHY enabled" )
    blc_ll_init2MPhyCodedPhy_feature();                            // Coded PHY
    blc_ll_setPhy(BLM_CONN_HANDLE, PHY_TRX_PREFER, PHY_PREFER_CODED, PHY_PREFER_CODED, CODED_PHY_PREFER_S8);

    // patch, set advertise prepare user cb (app_advertise_prepare_handler)
    blc_ll_setDefaultPhy(PHY_TRX_PREFER, BLE_PHY_CODED, BLE_PHY_CODED);

    blc_ll_setDefaultConnCodingIndication(CODED_PHY_PREFER_S8);    // set Default Connection Coding
    blc_ll_initChannelSelectionAlgorithm_2_feature();              // set CSA2

    blc_ll_initExtendedAdvertising_module(app_adv_set_param, app_primary_adv_pkt, APP_ADV_SETS_NUMBER);
    blc_ll_initExtSecondaryAdvPacketBuffer(app_secondary_adv_pkt, MAX_LENGTH_SECOND_ADV_PKT);
    blc_ll_initExtAdvDataBuffer(app_advData, APP_MAX_LENGTH_ADV_DATA);
    blc_ll_initExtScanRspDataBuffer(app_scanRspData, APP_MAX_LENGTH_SCAN_RESPONSE_DATA);

	u32 my_adv_interval_min = ADV_INTERVAL_50MS;
	u32 my_adv_interval_max = ADV_INTERVAL_50MS;

	le_phy_type_t  user_primary_adv_phy;
	le_phy_type_t  user_secondary_adv_phy;

    // if Coded PHY is used, this API set default S2/S8 mode for Extended ADV
    user_primary_adv_phy   = BLE_PHY_CODED;
    //user_secondary_adv_phy = BLE_PHY_1M;
    user_secondary_adv_phy = BLE_PHY_CODED;
    // if Coded PHY is used, this API set default S2/S8 mode for Extended ADV
    blc_ll_setDefaultExtAdvCodingIndication(ADV_HANDLE0, CODED_PHY_PREFER_S8);

	blc_ll_setExtAdvParam( ADV_HANDLE0, 		ADV_EVT_PROP_EXTENDED_NON_CONNECTABLE_NON_SCANNABLE_UNDIRECTED, my_adv_interval_min, 			my_adv_interval_max,
						   BLT_ENABLE_ADV_ALL,	OWN_ADDRESS_PUBLIC, 										    BLE_ADDR_PUBLIC, 				NULL,
						   ADV_FP_NONE,  		TX_POWER_8dBm,												   	user_primary_adv_phy, 			0,
						   user_secondary_adv_phy, 	ADV_SID_0, 													0);

    blc_ll_setExtAdvEnable_1( BLC_ADV_ENABLE, 1, ADV_HANDLE0, 0 , 0);
#endif

#ifdef TEST_B_CODED_PHY
#pragma message ( ">>>>>>>>>>>>>>>>>>>>>>>>>>>>> TEST_B_CODED_PHY enabled" )
    blc_ll_setExtScanParam_1_phy(
        OWN_ADDRESS_PUBLIC, SCAN_FP_ALLOW_ADV_ANY, 5, \
        SCAN_TYPE_PASSIVE,  SCAN_INTERVAL_100MS,   80
    );
#endif

	rf_set_power_level_index (RF_POWER_P3p01dBm);

	////// Host Initialization  //////////
	blc_gap_central_init();										//gap initialization
	blc_l2cap_register_handler (app_l2cap_handler);    			//l2cap initialization
	blc_hci_registerControllerEventHandler(controller_event_callback); //controller hci event to host all processed in this func

	//bluetooth event
	blc_hci_setEventMask_cmd (HCI_EVT_MASK_DISCONNECTION_COMPLETE | HCI_EVT_MASK_ENCRYPTION_CHANGE);

	//bluetooth low energy(LE) event
	blc_hci_le_setEventMask_cmd(
        HCI_LE_EVT_MASK_CONNECTION_COMPLETE
        | HCI_LE_EVT_MASK_ADVERTISING_REPORT
        | HCI_LE_EVT_MASK_CONNECTION_UPDATE_COMPLETE
#ifdef TEST_CODED_PHY
        | HCI_LE_EVT_MASK_EXTENDED_ADVERTISING_REPORT
#endif
        | HCI_LE_EVT_MASK_DATA_LENGTH_CHANGE
        | HCI_LE_EVT_MASK_CONNECTION_ESTABLISH
    ); //connection establish: telink private event

	//ATT initialization
	blc_att_setRxMtuSize(MTU_SIZE_SETTING); //If not set RX MTU size, default is: 23 bytes.

	//NO SMP process
	blc_smp_setSecurityLevel(No_Security);

	bls_pm_setSuspendMask (SUSPEND_DISABLE);

	WaitMs(100);

	gpio_write(LOWPWR_STATE_GPIO, 1);//将低功耗状态指示置1，主机模式暂不支持低功耗
}

_attribute_ram_code_ void ble_master_init_deepRetn(void)
{

}

void ble_master_mainloop(void)
{
	/////////////////////////////////////// HCI ///////////////////////////////////////
	blc_hci_proc ();

	if(blc_ll_getCurrentState() == BLS_LINK_STATE_CONN)//still in connection state
	{  
		//at_print("BLS_LINK_STATE_CONN\r\n");
		//blm_ll_updateConnection (cur_conn_device_hdl, host_update_conn_min, host_update_conn_min, host_update_conn_latency,  host_update_conn_timeout, 0, 0 );
	}
}
