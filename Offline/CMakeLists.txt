#####################################################################################################################

# Jorge Agramunt Ros    @ IFIC(Valencia,Spain)  jorge.agramunt@ific.uv.es
# Alvaro Tolosa Delgado @ IFIC(Valencia,Spain)  alvaro.tolosa@ific.uv.es
# Copyright (c) 2016 Jorge Agramunt & Alvaro Tolosa. All rights reserved.

#####################################################################################################################

# Example adapted from https://root.cern.ch/faq/can-i-integrate-root-my-cmake-build

#####################################################################################################################



# CMakeLists.txt for event package. It creates a library with dictionary and a main program
cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project(BRIKEN_offline)

   SET(CMAKE_BUILD_TYPE Release)
   include(CheckCCompilerFlag)
   include(CheckCXXCompilerFlag)

# You need to tell CMake where to find the ROOT installation. This can be done in a number of ways:
#   - ROOT built with classic configure/make use the provided $ROOTSYS/etc/cmake/FindROOT.cmake
#   - ROOT built with CMake. Add in CMAKE_PREFIX_PATH the installation prefix for ROOT
list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})

#---Locate the ROOT package and defines a number of variables (e.g. ROOT_INCLUDE_DIRS)
find_package(ROOT REQUIRED COMPONENTS MathCore RIO Hist Tree Net Graf3d Graf Gpad Thread)

#---Define useful ROOT functions and macros (e.g. ROOT_GENERATE_DICTIONARY)
include(${ROOT_USE_FILE})

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS})
add_definitions(${ROOT_CXX_FLAGS} -lTreePlayer )
ROOT_GENERATE_DICTIONARY(G__brikenDict OfflineAnalysisBRIKEN.h LINKDEF OfflineTreeLinkDef.h)
  
#---Create a shared library with geneated dictionary
add_library(brikenDict SHARED OfflineAnalysisBRIKEN.cxx G__brikenDict.cxx)
target_link_libraries(brikenDict ${ROOT_LIBRARIES}  -lTreePlayer)


set(HEADER_FILES NewSpec.cpp Komparators.cpp Signal.cpp)
add_library(otherStuff ${HEADER_FILES})

#include_directories( ${CMAKE_SOURCE_DIR}/../inc ${CMAKE_SOURCE_DIR}/../lib )


add_library(gi70 STATIC "../CommonClass/kiko_ptr.cpp" "../CommonClass/GIObject.cpp" "../../CommonClass/GIUnpackSIS3302.cpp" "../../CommonClass/GIUnpackSIS3316.cpp" "../../CommonClass/GIUnpack.cpp")



#---Create  a main program using the library
add_executable(OfflineAnalysisBRIKEN OfflineAnalysisBRIKEN.cpp)
target_link_libraries(OfflineAnalysisBRIKEN ${ROOT_LIBRARIES} brikenDict otherStuff gi70 ) 
 
# Library threads
find_package (Threads)
# C++11
set_property(TARGET OfflineAnalysisBRIKEN PROPERTY CXX_STANDARD 11)
set_property(TARGET OfflineAnalysisBRIKEN PROPERTY CXX_STANDARD_REQUIRED ON)
# PIC
set_property(TARGET OfflineAnalysisBRIKEN PROPERTY POSITION_INDEPENDENT_CODE ON)
# 64-bit
check_c_compiler_flag(-m64 M64TestFlagC)
check_cxx_compiler_flag(-m64 M64TestFlagCXX)