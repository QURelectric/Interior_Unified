// demo: CAN-BUS Shield, send data

////////////////// MESSAGE SUMMARY ////////////////////
/* Data is sent in three, 8-byte messages
    Message 1 (from MOST significant byte to LEAST):
        batterySOC          (as a percentage)
        MotorTemp           ([0; +255] ↔ [-40; +215]°C)
        InverterTemp        ([0; +255] ↔ [-40; +215]°C)
        -
        -
        -
        -
        -
    Message 2:
        MotorFlags          
        MotorFlags
        SystemFlags
        SystemFlags
        OperatingTime       (Hour)
        OperatingTime       (Hour)
        OperatingTime       (Minute)
        OperatingTime       (Second)
    Message 3:
        FaultLevel
        FaultCode
        Odometer            (Floating point number x10, divide by 10 to decode)
        Odometer
        Current             (Floating point number x10, divide by 10 to decode)
        Current
        Speed               (Floating point number x10, divide by 10 to decode)
        Speed
*/



#include <SPI.h>

#define CAN_2515
#include "mcp2515_can.h"

const int SPI_CS_PIN = 10;
mcp2515_can CAN(SPI_CS_PIN);

// CAN IDs
#define MSG1_ID 0x100
#define MSG2_ID 0x101
#define MSG3_ID 0x102

void setup()
{
    SERIAL_PORT_MONITOR.begin(115200);

    while (CAN_OK != CAN.begin(CAN_500KBPS))
    {
        SERIAL_PORT_MONITOR.println("CAN init fail, retry...");
        delay(100);
    }

    SERIAL_PORT_MONITOR.println("CAN init ok!");
}

void loop()
{

/**********************
 MSG 1
**********************/
uint8_t msg1[8];

msg1[0] = 72;   // batterySOC
msg1[1] = 50;   // MotorTemp (offset of 40 degrees C. For example, a bit pattern of 00000001 is actually -39 degrees)
msg1[2] = 55;   // InverterTemp (offset of 40 degrees C)
msg1[3] = 0;
msg1[4] = 0;
msg1[5] = 0;
msg1[6] = 0;
msg1[7] = 0;

CAN.sendMsgBuf(MSG1_ID, 0, 8, msg1);


/**********************
 MSG 2
**********************/

uint16_t MotorFlag = 0; // See manual for what each of the 16 flags indicate
uint16_t SystemFlags = 0; // See manual for what each of the 16 flags indicate
uint32_t OperatingTime = 1000; // 100.0 scaled x10

uint8_t msg2[8];

msg2[0] = (MotorFlag >> 8) & 0xFF;
msg2[1] = MotorFlag & 0xFF;

msg2[2] = (SystemFlags >> 8) & 0xFF;
msg2[3] = SystemFlags & 0xFF;

msg2[4] = (OperatingTime >> 24) & 0xFF;
msg2[5] = (OperatingTime >> 16) & 0xFF;
msg2[6] = (OperatingTime >> 8) & 0xFF;
msg2[7] = OperatingTime & 0xFF;

CAN.sendMsgBuf(MSG2_ID, 0, 8, msg2);


/**********************
 MSG 3
**********************/

uint8_t FaultLevel = 0;
uint8_t FaultCode = 0;

uint16_t Odometer = 0.0;  // 10.0 scaled x10
uint16_t Current = 0.0;  // 10.0 scaled x10
uint16_t Speed = 100;  // 10.0 scaled x10

uint8_t msg3[8];

msg3[0] = FaultLevel;
msg3[1] = FaultCode;

msg3[2] = (Odometer >> 8) & 0xFF;
msg3[3] = Odometer & 0xFF;

msg3[4] = (Current >> 8) & 0xFF;
msg3[5] = Current & 0xFF;

msg3[6] = (Speed >> 8) & 0xFF;
msg3[7] = Speed & 0xFF;

CAN.sendMsgBuf(MSG3_ID, 0, 8, msg3);


delay(1000);

}