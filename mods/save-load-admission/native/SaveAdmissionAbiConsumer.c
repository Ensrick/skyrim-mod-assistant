/* SPDX-License-Identifier: MIT */
/* Compiled as C, not C++, so the build itself proves SaveAdmissionAbi.h
   needs no C++ at all; a C++11 consumer follows a fortiori. */
#include "SaveAdmissionAbi.h"
#include <stddef.h>
#include <string.h>

typedef char ensrick_abi_result_layout_check[sizeof(ensrick_admission_result) == 328 ? 1 : -1];
#if defined(_WIN64)
typedef char ensrick_abi_name_layout_check[sizeof(ensrick_admission_plugin_name) == 16 ? 1 : -1];
typedef char ensrick_abi_request_layout_check[sizeof(ensrick_admission_request) == 72 ? 1 : -1];
#endif

uint32_t ensrick_abi_c_consumer_probe(uint32_t* version, uint64_t* maximum, const char** ok_name)
{
    ensrick_admission_result result;
    ensrick_admission_lease* lease = (ensrick_admission_lease*)1; /* must be reset to NULL */
    uint32_t status;
    memset(&result, 0, sizeof result);
    result.struct_size = (uint32_t)sizeof result;
    *version = ensrick_admission_abi_version();
    *maximum = ensrick_admission_maximum_bytes();
    *ok_name = ensrick_admission_status_name(ENSRICK_ADMISSION_OK);
    status = ensrick_admission_begin(NULL, &result, &lease);
    if (lease != NULL || result.status != status) return 0xFFFFFFFFu;
    ensrick_admission_release(NULL);
    return status;
}
