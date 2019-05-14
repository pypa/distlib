/*
 * Copyright (C) 2011-2018 Vinay Sajip. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef _WIN32_WINNT            // Specifies that the minimum required platform is Windows Vista.
#define _WIN32_WINNT 0x0600     // Change this to the appropriate value to target other versions of Windows.
#endif

#include <stdio.h>
#include <windows.h>
#include <Shlwapi.h>

#pragma comment (lib, "Shlwapi.lib")

#define APPENDED_ARCHIVE
#define USE_ENVIRONMENT
#define SUPPORT_RELATIVE_PATH

#define MSGSIZE 1024

#if !defined(APPENDED_ARCHIVE)

static wchar_t suffix[] = {
#if defined(_CONSOLE)
    L"-script.py"
#else
    L"-script.pyw"
#endif
};

#endif

#if defined(SUPPORT_RELATIVE_PATH)

#define RELATIVE_PREFIX L"<launcher_dir>\\"
#define RELATIVE_PREFIX_LENGTH 15

#endif

static int pid = 0;

#if !defined(_CONSOLE)

typedef int (__stdcall *MSGBOXWAPI)(IN HWND hWnd,
        IN LPCSTR lpText, IN LPCSTR lpCaption,
        IN UINT uType, IN WORD wLanguageId, IN DWORD dwMilliseconds);

#define MB_TIMEDOUT 32000

int MessageBoxTimeoutA(HWND hWnd, LPCSTR lpText,
    LPCSTR lpCaption, UINT uType, WORD wLanguageId, DWORD dwMilliseconds)
{
    static MSGBOXWAPI MsgBoxTOA = NULL;
    HMODULE hUser = LoadLibraryA("user32.dll");

    if (!MsgBoxTOA) {
        if (hUser)
            MsgBoxTOA = (MSGBOXWAPI)GetProcAddress(hUser,
                                      "MessageBoxTimeoutA");
        else {
            /*
             * stuff happened, add code to handle it here
             * (possibly just call MessageBox())
             */
        }
    }

    if (MsgBoxTOA)
        return MsgBoxTOA(hWnd, lpText, lpCaption, uType, wLanguageId,
                         dwMilliseconds);
    if (hUser)
        FreeLibrary(hUser);
    return 0;
}

#endif

static void
assert(BOOL condition, char * format, ... )
{
    if (!condition) {
        va_list va;
        char message[MSGSIZE];
        int len;

        va_start(va, format);
        len = vsnprintf_s(message, MSGSIZE, MSGSIZE - 1, format, va);
#if defined(_CONSOLE)
        fprintf(stderr, "Fatal error in launcher: %s\n", message);
#else
        MessageBoxTimeoutA(NULL, message, "Fatal Error in Launcher",
                           MB_OK | MB_SETFOREGROUND | MB_ICONERROR,
                           0, 3000);
#endif
        ExitProcess(1);
    }
}

static wchar_t script_path[MAX_PATH];

#if defined(APPENDED_ARCHIVE)

#define LARGE_BUFSIZE (65 * 1024 * 1024)

typedef struct {
    DWORD sig;
    DWORD unused_disk_nos;
    DWORD unused_numrecs;
    DWORD cdsize;
    DWORD cdoffset;
} ENDCDR;

/* We don't want to pick up this variable when scanning the executable.
 * So we initialise it statically, but fill in the first byte later.
 */
static char
end_cdr_sig [4] = { 0x00, 0x4B, 0x05, 0x06 };

static char *
find_pattern(char *buffer, size_t bufsize, char * pattern, size_t patsize)
{
    char * result = NULL;
    char * p;
    char * bp = buffer;
    size_t n;

    while ((n = bufsize - (bp - buffer) - patsize) >= 0) {
        p = (char *) memchr(bp, pattern[0], n);
        if (p == NULL)
            break;
        if (memcmp(pattern, p, patsize) == 0) {
            result = p; /* keep trying - we want the last one */
        }
        bp = p + 1;
    }
    return result;
}

