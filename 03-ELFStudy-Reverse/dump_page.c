#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <signal.h>
#include <string.h>
#include <errno.h>
#include <stddef.h>

static unsigned long at_entry(pid_t p) {
    char b[64];
    snprintf(b, sizeof b, "/proc/%d/auxv", p);
    FILE *f = fopen(b, "rb");
    if (!f) return 0;
    unsigned long t, v, entry = 0;
    while (fread(&t, 8, 1, f) == 1 && fread(&v, 8, 1, f) == 1) {
        if (t == 0) break;
        if (t == 9) entry = v;
    }
    fclose(f);
    return entry;
}

static unsigned long peek(pid_t p, unsigned long a) {
    errno = 0;
    long v = ptrace(PTRACE_PEEKDATA, p, (void *)a, 0);
    return errno ? 0xdeadbeefUL : (unsigned long)v;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <elf-bin> <dump-out> [input-file]\n", argv[0]);
        return 1;
    }
    pid_t p = fork();
    if (p == 0) {
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        freopen("/dev/null", "w", stdout);
        freopen("/dev/null", "w", stderr);
        if (argc >= 4) execl(argv[1], argv[1], argv[3], (char *)0);
        else execl(argv[1], argv[1], (char *)0);
        _exit(127);
    }
    int st, sig;
    waitpid(p, &st, 0);
    unsigned long entry = at_entry(p);
    unsigned long base = entry - 0x2e90;
    unsigned long bp = base + 0x3b34;  /* sub_3B30 entry, called after printing */

    ptrace(PTRACE_POKEUSER, p, (void *)offsetof(struct user, u_debugreg[0]), (void *)bp);
    ptrace(PTRACE_POKEUSER, p, (void *)offsetof(struct user, u_debugreg[7]), (void *)0x1);
    ptrace(PTRACE_CONT, p, 0, 0);
    for (;;) {
        waitpid(p, &st, 0);
        if (WIFEXITED(st) || WIFSIGNALED(st)) {
            fprintf(stderr, "process ended before breakpoint\n");
            return 2;
        }
        sig = WSTOPSIG(st);
        if (sig == SIGTRAP) break;
        ptrace(PTRACE_CONT, p, 0, (void *)sig);
    }
    /* RX 段最后一页 0x7000..0x8000 此时已由加载器解密 */
    FILE *out = fopen(argv[2], "wb");
    for (unsigned long a = base + 0x7000; a < base + 0x8000; a += 8) {
        unsigned long v = peek(p, a);
        fwrite(&v, 8, 1, out);
    }
    fclose(out);
    fprintf(stderr, "base=%#lx dumped RX page -> %s\n", base, argv[2]);
    return 0;
}
