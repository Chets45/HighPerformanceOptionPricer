cmake_minimum_required(VERSION 3.15)
project(OptionsPricingCalculator LANGUAGES CXX)

find_package(Python3 3.7 COMPONENTS Interpreter Development REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.13.1
)
FetchContent_MakeAvailable(pybind11)

add_library(option_lib
        src/Option.cpp
        src/MathUtil.cpp
)

target_include_directories(option_lib PUBLIC ${pybind11_INCLUDE_DIRS})

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/python)

pybind11_add_module(option_pricer_cpp
        src/bindings.cpp
)

target_link_libraries(option_pricer_cpp PRIVATE option_lib)
