/* SPDX-License-Identifier: MIT */
/*
 * C-compatible admission ABI over the native ESS/co-save reader and the
 * Windows co-save read lease. Consumable from C11 or C++11; implemented in
 * C++20 (SaveAdmissionAbi.cpp) and linked STATICALLY into the SKSE fork.
 * This header must never include SaveAdmission.h or WindowsReadLease.h.
 *
 * Memory contract (ordinary C rules, not a sandbox): every pointer must be
 * readable for the size the caller declares beside it, for the duration of
 * the call. The bridge bounds every read by those declared sizes and by the
 * fixed scan caps documented below; it refuses null pointers, zero sizes,
 * oversized counts, and names/paths with no NUL inside the declared capacity.
 * It cannot detect dangling pointers or capacities that overstate the real
 * allocation; that is the caller's ordinary responsibility.
 *
 * Threading: all functions are reentrant. One lease may be used from one
 * thread at a time and must be released exactly once (double release is a
 * caller bug, exactly like free()). Nothing here writes the filesystem,
 * loads a DLL, or lets a C++ exception cross the boundary.
 */
#ifndef ENSRICK_SAVE_ADMISSION_ABI_H
#define ENSRICK_SAVE_ADMISSION_ABI_H
#include <stdint.h>

#ifdef __cplusplus
#define ENSRICK_ADMISSION_NOEXCEPT noexcept
extern "C" {
#else
#define ENSRICK_ADMISSION_NOEXCEPT
#endif

#define ENSRICK_ADMISSION_ABI_VERSION 1u
#define ENSRICK_ADMISSION_REASON_BYTES 256

typedef enum ensrick_admission_status {
    ENSRICK_ADMISSION_OK = 0,                      /* begin: admitted, lease returned            */
    ENSRICK_ADMISSION_INVALID_ARGUMENT = 1,        /* request/result contract violated; no parse */
    ENSRICK_ADMISSION_FINGERPRINT_UNAVAILABLE = 2, /* expected_fingerprint == 0: denied          */
    ENSRICK_ADMISSION_MALFORMED_SAVE = 3,          /* ESS snapshot refused by the reader         */
    ENSRICK_ADMISSION_ACTIVE_PLUGINS_INVALID = 4,  /* active table fails name/count policy       */
    ENSRICK_ADMISSION_PLUGIN_MISMATCH = 5,         /* saved plugin missing or type changed       */
    ENSRICK_ADMISSION_LEASE_FAILED = 6,            /* co-save open/lock/read failed; see win32   */
    ENSRICK_ADMISSION_COSAVE_REFUSED = 7,          /* co-save malformed, checkpoint bad/mismatch */
    ENSRICK_ADMISSION_OUT_OF_MEMORY = 8,
    ENSRICK_ADMISSION_INTERNAL_ERROR = 9
} ensrick_admission_status;

/* One active plugin file name. `utf8` need not be NUL-terminated at a known
 * offset; the bridge scans for the first NUL within min(capacity_bytes, 256)
 * bytes and refuses the name if none is found (a valid name is <= 255 bytes,
 * so nothing past byte 256 is ever read). For a `char name[N]` field pass
 * capacity_bytes = N. */
typedef struct ensrick_admission_plugin_name {
    const char* utf8;
    uint32_t capacity_bytes;
    uint32_t reserved; /* must be zero */
} ensrick_admission_plugin_name;

typedef struct ensrick_admission_request {
    uint32_t struct_size; /* sizeof(ensrick_admission_request) */
    uint32_t abi_version; /* ENSRICK_ADMISSION_ABI_VERSION */
    /* Private, stable snapshot of the whole .ess file. Must not exceed
     * ensrick_admission_maximum_bytes(). Not retained after the call. */
    const uint8_t* ess_bytes;
    uint64_t ess_size;
    /* Active tables from the running engine. Extra active plugins are fine;
     * missing saved plugins or full/light changes are refused. */
    const ensrick_admission_plugin_name* full_plugins;
    const ensrick_admission_plugin_name* light_plugins;
    uint32_t full_count;
    uint32_t light_count;
    /* Live currency ledger fingerprint. Zero means "unknown" and is denied. */
    uint64_t expected_fingerprint;
    /* Absolute UTF-16 path of the .skse co-save. Scanned for a NUL within
     * min(cosave_path_capacity_units, 32768) code units; refused otherwise.
     * The path is used only to open the file and never copied into reason. */
    const uint16_t* cosave_path_utf16;
    uint32_t cosave_path_capacity_units;
    uint32_t reserved; /* must be zero */
} ensrick_admission_request;

typedef struct ensrick_admission_result {
    uint32_t struct_size; /* caller sets sizeof(ensrick_admission_result) before the call */
    uint32_t status;      /* ensrick_admission_status */
    uint32_t win32_error; /* GetLastError() behind LEASE_FAILED when known, else 0 */
    uint32_t problem_count; /* plugin problems found (PLUGIN_MISMATCH); reason lists as many as fit */
    /* ESS header facts, valid once status is past MALFORMED_SAVE. */
    uint32_t save_number;
    uint32_t player_level;
    uint32_t saved_full_count;
    uint32_t saved_light_count;
    uint16_t compression;
    uint8_t form_version;
    uint8_t reserved8;
    uint32_t reserved32;
    /* Currency checkpoint, valid only when status == OK. */
    uint64_t checkpoint_fingerprint;
    uint64_t checkpoint_value;
    uint64_t checkpoint_backend;
    uint64_t checkpoint_physical;
    /* NUL-terminated UTF-8 (never split mid-sequence). Popup-safe: composed
     * only from fixed phrases, core reader messages, Win32 codes, and
     * policy-validated plugin file names. Never contains any filesystem path. */
    char reason[ENSRICK_ADMISSION_REASON_BYTES];
} ensrick_admission_result;

/* Opaque. Holds the Windows read-sharing lease on the co-save plus its
 * byte snapshot. Writers/deleters are blocked while it is alive. */
typedef struct ensrick_admission_lease ensrick_admission_lease;

uint32_t ensrick_admission_abi_version(void) ENSRICK_ADMISSION_NOEXCEPT;
uint64_t ensrick_admission_maximum_bytes(void) ENSRICK_ADMISSION_NOEXCEPT;
/* Static string for logging; "unknown" for values outside the enum. */
const char* ensrick_admission_status_name(uint32_t status) ENSRICK_ADMISSION_NOEXCEPT;

/* Validates the ESS snapshot, the active plugin tables, the co-save lease
 * and the currency checkpoint with the existing native policies. On OK,
 * *lease receives an owned lease that the caller must release. On any other
 * status *lease is NULL and nothing stays open. Returns the same value it
 * stores in result->status. If `result` is NULL or its struct_size does not
 * match, INVALID_ARGUMENT is returned and `result` is left untouched. */
uint32_t ensrick_admission_begin(const ensrick_admission_request* request,
    ensrick_admission_result* result, ensrick_admission_lease** lease) ENSRICK_ADMISSION_NOEXCEPT;

/* NULL-safe. Closes the lease handle; the co-save becomes writable again. */
void ensrick_admission_release(ensrick_admission_lease* lease) ENSRICK_ADMISSION_NOEXCEPT;

/* 1 if `borrowed_handle` (a Win32 HANDLE the engine actually reads with)
 * refers to the same file object identity as the held lease, else 0. NULL
 * or INVALID_HANDLE_VALUE, or a NULL lease, yields 0. Handle is borrowed. */
uint32_t ensrick_admission_lease_matches_handle(const ensrick_admission_lease* lease,
    void* borrowed_handle) ENSRICK_ADMISSION_NOEXCEPT;

/* Read-only view of the leased co-save bytes, valid until release. */
uint32_t ensrick_admission_lease_cosave(const ensrick_admission_lease* lease,
    const uint8_t** data, uint64_t* size) ENSRICK_ADMISSION_NOEXCEPT;

#ifdef __cplusplus
}
#endif
#endif
