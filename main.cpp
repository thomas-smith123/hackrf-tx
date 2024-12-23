/* Mode1090, a Mode S messages decoder for RTLSDR devices.
 *
 * Copyright (C) 2012 by Salvatore Sanfilippo <antirez@gmail.com>
 *
 * HackRF One support added by Ilker Temir <ilker@ilkertemir.com>
 *
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 * 
 *  *  Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *
 *  *  Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdio.h>
#include "iostream"
#include <string.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdint.h>
#include <errno.h>
#include <unistd.h>
#include <math.h>
#include <sys/time.h>
#include <signal.h>
#include <fcntl.h>
#include <ctype.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/select.h>
#include "rtl-sdr.h"
#include "libhackrf/hackrf.h"
#include <time.h>
#include <string.h>
#include <unistd.h> // 在gcc编译器中，使用的头文件因gcc版本的不同而不同
using namespace std;

#define MODES_DEFAULT_RATE         8000000
#define MODES_DEFAULT_FREQ         2400000000
#define MODES_DEFAULT_WIDTH        1000
#define MODES_DEFAULT_HEIGHT       700
#define MODES_ASYNC_BUF_NUMBER     12
#define MODES_DATA_LEN             (16*16384)//*4   /* 256k */
#define MODES_AUTO_GAIN            -100         /* Use automatic gain. */
#define MODES_MAX_GAIN             999999       /* Use max available gain. */
/* HackRF One Defaults */
#define MODES_ENABLE_AMP 	   0
#define MODES_LNA_GAIN 	           10
#define MODES_VGA_GAIN 	           48


#define MODES_PREAMBLE_US 8       /* microseconds */
#define MODES_LONG_MSG_BITS 112
#define MODES_SHORT_MSG_BITS 56
#define MODES_FULL_LEN (MODES_PREAMBLE_US+MODES_LONG_MSG_BITS)
#define MODES_LONG_MSG_BYTES (112/8)
#define MODES_SHORT_MSG_BYTES (56/8)

#define MODES_ICAO_CACHE_LEN 1024 /* Power of two required. */
#define MODES_ICAO_CACHE_TTL 60   /* Time to live of cached addresses. */
#define MODES_UNIT_FEET 0
#define MODES_UNIT_METERS 1

#define MODES_DEBUG_DEMOD (1<<0)
#define MODES_DEBUG_DEMODERR (1<<1)
#define MODES_DEBUG_BADCRC (1<<2)
#define MODES_DEBUG_GOODCRC (1<<3)
#define MODES_DEBUG_NOPREAMBLE (1<<4)
#define MODES_DEBUG_NET (1<<5)
#define MODES_DEBUG_JS (1<<6)


/* When debug is set to MODES_DEBUG_NOPREAMBLE, the first sample must be
 * at least greater than a given level for us to dump the signal. */
#define MODES_DEBUG_NOPREAMBLE_LEVEL 25

#define MODES_INTERACTIVE_REFRESH_TIME 250      /* Milliseconds */
#define MODES_INTERACTIVE_ROWS 15               /* Rows on screen */
#define MODES_INTERACTIVE_TTL 60                /* TTL before being removed */

#define MODES_NET_MAX_FD 1024
#define MODES_NET_OUTPUT_SBS_PORT 30003
#define MODES_NET_OUTPUT_RAW_PORT 30002
#define MODES_NET_INPUT_RAW_PORT 30001
#define MODES_NET_HTTP_PORT 8080
#define MODES_CLIENT_BUF_SIZE 1024
#define MODES_NET_SNDBUF_SIZE (1024*64)

#define MODES_NOTUSED(V) ((void) V)


#define SAMPLE_RATE 10000000      // 采样率 (1 MHz)
// #define CENTER_FREQ 1090000000    // 中心频率 (915 MHz)
#define BUFFER_SIZE 262144       // 缓冲区大小 (256 KB)
#define SINE_FREQ 1000000          // 正弦波频率 (10 kHz)


/* Program global state. */
hackrf_device *device;
int init()
{
    int status;
    status = hackrf_init();
    if (status!=hackrf_error::HACKRF_SUCCESS)
    {
        std::cout<<"Fail to init."<<std::endl;
        hackrf_exit();
        return -1;
    }
    else
        std::cout<<"Init success"<<std::endl;
    status = hackrf_open(&device);    
    if (status!=hackrf_error::HACKRF_SUCCESS)
    {
        std::cout<<"Fail to open."<<std::endl;
        hackrf_exit();
        return -1;
    }
    else
        std::cout<<"Open success."<<std::endl;
    status = hackrf_set_freq(device, MODES_DEFAULT_FREQ);
    if (status!=hackrf_error::HACKRF_SUCCESS)
    {
        std::cout<<"Fail to set freq."<<std::endl;
        hackrf_exit();
        return -1;
    }
    else
        std::cout<<"Set freq success."<<std::endl;
    status = hackrf_set_sample_rate(device, MODES_DEFAULT_RATE);
    if (status!=hackrf_error::HACKRF_SUCCESS)
    {
        std::cout<<"Fail to set sample rate."<<std::endl;
        hackrf_exit();
        return -1;
    }
    else
        std::cout<<"Set sample rate success."<<std::endl;
    status = hackrf_set_amp_enable(device, MODES_ENABLE_AMP);
    if (status!=hackrf_error::HACKRF_SUCCESS)
    {
        std::cout<<"Fail to set amp enable."<<std::endl;
        hackrf_exit();
        return -1;
    }
    else
        std::cout<<"Set amp enable success."<<std::endl;
    status = hackrf_set_txvga_gain(device,0);
    if (status!=hackrf_error::HACKRF_SUCCESS)
    {
        std::cout<<"Fail to set tx amp."<<std::endl;
        hackrf_exit();
        return -1;
    }
    else
        std::cout<<"Set tx amp enable success."<<std::endl;
    return 0;

}
void generate_sine_wave(unsigned char *buffer, int length, double amplitude) {
    for (int i = 0; i < length; i++) {
        double t = (double)i / SAMPLE_RATE; // 计算时间点
        double sample = amplitude * sin(2.0 * M_PI * SINE_FREQ * t); // 正弦波信号
        unsigned char iq_sample = (unsigned char)((sample + 1.0) * 127.5); // 将信号范围 [-1, 1] 转换到 [0, 255]
        buffer[i] = iq_sample; // 存入缓冲区
    }
}
// HackRF 传输回调函数
int tx_callback(hackrf_transfer *transfer) {
    static unsigned char buffer[BUFFER_SIZE];
    static int initialized = 0;

    // 生成正弦波数据（仅生成一次，循环复用）
    if (!initialized) {
        generate_sine_wave(buffer, BUFFER_SIZE, 0.8); // 生成 0.8 振幅的正弦波
        initialized = 1;
    }

    // 将缓冲区中的数据拷贝到传输缓冲区
    memcpy(transfer->buffer, buffer, BUFFER_SIZE);
    return 0; // 返回 0 表示成功
}

int main(int argc, char **argv) {
    
    std::cout<<"Start:";
    int status;
    if (init()==-1)
        return -1;
    else
        cout<<"init done."<<endl;

    status = hackrf_start_tx(device, tx_callback, NULL);
    if (status != hackrf_error::HACKRF_SUCCESS) {
        cout<<"Fail to tx."<<endl;
        hackrf_close(device);
        hackrf_exit();
        return -1;
    }
    sleep(10);
    hackrf_stop_tx(device);
    hackrf_close(device);
    hackrf_exit();
    return 0;
    
}


