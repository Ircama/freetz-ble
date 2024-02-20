#ifndef __APP_UART_H__
#define __APP_UART_H__

typedef enum {
    AT_BAUD_2400 = 0,
	AT_BAUD_4800,
	AT_BAUD_9600,
	AT_BAUD_19200,
	AT_BAUD_38400,
	AT_BAUD_57600,
	AT_BAUD_115200,
	AT_BAUD_230400,
	AT_BAUD_460800,
	AT_BAUD_921600,
} AT_BAUD;

#endif //__APP_UART_H__