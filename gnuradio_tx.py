#
# @Date: 2025-01-15 22:18:42
# @LastEditors: error: error: git config user.name & please set dead value or install git && error: git config user.email & please set dead value or install git & please set dead value or install git
# @LastEditTime: 2025-01-16 17:36:05
# @FilePath: /ad9361_py/gnuradio_tx.py
#
import numpy as np
# import sys
# sys.path.append('/home/jiangrd3/ad9361_py/gnuradio-prefix/lib/python3.11/site-packages')
from gnuradio import gr
from gnuradio import blocks
import osmosdr


def hex_to_bin_array(hex_str):
    # 去掉可能的前缀 '0x' 并转换为大写（可选）
    hex_str = hex_str.strip().upper()
    # 将每个16进制字符转为4位二进制字符串并拼接
    bin_str = ''.join(format(int(char, 16), '04b') for char in hex_str)
    # 将二进制字符串转换为01的数组
    bin_array = [int(bit) for bit in bin_str]
    return bin_array

class HackRFSignalTx(gr.top_block):
    def __init__(self, signal_data, sample_rate, center_freq, gain):
        gr.top_block.__init__(self)

        # Step 1: 将 NumPy 数据包装为 GNU Radio 流
        # 使用 blocks.vector_source_c 作为数据源（复数信号）
        self.signal_source = blocks.vector_source_c(signal_data.tolist(), repeat=True)

        # Step 2: 配置 HackRF Sink
        self.hackrf_sink = osmosdr.sink(args="numchan=1 hackrf=0")
        self.hackrf_sink.set_sample_rate(sample_rate)   # 设置采样率
        self.hackrf_sink.set_center_freq(center_freq)   # 设置中心频率
        self.hackrf_sink.set_gain(gain)                 # 设置增益

        # Step 3: 连接信号源到 HackRF Sink
        self.connect(self.signal_source, self.hackrf_sink)

# 主程序
if __name__ == '__main__':
    msg = '8CFFFFFC423C52D692D953855472'
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
    pwm_signal_complex = np.array(bin_msg,np.complex64)
    pass
    
    # file = '20241225_1152.csv'
    # with open(file,'r') as f:
    #     for i in f:
    #         data = i.split(',')[4:1043]
            
    #         tmp = np.array([complex(float(c.split('+j')[0]),float(c.split('+j')[1])) for c in data])
    #         pass
    # 参数配置
    sample_rate = 10e6  # 采样率（Hz）
    center_freq = 1090e6  # 中心频率（Hz）
    gain = 10  # 发射增益

    # Step 1: 使用 NumPy 生成 PWM 信号
    # 示例：生成简单的 PWM 信号（占空比 50%，周期 10 个采样点）
    bit_duration = 10  # 每个比特持续 10 个采样点
    bit_sequence = [0, 1, 0, 1, 1, 0]  # 比特序列
    pwm_signal = []
    for bit in bit_sequence:
        pwm_signal.extend([bit] * bit_duration)

    # 转换为复数信号（HackRF 需要复数输入）
    pwm_signal = np.array(pwm_signal, dtype=np.float32) * 0.7  # 调整幅度
    # pwm_signal_complex = pwm_signal + 1j * pwm_signal  # 简单构造复数信号

    # Step 2: 初始化并运行 GNU Radio 流图
    tb = HackRFSignalTx(pwm_signal_complex, sample_rate, center_freq, gain)
    tb.start()
    input("Press Enter to stop transmission...")
    tb.stop()
    tb.wait()