static char *
find_shebang(char * buffer, size_t bufsize)
{
    FILE * fp = NULL;
    errno_t rc;
    char * result = NULL;
    char * p;
    size_t read;
    long pos;
    __int64 file_size;
    __int64 end_cdr_offset = -1;
    ENDCDR end_cdr;

    rc = _wfopen_s(&fp, script_path, L"rb");
    assert(rc == 0, "Failed to open executable");
    fseek(fp, 0, SEEK_END);
    file_size = ftell(fp);
    pos = (long) (file_size - bufsize);
    if (pos < 0)
        pos = 0;
    fseek(fp, pos, SEEK_SET);
    read = fread(buffer, sizeof(char), bufsize, fp);
    p = find_pattern(buffer, read, end_cdr_sig, sizeof(end_cdr_sig));
    if (p != NULL) {
        end_cdr = *((ENDCDR *) p);
        end_cdr_offset = pos + (p - buffer);
    }
    else {
        /*
         * Try a larger buffer. A comment can only be 64K long, so
         * go for the largest size.
         */
        char * big_buffer = malloc(LARGE_BUFSIZE);
        int n = (int) LARGE_BUFSIZE;

        pos = (long) (file_size - n);

        if (pos < 0)
            pos = 0;
        fseek(fp, pos, SEEK_SET);
        read = fread(big_buffer, sizeof(char), n, fp);
        p = find_pattern(big_buffer, read, end_cdr_sig, sizeof(end_cdr_sig));
        assert(p != NULL, "Unable to find an appended archive.");
        end_cdr = *((ENDCDR *) p);
        end_cdr_offset = pos + (p - big_buffer);
        free(big_buffer);
    }
    end_cdr_offset -= end_cdr.cdsize + end_cdr.cdoffset;
    /*
     * end_cdr_offset should now be pointing to the start of the archive.
     * However, the "start of the archive" is a little ill-defined, as
     * not all means of prepending data to a zipfile handle the central
     * directory offset the same way (simple file content appends leave
     * it alone, obviously, but the stdlib zipapp and zipfile modules
     * reflect the prepended data in the offset).
     * We consider two possibilities here:
     * 1. end_cdr_offset points to the start of the shebang (zipapp)
     * 2. end_cdr_offset points to the end of the shebang (data copy)
     * We'll assume the shebang line has no # or ! chars except at the
     * beginning, and fits into bufsize (which should be MAX_PATH).
     */

    /* Check for case 1 - we are at the start of the shebang */
    fseek(fp, end_cdr_offset, SEEK_SET);
    read = fread(buffer, sizeof(char), bufsize, fp);
    assert(read > 0, "Unable to read from file");
    if (memcmp(buffer, "#!", 2) == 0) {
        result = buffer;
    }
    else {
        /* We are not at the start, so check backward bufsize bytes */
        pos = (long) (end_cdr_offset - bufsize);
        if (pos < 0)
            pos = 0;
        fseek(fp, pos, SEEK_SET);
        read = fread(buffer, sizeof(char), bufsize, fp);
        assert(read > 0, "Unable to read from file");
        p = &buffer[read - 1];
        while (p >= buffer) {
            if (memcmp(p, "#!", 2) == 0) {
                result = p;
                break;
            }
            --p;
        }
    }
    fclose(fp);
    return result;
}

#endif

#if defined(USE_ENVIRONMENT)
/*
 * Where to place any executable found on the path. Should be OK to use a
 * static as there's only one of these per invocation of this executable.
 */
static wchar_t path_executable[MSGSIZE];

