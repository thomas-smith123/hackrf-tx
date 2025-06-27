import numpy as np
import uhd
import time, os
from datetime import datetime, timedelta
import tqdm

PATH = './'
filename1 = '20250219_2306.csv'
filename2 = '20250221_1806.csv'

def hex_to_bin_array(hex_str):
    hex_str = hex_str.strip().upper()
    bin_str = ''.join(format(int(char, 16), '04b') for char in hex_str)
    return [int(bit) for bit in bin_str]

# UHD 设备参数
center_freq = 1091e6  # 中心频率 1091 MHz
sample_rate = 10e6     # 采样率 10 MHz
tx_gain = 50          # 发射增益
tx_channel = 0        # 通道 0
dev_args = ""         # 设备参数 (根据设备调整)

def main(filename, num_records=250):
    # 创建USRP对象
    usrp = uhd.usrp.MultiUSRP(dev_args)
    
    # 设置发射参数
    usrp.set_tx_rate(sample_rate, tx_channel)
    usrp.set_tx_freq(uhd.types.TuneRequest(center_freq), tx_channel)
    usrp.set_tx_gain(tx_gain, tx_channel)
    
    # 创建发送流
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = [tx_channel]
    tx_streamer = usrp.get_tx_stream(st_args)
    
    # 设置元数据
    md = uhd.types.TXMetadata()
    md.start_of_burst = True
    md.end_of_burst = False
    md.has_time_spec = False
    
    with open(os.path.join(PATH, filename), 'r') as f:
        total_row = sum(1 for _ in f)
        f.seek(0)
        cnt = 0
        pbar = tqdm.tqdm(total=total_row, desc=f"Processing {filename}", unit="record")
        while cnt < total_row:
            # 计算当前批次要读取的记录数
            records_to_read = min(num_records, total_row - cnt)
            pwm_signal = []
            
            # 读取并处理数据
            for _ in range(records_to_read):
                line = f.readline().strip()
                if not line:
                    continue
                tmp = line.split(',')
                if len(tmp) < 1400:
                    continue
                tmp = tmp[4:4+1300]
                # 转换为复数并归一化
                complex_data = [complex(float(i.split('+j')[0]), float(i.split('+j')[1]))/2048 
                                for i in tmp]
                pwm_signal.append(np.array(complex_data + [0j]*200, dtype=np.complex64))
                cnt += 1
            
            if not pwm_signal:
                continue
                
            # 合并所有记录
            pwm_signal = np.concatenate(pwm_signal)
            
            for i in range(4):  # 重复发送3次
                print(f"Sending signal batch {i+1}...")
                
                # 发送数据
                num_tx = tx_streamer.send(pwm_signal, md)
                
                # 计算发送持续时间
                duration = len(pwm_signal) / sample_rate
                time.sleep(duration)  # 等待发送完成
                
                # 等待7秒间隔
                time.sleep(5)
            pbar.update(records_to_read)
    # 发送结束包
    md.end_of_burst = True
    tx_streamer.send(np.zeros(0, dtype=np.complex64), md)
    print("Signal transmission completed!")

def generate_pwm_signal(batch_num):
    """生成PWM信号（如果需要）"""
    msg = '8F7C48125C0D26E63F843E8D2A2F'
    header = [1,0,1,0,0,0,0,1,0,1,0,0,0,0,0,0]
    bit_sequence = hex_to_bin_array(msg)
    tmp = []
    for i in bit_sequence:
        tmp.extend([0,1] if i == 0 else [1,0])
    header.extend(tmp)
    header.extend([0]*500)
    bin_msg = np.repeat(np.array(header), 5)
    pwm_signal = np.zeros(4096, dtype=np.complex64)
    pwm_signal[:len(bin_msg)] = bin_msg
    return pwm_signal

if __name__ == "__main__":
    # main(filename1)
    main(filename2)
