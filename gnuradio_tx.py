import numpy as np
from gnuradio import gr, blocks
import osmosdr
import time, os

PATH = './'
filename = '20250119_2020.csv'
data = []

def hex_to_bin_array(hex_str):
    # 去掉可能的前缀 '0x' 并转换为大写（可选）
    hex_str = hex_str.strip().upper()
    # 将每个16进制字符转为4位二进制字符串并拼接
    bin_str = ''.join(format(int(char, 16), '04b') for char in hex_str)
    # 将二进制字符串转换为01的数组
    bin_array = [int(bit) for bit in bin_str]
    return bin_array

# HackRF 参数
center_freq = 1090e6  # 中心频率，1090 MHz
sample_rate = 10e6     # 采样率
tx_gain = 10          # 发射增益

def main():
    tb = gr.top_block()

    # 创建 HackRF Sink
    hackrf_sink = osmosdr.sink(args="numchan=1 hackrf=0")
    hackrf_sink.set_sample_rate(sample_rate)
    hackrf_sink.set_center_freq(center_freq)
    hackrf_sink.set_gain(tx_gain)
    with open(os.path.join(PATH, filename),'r') as f:
        for line in f:
            tmp = line.strip().split(',')
            if len(tmp) < 1400:
                continue
            tmp = line.strip().split(',')[4:-251]
            tmp = np.array([complex(float(i.split('+j')[0]),float(i.split('+j')[1])) for i in tmp])/2048
            pwm_signal = tmp
            pwm_signal = np.concatenate([pwm_signal,np.zeros(4096-len(pwm_signal),np.complex64)],0)
            for i in range(20):  # 每秒发射一次信号，连续发射 5 次
                print(f"Sending signal batch {i + 1}...")
                
                # 生成动态信号
                pwm_signal = tmp#generate_pwm_signal(i)
                signal_source = blocks.vector_source_c(pwm_signal.tolist(), repeat=True)

                # 动态连接信号源到 HackRF Sink
                tb.connect(signal_source, hackrf_sink)

                # 启动传输
                tb.start()
                # input("Press Enter to stop transmission...")
                # 等待当前信号传输完成
                duration = len(pwm_signal) / sample_rate *200
                time.sleep(duration)
                
                # 停止传输并断开连接
                tb.stop()
                tb.wait()
                tb.disconnect(signal_source, hackrf_sink)

                # 等待 1 秒再发下一次
                time.sleep(5)

    print("Signal transmission completed!")

# def generate_pwm_signal(batch_num):
#     """
#     动态生成 PWM 信号。
#     每次调用生成不同的信号，用于模拟变化的信号内容。
#     """
#     pwm_length = 1024
#     duty_cycle = 0.2 + 0.1 * (batch_num % 5)  # 每次增加占空比
#     pwm_signal = np.zeros(pwm_length, dtype=np.complex64)

#     high_samples = int(pwm_length * duty_cycle)
#     pwm_signal[:high_samples] = 1.0 + 0j
#     pwm_signal[high_samples:] = 0.0 + 0j

#     return pwm_signal

def generate_pwm_signal(batch_num):
    """
    动态生成 PWM 信号。
    每次调用生成不同的信号，用于模拟变化的信号内容。
    """
    msg = '8CFFFFFF423C52D692D953855472'
    header = [1,0,1,0,0,0,0,1,0,1,0,0,0,0,0,0]
    bit_sequence = hex_to_bin_array(msg)
    tmp = []
    for i in bit_sequence:
        if i == 0:
            tmp.extend([0,1])
        else:
            tmp.extend([1,0])
    header.extend(tmp)
    end = [0]*500
    header.extend(end)
    bin_msg = np.array(header)
    bin_msg = np.repeat(bin_msg,5)
    pwm_signal = np.array(bin_msg,np.complex64)
    pwm_signal = np.concatenate([pwm_signal,np.zeros(4096-len(pwm_signal),np.complex64)])

    return pwm_signal

if __name__ == "__main__":
    
    
            
            # time.sleep(5)
    main()
