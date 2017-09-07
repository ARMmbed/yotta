# NOTE: This file is generated from {{ self }}: changes will be overwritten!

if(YOTTA_META_TOOLCHAIN_FILE_INCLUDED)
    return()
endif()
set(YOTTA_META_TOOLCHAIN_FILE_INCLUDED 1)

# this is a poor attempt to resolve build issues where CMAKE generates its own temp directories
# --> within those directories, project-relative paths will not work ... unless we commit this atrocity:
string(REPLACE "/CMakeFiles/CMakeTmp" "" CMAKE_BINDIR_NO_NESTING "${CMAKE_BINARY_DIR}")

{% for toolchain_file in toolchain_files %}
include("${CMAKE_BINDIR_NO_NESTING}/{{ toolchain_file | relative | replaceBackslashes }}")
{% endfor %}