static BOOL find_on_path(wchar_t * name)
{
    wchar_t * pathext;
    size_t    varsize;
    wchar_t * context = NULL;
    wchar_t * extension;
    DWORD     len;
    errno_t   rc;
    BOOL found = FALSE;

    if (wcschr(name, L'.') != NULL) {
        /* assume it has an extension. */
        if (SearchPathW(NULL, name, NULL, MSGSIZE, path_executable, NULL))
            found = TRUE;
    }
    else {
        /* No extension - search using registered extensions. */
        rc = _wdupenv_s(&pathext, &varsize, L"PATHEXT");
        _wcslwr_s(pathext, varsize);
        if (rc == 0) {
            extension = wcstok_s(pathext, L";", &context);
            while (extension) {
                len = SearchPathW(NULL, name, extension, MSGSIZE, path_executable, NULL);
                if (len) {
                    found = TRUE;
                    break;
                }
                extension = wcstok_s(NULL, L";", &context);
            }
            free(pathext);
        }
    }
    return found;
}

/*
 * Find an executable in the environment. For now, we just look in the path,
 * but potentially we could expand this to look in the registry, etc.
 */
static wchar_t *
find_environment_executable(wchar_t * line) {
    BOOL found = find_on_path(line);

    return found ? path_executable : NULL;
}

#endif

static wchar_t *
skip_ws(wchar_t *p)
{
    while (*p && iswspace(*p))
        ++p;
    return p;
}

static wchar_t *
skip_me(wchar_t * p)
{
    wchar_t * result;
    wchar_t terminator;

    if (*p != L'\"')
        terminator = L' ';
    else {
        terminator = *p++;
        ++p;
    }
    result = wcschr(p, terminator);
    if (result == NULL) /* perhaps nothing more on the command line */
        result = L"";
    else
        result = skip_ws(++result);
    return result;
}

static char *
find_terminator(char *buffer, size_t size)
{
    char c;
    char * result = NULL;
    char * end = buffer + size;
    char * p;

    for (p = buffer; p < end; p++) {
        c = *p;
        if (c == '\r') {
            result = p;
            break;
        }
        if (c == '\n') {
            result = p;
            break;
        }
    }
    return result;
}

static BOOL
safe_duplicate_handle(HANDLE in, HANDLE * pout)
{
    BOOL ok;
    HANDLE process = GetCurrentProcess();
    DWORD rc;

    *pout = NULL;
    ok = DuplicateHandle(process, in, process, pout, 0, TRUE,
                         DUPLICATE_SAME_ACCESS);
    if (!ok) {
        rc = GetLastError();
        if (rc == ERROR_INVALID_HANDLE)
            ok = TRUE;
    }
    return ok;
}

static BOOL
control_key_handler(DWORD type)
{
    if ((type == CTRL_C_EVENT) && pid)
        GenerateConsoleCtrlEvent(pid, 0);
    return TRUE;
}

static void
run_child(wchar_t * cmdline)
{
    HANDLE job;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION info;
    DWORD rc;
    BOOL ok;
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;

    job = CreateJobObject(NULL, NULL);
    ok = QueryInformationJobObject(job, JobObjectExtendedLimitInformation,
                                  &info, sizeof(info), &rc);
    assert(ok && (rc == sizeof(info)), "Job information querying failed");
    info.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
                                             JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK;
    ok = SetInformationJobObject(job, JobObjectExtendedLimitInformation, &info,
                                 sizeof(info));
    assert(ok, "Job information setting failed");
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    ok = safe_duplicate_handle(GetStdHandle(STD_INPUT_HANDLE), &si.hStdInput);
    assert(ok, "stdin duplication failed");
    ok = safe_duplicate_handle(GetStdHandle(STD_OUTPUT_HANDLE), &si.hStdOutput);
    assert(ok, "stdout duplication failed");
    ok = safe_duplicate_handle(GetStdHandle(STD_ERROR_HANDLE), &si.hStdError);
    assert(ok, "stderr duplication failed");
    si.dwFlags = STARTF_USESTDHANDLES;
    SetConsoleCtrlHandler((PHANDLER_ROUTINE) control_key_handler, TRUE);
    ok = CreateProcessW(NULL, cmdline, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi);
    assert(ok, "Unable to create process using '%ls'", cmdline);
    pid = pi.dwProcessId;
    AssignProcessToJobObject(job, pi.hProcess);
    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess, INFINITE);
    ok = GetExitCodeProcess(pi.hProcess, &rc);
    assert(ok, "Failed to get exit code of process");
    ExitProcess(rc);
}

