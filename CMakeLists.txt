cmake_minimum_required(VERSION 3.5.0)
project(tx VERSION 0.1.0 LANGUAGES CXX)
# 查找pkg-config
find_package(PkgConfig REQUIRED)
# 查找librtlsdr和libhackrf库
pkg_check_modules(RTLSDR REQUIRED librtlsdr)
pkg_check_modules(HACKRF REQUIRED libhackrf)



add_executable(tx main.cpp)

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
include(CTest)
enable_testing()

