cmake_minimum_required(VERSION 3.16)
project(call_audio_probe LANGUAGES CXX)

set(SOUNDTOUCH_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../TMessagesProj/jni/soundtouch")
add_executable(call_audio_probe
        probe.cpp
        ${SOUNDTOUCH_DIR}/TDStretch.cpp
        ${SOUNDTOUCH_DIR}/RateTransposer.cpp
        ${SOUNDTOUCH_DIR}/AAFilter.cpp
        ${SOUNDTOUCH_DIR}/FIRFilter.cpp
        ${SOUNDTOUCH_DIR}/FIFOSampleBuffer.cpp
        ${SOUNDTOUCH_DIR}/InterpolateCubic.cpp
        ${SOUNDTOUCH_DIR}/InterpolateLinear.cpp
        ${SOUNDTOUCH_DIR}/InterpolateShannon.cpp
        ${SOUNDTOUCH_DIR}/cpu_detect_x86.cpp)
target_include_directories(call_audio_probe PRIVATE ${SOUNDTOUCH_DIR})
target_compile_features(call_audio_probe PRIVATE cxx_std_17)
target_compile_definitions(call_audio_probe PRIVATE SOUNDTOUCH_DISABLE_X86_OPTIMIZATIONS)
find_package(Threads REQUIRED)
target_link_libraries(call_audio_probe PRIVATE Threads::Threads)
