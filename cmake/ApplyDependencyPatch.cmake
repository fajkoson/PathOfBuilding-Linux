find_program(_pob_git git REQUIRED)
execute_process(COMMAND "${_pob_git}" apply --no-index --check "${POB_PATCH}"
    WORKING_DIRECTORY "${POB_SOURCE}" RESULT_VARIABLE _pob_can_apply
    OUTPUT_QUIET ERROR_QUIET)
if(_pob_can_apply EQUAL 0)
    execute_process(COMMAND "${_pob_git}" apply --no-index "${POB_PATCH}"
        WORKING_DIRECTORY "${POB_SOURCE}" COMMAND_ERROR_IS_FATAL ANY)
else()
    # FetchContent may reuse an already patched source tree across presets.
    execute_process(COMMAND "${_pob_git}" apply --no-index --reverse --check "${POB_PATCH}"
        WORKING_DIRECTORY "${POB_SOURCE}" RESULT_VARIABLE _pob_already_applied
        OUTPUT_QUIET ERROR_QUIET)
    if(NOT _pob_already_applied EQUAL 0)
        message(FATAL_ERROR "Patch no longer matches ${POB_SOURCE}; clear its fetched source cache: ${POB_PATCH}")
    endif()
endif()