static wchar_t *
find_exe_extension(wchar_t * line) {
    wchar_t * p;

    while ((p = StrStrIW(line, L".exe")) != NULL) {
        wchar_t c = p[4];

        if ((c == L'\0') || (c == L'"') || iswspace(c))
            break;
        line = &p[4];
    }
    return p;
}

static wchar_t *
find_executable_and_args(wchar_t * line, wchar_t ** argp)
{
    wchar_t * p = find_exe_extension(line);
#if defined(USE_ENVIRONMENT)
    wchar_t * q;
    int n;
#endif
    wchar_t * result;

#if !defined(USE_ENVIRONMENT)
    assert(p != NULL, "Expected to find a command ending in '.exe' in shebang line: %ls", line);
    p += 4; /* skip past the '.exe' */
    result = line;
#else
    if (p != NULL) {
        p += 4; /* skip past the '.exe' */
        result = line;
    }
    else {
        n = _wcsnicmp(line, L"/usr/bin/env", 12);
        assert(n == 0, "Expected to find a command ending in '.exe' in shebang line: %ls", line);
        p = line + 12; /* past the '/usr/bin/env' */
        assert(*p && iswspace(*p), "Expected to find whitespace after '/usr/bin/env': %ls", line);
        do {
            ++p;
        } while (*p && iswspace(*p));
        /* Now, p points to what comes after /usr/bin/env and any following whitespace. */
        q = p;
        /* Skip past executable name and NUL-terminate it. */
        while (*q && !iswspace(*q))
            ++q;
        if (iswspace(*q))
            *q++ = L'\0';
        result = find_environment_executable(p);
        assert(result != NULL, "Unable to find executable in environment: %ls", line);
        p = q; /* point past name of executable in shebang */
    }
#endif
    if (*line == L'"') {
        assert(*p == L'"', "Expected terminating double-quote for executable in shebang line: %ls", line);
        *p++ = L'\0';
        ++line;
        ++result;  /* See https://bitbucket.org/pypa/distlib/issues/104 */
    }
    /* p points just past the executable. It must either be a NUL or whitespace. */
#if !defined(SUPPORT_RELATIVE_PATH)
    assert(*p != L'"', "Terminating quote without starting quote for executable in shebang line: %ls", line);
#else
    if (_wcsnicmp(line, RELATIVE_PREFIX, RELATIVE_PREFIX_LENGTH) && (line[RELATIVE_PREFIX_LENGTH] != L'\"')) {
        assert(*p != L'"', "Terminating quote without starting quote for executable in shebang line: %ls", line);
    }
#endif
    /* if p is whitespace, make it NUL to truncate 'line', and advance */
    if (*p && iswspace(*p))
        *p++ = L'\0';
    /* Now we can skip the whitespace, having checked that it's there. */
    while(*p && iswspace(*p))
        ++p;
    *argp = p;
    return result;
}

