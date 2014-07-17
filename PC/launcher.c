/*
 * Copyright (C) 2011-2014 Vinay Sajip. All rights reserved.
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

#define MSGSIZE 1024

#if !defined(APPENDED_ARCHIVE)

static char suffix[] = {
#if defined(_CONSOLE)
    "-script.py"
#else
    "-script.pyw"
#endif
};

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

static char script_path[MAX_PATH];

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
    long n;

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
    long file_size;
    long end_cdr_offset = -1;
    ENDCDR end_cdr;

    rc = fopen_s(&fp, script_path, "rb");
    assert(rc == 0, "Failed to open executable");
    fseek(fp, 0, SEEK_END);
    file_size = ftell(fp);
    pos = file_size - bufsize;
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

        pos = file_size - n;

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
     * end_cdr_offset should now be pointing to the start of the archive,
     * i.e. just after the shebang. We'll assume the shebang line has no
     * # or ! chars except at the beginning, and fits into bufsize (which
     * should be MAX_PATH).
     */
    pos = end_cdr_offset - bufsize;
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
    fclose(fp);
    return result;
}

#endif

#if 0
static COMMAND * find_on_path(wchar_t * name)
{
    wchar_t * pathext;
    size_t    varsize;
    wchar_t * context = NULL;
    wchar_t * extension;
    COMMAND * result = NULL;
    DWORD     len;
    errno_t   rc;

    wcscpy_s(path_command.key, MAX_PATH, name);
    if (wcschr(name, L'.') != NULL) {
        /* assume it has an extension. */
        len = SearchPathW(NULL, name, NULL, MSGSIZE, path_command.value, NULL);
        if (len) {
            result = &path_command;
        }
    }
    else {
        /* No extension - search using registered extensions. */
        rc = _wdupenv_s(&pathext, &varsize, L"PATHEXT");
        if (rc == 0) {
            extension = wcstok_s(pathext, L";", &context);
            while (extension) {
                len = SearchPathW(NULL, name, extension, MSGSIZE, path_command.value, NULL);
                if (len) {
                    result = &path_command;
                    break;
                }
                extension = wcstok_s(NULL, L";", &context);
            }
            free(pathext);
        }
    }
    return result;
}

#endif

static char *
skip_ws(char *p)
{
    while (*p && isspace(*p))
        ++p;
    return p;
}

static char *
skip_me(char * p)
{
    char * result;
    char terminator;

    if (*p != '\"')
        terminator = ' ';
    else {
        terminator = *p++;
        ++p;
    }
    result = strchr(p, terminator);
    if (result == NULL) /* perhaps nothing more on the command line */
        result = "";
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
run_child(char * cmdline)
{
    HANDLE job;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION info;
    DWORD rc;
    BOOL ok;
    STARTUPINFO si;
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
    ok = CreateProcess(NULL, cmdline, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi);
    assert(ok, "Unable to create process using '%s'", cmdline);
    pid = pi.dwProcessId;
    AssignProcessToJobObject(job, pi.hProcess);
    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess, INFINITE);
    ok = GetExitCodeProcess(pi.hProcess, &rc);
    assert(ok, "Failed to get exit code of process");
    ExitProcess(rc);
}

static char *
find_exe(char * line) {
    char * p;

    while ((p = StrStrIA(line, ".exe")) != NULL) {
        char c = p[4];

        if ((c == '\0') || (c == '"') || isspace(c))
            break;
        line = &p[4];
    }
    return p;
}

static char *
find_executable_and_args(char * line, char ** argp)
{
    char * p = find_exe(line);

    assert(p != NULL, "Expected to find a command ending in '.exe' in shebang line.");
    p += 4;
    if (*line == '"') {
        assert(*p == '"', "Expected terminating double-quote for executable in shebang line.");
        *p++ = '\0';
        ++line;
    }
    /* p points just past the executable. It must either be a NUL or whitespace. */
    assert(*p != '"', "Terminating quote without starting quote for executable in shebang line.");
    /* Now we can skip the whitespace, having checked that it's there. */
    while(*p && isspace(*p))
        *p++ = '\0';    /* Ensure parameters are not included in executable */
    *argp = p;
    return line;
}

static int
process(int argc, char * argv[])
{
    char * cmdline = skip_me(GetCommandLine());
    char * psp;
    size_t len = GetModuleFileName(NULL, script_path, MAX_PATH);
    FILE *fp = NULL;
    char buffer[MAX_PATH];
    char *cp;
    char * cmdp;
    char * p;
#if !defined(APPENDED_ARCHIVE)
    errno_t rc;
#endif

    if (script_path[0] != '\"')
        psp = script_path;
    else {
        psp = &script_path[1];
        len -= 2;
    }
    psp[len] = '\0';

#if !defined(APPENDED_ARCHIVE)
    /* Replace the .exe with -script.py(w) */
    p = strstr(psp, ".exe");
    assert(p != NULL, "Failed to find \".exe\" in executable name");

    len = MAX_PATH - (p - script_path);
    assert(len > sizeof(suffix), "Failed to append \"%s\" suffix", suffix);
    strncpy_s(p, len, suffix, sizeof(suffix));
#endif
#if defined(APPENDED_ARCHIVE)
    /* Initialise signature dynamically so that it doesn't appear in
     * a stock executable.
     */
    end_cdr_sig[0] = 0x50;

    p = find_shebang(buffer, MAX_PATH);
    assert(p != NULL, "Failed to find shebang");
#else
    rc = fopen_s(&fp, psp, "rb");
    assert(rc == 0, "Failed to open script file \"%s\"", psp);
    fread(buffer, sizeof(char), MAX_PATH, fp);
    fclose(fp);
    p = buffer;
#endif
    cp = find_terminator(p, MAX_PATH);
    assert(cp != NULL, "Expected to find terminator in shebang line");
    *cp = '\0';
    cp = p;
    while (*cp && isspace(*cp))
        ++cp;
    assert(*cp == '#', "Expected to find \'#\' at start of shebang line");
    ++cp;
    while (*cp && isspace(*cp))
        ++cp;
    assert(*cp == '!', "Expected to find \'!\' following \'#\' in shebang line");
    ++cp;
    while (*cp && isspace(*cp))
        ++cp;
    p = NULL;
    cp = find_executable_and_args(cp, &p);
    assert(cp != NULL, "Expected to find executable in shebang line");
    assert(p != NULL, "Expected to find arguments (even if empty) in shebang line");
     /* 3 spaces + 4 quotes + NUL */
    len = strlen(cp) + strlen(p) + 8 + strlen(psp) + strlen(cmdline);
    cmdp = calloc(len, sizeof(char));
    assert(cmdp != NULL, "Expected to be able to allocate command line memory");
    _snprintf_s(cmdp, len, len, "\"%s\" %s \"%s\" %s", cp, p, psp, cmdline);
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
