# TX USING HACKRF 使用HACKRF进行发射

使用windows调用c进行开发太麻烦，还是转到ubuntu下做。

It's too convenient that develop this under Windows using C, and thus swap to ubuntu.

## Develop Environment 开发环境
`sudo apt-get install hackrf libhackrf-dev`

```
git clone https://github.com/greatscottgadgets/hackrf.git
cd hackrf/host
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```
## CMakelists

使用vscode的cmake插件进行快速启动。
Quick start using cmake plugin in vscode.

最重要的是添加库。The most important is to include lib.

`sudo apt-get install pkg-config`

```
find_package(PkgConfig REQUIRED) # find PkgConfig package
target_link_libraries(tx PRIVATE
    ${RTLSDR_LIBRARIES}  # librtlsdr的链接库
    ${HACKRF_LIBRARIES}  # libhackrf的链接库
    pthread              # 添加pthread库
    m                    # 添加数学库
)
target_include_directories(tx PRIVATE
    ${RTLSDR_INCLUDE_DIRS}
    ${HACKRF_INCLUDE_DIRS}
)
```