static int
process(int argc, char * argv[])
{
    wchar_t * cmdline = skip_me(GetCommandLineW());
    wchar_t * psp;
    size_t len = GetModuleFileNameW(NULL, script_path, MAX_PATH);
    FILE *fp = NULL;
    char buffer[MAX_PATH];
    wchar_t wbuffer[MAX_PATH];
#if defined(SUPPORT_RELATIVE_PATH)
    wchar_t dbuffer[MAX_PATH];
    wchar_t pbuffer[MAX_PATH];
    wchar_t * qp;
    int prefix_offset;
#endif
    char *cp;
    wchar_t * wcp;
    wchar_t * cmdp;
    char * p;
    wchar_t * wp;
    int n;
#if !defined(APPENDED_ARCHIVE)
    errno_t rc;
#endif

    if (script_path[0] != L'\"')
        psp = script_path;
    else {
        psp = &script_path[1];
        len -= 2;
    }
    psp[len] = L'\0';

#if !defined(APPENDED_ARCHIVE)
    /* Replace the .exe with -script.py(w) */
    wp = wcsstr(psp, L".exe");
    assert(wp != NULL, "Failed to find \".exe\" in executable name");

    len = MAX_PATH - (wp - script_path);
    assert(len > sizeof(suffix), "Failed to append \"%ls\" suffix", suffix);
    wcsncpy_s(wp, len, suffix, sizeof(suffix));
#endif
#if defined(APPENDED_ARCHIVE)
    /* Initialise signature dynamically so that it doesn't appear in
     * a stock executable.
     */
    end_cdr_sig[0] = 0x50;

    p = find_shebang(buffer, MAX_PATH);
    assert(p != NULL, "Failed to find shebang");
#else
    rc = _wfopen_s(&fp, psp, L"rb");
    assert(rc == 0, "Failed to open script file '%ls'", psp);
    fread(buffer, sizeof(char), MAX_PATH, fp);
    fclose(fp);
    p = buffer;
#endif
    cp = find_terminator(p, MAX_PATH);
    assert(cp != NULL, "Expected to find terminator in shebang line");
    *cp = '\0';
    // Decode as UTF-8
    n = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, p, (int) (cp - p), wbuffer, MAX_PATH);
    assert(n != 0, "Expected to decode shebang line using UTF-8");
    wbuffer[n] = L'\0';
    wcp = wbuffer;
    while (*wcp && iswspace(*wcp))
        ++wcp;
    assert(*wcp == L'#', "Expected to find \'#\' at start of shebang line");
    ++wcp;
    while (*wcp && iswspace(*wcp))
        ++wcp;
    assert(*wcp == L'!', "Expected to find \'!\' following \'#\' in shebang line");
    ++wcp;
    while (*wcp && iswspace(*wcp))
        ++wcp;
    wp = NULL;
    wcp = find_executable_and_args(wcp, &wp);
    assert(wcp != NULL, "Expected to find executable in shebang line");
    assert(wp != NULL, "Expected to find arguments (even if empty) in shebang line");
#if defined(SUPPORT_RELATIVE_PATH)
    /*
       If the executable starts with the relative prefix, resolve the following path
       relative to the launcher's directory.
     */
    prefix_offset = RELATIVE_PREFIX_LENGTH;
    if (!_wcsnicmp(RELATIVE_PREFIX, wcp, prefix_offset)) {
        wcscpy_s(dbuffer, MAX_PATH, script_path);
        PathRemoveFileSpecW(dbuffer);
        if (wcp[prefix_offset] == L'\"') {
            prefix_offset++;
            qp = wcschr(&wcp[prefix_offset], L'\"');
            assert(qp != NULL, "Expected terminating double-quote for executable in shebang line: %ls", wcp);
            *qp = L'\0';
        }
        // The following call appears to canonicalize the path, so no need to
        // worry about doing that
        PathCombineW(pbuffer, dbuffer, &wcp[prefix_offset]);
        wcp = pbuffer;
    }
#endif
     /* 3 spaces + 4 quotes + NUL */
    len = wcslen(wcp) + wcslen(wp) + 8 + wcslen(psp) + wcslen(cmdline);
    cmdp = (wchar_t *) calloc(len, sizeof(wchar_t));
    assert(cmdp != NULL, "Expected to be able to allocate command line memory");
    _snwprintf_s(cmdp, len, len, L"\"%ls\" %ls \"%ls\" %ls", wcp, wp, psp, cmdline);
    run_child(cmdp);  /* never actually returns */
    free(cmdp);
    return 0;
}

#if defined(_CONSOLE)

int main(int argc, char* argv[])
{
    return process(argc, argv);
}

#else

int APIENTRY WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
                     LPSTR lpCmdLine, int nCmdShow)
{
    return process(__argc, __argv);
}

#endif
