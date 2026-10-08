/*
 * autoxhook.c - autoxkit 低级键盘/鼠标钩子 DLL 实现
 *
 * 纯 Win32 C 实现，不依赖 Python 运行时。
 * 构建见 build_dll.ps1：
 *   gcc -O2 -Wall -shared -s -static-libgcc -o _autoxhook.dll autoxhook.c -luser32 -lkernel32
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "autoxhook.h"

#define AXH_VERSION "autoxhook 1.0"
#define AXH_MAX_LISTENERS 8

/* 槽位状态：0=空闲, 1=运行中, 2=停止中 */
#define AXH_SLOT_FREE 0
#define AXH_SLOT_RUNNING 1
#define AXH_SLOT_STOPPING 2

typedef struct {
    volatile LONG slot_state;
    int want_kbd;
    int want_mouse;
    HHOOK kbd_hook;
    HHOOK mouse_hook;
    HANDLE thread;
    HANDLE init_event;
    DWORD tid;
    /* 32 位对齐 LONG，Interlocked 写 / volatile 读，x86/x64 天然原子 */
    volatile LONG key_mask;
    volatile LONG mouse_mask;
    axh_key_cb kcb;
    axh_mouse_cb mcb;
} axh_listener;

static axh_listener g_listeners[AXH_MAX_LISTENERS];
static HINSTANCE g_hinst = NULL;
static DWORD g_tls_index = TLS_OUT_OF_INDEXES;

/* 修饰键/锁键状态跟踪（对齐 pyWinhook 的 key_state 能力） */
static unsigned char g_key_state[256];

/* ---------- 内部工具 ---------- */

/* 泵线程私有的当前监听器。LL 钩子回调总是在安装它的线程上被调用，
 * 故 TLS 可 O(1) 定位回调所属实例（回调签名本身不含钩子句柄）。 */
static axh_listener* current_listener(void) {
    return (axh_listener*)TlsGetValue(g_tls_index);
}

static unsigned int mouse_bit(unsigned int msg) {
    switch (msg) {
        case WM_LBUTTONDOWN: return AXH_M_LDOWN;
        case WM_LBUTTONUP:   return AXH_M_LUP;
        case WM_RBUTTONDOWN: return AXH_M_RDOWN;
        case WM_RBUTTONUP:   return AXH_M_RUP;
        case WM_MBUTTONDOWN: return AXH_M_MDOWN;
        case WM_MBUTTONUP:   return AXH_M_MUP;
        case WM_MOUSEWHEEL:  return AXH_M_WHEEL;
        case WM_XBUTTONDOWN: return AXH_M_XDOWN;
        case WM_XBUTTONUP:   return AXH_M_XUP;
        case WM_MOUSEMOVE:   return AXH_M_MOVE;
        default:             return 0;
    }
}

static void set_modifier(unsigned int vkey, int down) {
    g_key_state[vkey] = down ? 0x80 : 0x00;
    switch (vkey) {
        case VK_LMENU: case VK_RMENU:
            g_key_state[VK_MENU] =
                g_key_state[VK_LMENU] | g_key_state[VK_RMENU];
            break;
        case VK_LSHIFT: case VK_RSHIFT:
            g_key_state[VK_SHIFT] =
                g_key_state[VK_LSHIFT] | g_key_state[VK_RSHIFT];
            break;
        case VK_LCONTROL: case VK_RCONTROL:
            g_key_state[VK_CONTROL] =
                g_key_state[VK_LCONTROL] | g_key_state[VK_RCONTROL];
            break;
        default:
            break;
    }
}

/* 仅在事件放行时调用（被拦截的按键不算"按过"，与 pyWinhook 语义一致） */
static void update_key_state(unsigned int vkey, int msg) {
    int down = (msg == WM_KEYDOWN || msg == WM_SYSKEYDOWN);
    int up = (msg == WM_KEYUP || msg == WM_SYSKEYUP);
    if (!down && !up)
        return;
    switch (vkey) {
        case VK_MENU: case VK_LMENU: case VK_RMENU:
            set_modifier(vkey, down);
            g_key_state[VK_MENU] =
                g_key_state[VK_LMENU] | g_key_state[VK_RMENU];
            break;
        case VK_SHIFT: case VK_LSHIFT: case VK_RSHIFT:
            set_modifier(vkey, down);
            g_key_state[VK_SHIFT] =
                g_key_state[VK_LSHIFT] | g_key_state[VK_RSHIFT];
            break;
        case VK_CONTROL: case VK_LCONTROL: case VK_RCONTROL:
            set_modifier(vkey, down);
            g_key_state[VK_CONTROL] =
                g_key_state[VK_LCONTROL] | g_key_state[VK_RCONTROL];
            break;
        case VK_NUMLOCK:
            if (up) g_key_state[VK_NUMLOCK] = !g_key_state[VK_NUMLOCK];
            break;
        case VK_CAPITAL:
            if (up) g_key_state[VK_CAPITAL] = !g_key_state[VK_CAPITAL];
            break;
        case VK_SCROLL:
            if (up) g_key_state[VK_SCROLL] = !g_key_state[VK_SCROLL];
            break;
        default:
            break;
    }
}

static void init_lock_keys(void) {
    g_key_state[VK_NUMLOCK] = (GetKeyState(VK_NUMLOCK) & 0x0001) ? 0x01 : 0x00;
    g_key_state[VK_CAPITAL] = (GetKeyState(VK_CAPITAL) & 0x0001) ? 0x01 : 0x00;
    g_key_state[VK_SCROLL]  = (GetKeyState(VK_SCROLL)  & 0x0001) ? 0x01 : 0x00;
}

/* ---------- 低级钩子回调（热路径） ---------- */

static LRESULT CALLBACK ll_key_proc(int code, WPARAM wParam, LPARAM lParam) {
    axh_listener* L = current_listener();
    if (code >= 0 && L != NULL) {
        int down = (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN);
        unsigned int bit = down ? (unsigned int)AXH_KEY_DOWN
                                : (unsigned int)AXH_KEY_UP;
        PKBDLLHOOKSTRUCT k = (PKBDLLHOOKSTRUCT)lParam;
        int blocked = 0;

        /* 订阅掩码短路：无人订阅的类型完全不进入 Python/GIL */
        if ((unsigned int)L->key_mask & bit) {
            axh_key_cb cb = L->kcb;
            if (cb && cb((int)wParam, (int)k->vkCode, (int)k->scanCode,
                         (int)k->flags, (unsigned int)k->time) == 1) {
                blocked = 1;
            }
        }
        if (blocked)
            return 1; /* 拦截：不更新按键状态，不向系统传播 */
        update_key_state((unsigned int)k->vkCode, (int)wParam);
    }
    /* CallNextHookEx 首参数已被系统忽略，传 NULL 即可 */
    return CallNextHookEx(NULL, code, wParam, lParam);
}

static LRESULT CALLBACK ll_mouse_proc(int code, WPARAM wParam, LPARAM lParam) {
    axh_listener* L = current_listener();
    if (code >= 0 && L != NULL) {
        unsigned int bit = mouse_bit((unsigned int)wParam);
        if (bit && ((unsigned int)L->mouse_mask & bit)) {
            PMSLLHOOKSTRUCT ms = (PMSLLHOOKSTRUCT)lParam;
            int data = 0;
            axh_mouse_cb cb = L->mcb;
            if (wParam == WM_MOUSEWHEEL) {
                /* 高 16 位为滚动量，转有符号 short */
                data = (int)(short)(ms->mouseData >> 16);
            } else if (wParam == WM_XBUTTONDOWN || wParam == WM_XBUTTONUP) {
                data = (int)((ms->mouseData >> 16) & 0xFFFF); /* 1 或 2 */
            }
            if (cb && cb((int)wParam, (int)ms->pt.x, (int)ms->pt.y, data,
                         (int)ms->flags, (unsigned int)ms->time) == 1) {
                return 1; /* 拦截 */
            }
        }
    }
    return CallNextHookEx(NULL, code, wParam, lParam);
}

/* ---------- 消息泵线程 ---------- */

static DWORD WINAPI pump_proc(LPVOID param) {
    axh_listener* L = (axh_listener*)param;
    TlsSetValue(g_tls_index, L);

    /* 强制创建消息队列，避免 stop 侧 PostThreadMessageW 过早失败 */
    {
        MSG dummy;
        PeekMessageW(&dummy, NULL, WM_USER, WM_USER, PM_NOREMOVE);
    }

    init_lock_keys();

    if (L->want_kbd) {
        L->kbd_hook = SetWindowsHookExW(WH_KEYBOARD_LL, ll_key_proc,
                                        g_hinst, 0);
    }
    if (L->want_mouse) {
        L->mouse_hook = SetWindowsHookExW(WH_MOUSE_LL, ll_mouse_proc,
                                          g_hinst, 0);
    }

    /* 安装结果直接体现在 L->kbd_hook / L->mouse_hook（NULL=失败）；
     * SetEvent 为 start 侧随后的读取提供同步屏障 */
    SetEvent(L->init_event);

    if ((L->want_kbd && !L->kbd_hook) || (L->want_mouse && !L->mouse_hook)) {
        /* 任一请求的钩子安装失败：卸载已装上的钩子并退出线程，
         * 具体错误码由 axh_start 依据 hook 字段判定 */
        if (L->kbd_hook) {
            UnhookWindowsHookEx(L->kbd_hook);
            L->kbd_hook = NULL;
        }
        if (L->mouse_hook) {
            UnhookWindowsHookEx(L->mouse_hook);
            L->mouse_hook = NULL;
        }
        TlsSetValue(g_tls_index, NULL);
        return 1;
    }

    /* 消息泵：GetMessageW 阻塞于内核，与 Python/GIL 完全无关 */
    {
        MSG msg;
        while (GetMessageW(&msg, NULL, 0, 0) > 0) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }

    if (L->kbd_hook) {
        UnhookWindowsHookEx(L->kbd_hook);
        L->kbd_hook = NULL;
    }
    if (L->mouse_hook) {
        UnhookWindowsHookEx(L->mouse_hook);
        L->mouse_hook = NULL;
    }
    TlsSetValue(g_tls_index, NULL);
    return 0;
}

/* ---------- 导出 API ---------- */

AXH_EXPORT int __stdcall axh_start(int hook_keyboard, int hook_mouse,
                                   axh_key_cb kcb, axh_mouse_cb mcb) {
    int handle = -1;
    int i;
    axh_listener* L;
    DWORD wait_result;

    if (!hook_keyboard && !hook_mouse)
        return -6;
    if (g_tls_index == TLS_OUT_OF_INDEXES)
        return -7;

    /* 原子抢占空闲槽位 */
    for (i = 0; i < AXH_MAX_LISTENERS; i++) {
        if (InterlockedCompareExchange(&g_listeners[i].slot_state,
                                       AXH_SLOT_RUNNING, AXH_SLOT_FREE)
                == AXH_SLOT_FREE) {
            handle = i;
            break;
        }
    }
    if (handle < 0)
        return -1;

    L = &g_listeners[handle];
    L->want_kbd = hook_keyboard ? 1 : 0;
    L->want_mouse = hook_mouse ? 1 : 0;
    L->kcb = kcb;
    L->mcb = mcb;
    L->key_mask = 0;
    L->mouse_mask = 0;
    L->kbd_hook = NULL;
    L->mouse_hook = NULL;

    /* 手动重置事件：pump 线程 SetEvent 报告初始化结果 */
    L->init_event = CreateEventW(NULL, TRUE, FALSE, NULL);
    if (!L->init_event) {
        L->slot_state = AXH_SLOT_FREE;
        return -7;
    }

    L->thread = CreateThread(NULL, 0, pump_proc, L, 0, &L->tid);
    if (!L->thread) {
        CloseHandle(L->init_event);
        L->init_event = NULL;
        L->slot_state = AXH_SLOT_FREE;
        return -2;
    }

    wait_result = WaitForSingleObject(L->init_event, 2000);
    if (wait_result != WAIT_OBJECT_0) {
        /* 初始化超时：尽力回收 */
        axh_stop(handle);
        return -3;
    }

    if (L->kbd_hook == NULL && L->want_kbd) {
        /* pump 线程已清理并退出 */
        WaitForSingleObject(L->thread, 2000);
        CloseHandle(L->thread);
        CloseHandle(L->init_event);
        L->thread = NULL;
        L->init_event = NULL;
        L->slot_state = AXH_SLOT_FREE;
        return -4;
    }
    if (L->mouse_hook == NULL && L->want_mouse) {
        WaitForSingleObject(L->thread, 2000);
        CloseHandle(L->thread);
        CloseHandle(L->init_event);
        L->thread = NULL;
        L->init_event = NULL;
        L->slot_state = AXH_SLOT_FREE;
        return -5;
    }

    return handle;
}

AXH_EXPORT int __stdcall axh_stop(int handle) {
    axh_listener* L;
    DWORD wait_result;

    if (handle < 0 || handle >= AXH_MAX_LISTENERS)
        return -1;
    L = &g_listeners[handle];

    /* used: RUNNING -> STOPPING（并发 stop 只有一个能进入） */
    if (InterlockedCompareExchange(&L->slot_state, AXH_SLOT_STOPPING,
                                   AXH_SLOT_RUNNING) != AXH_SLOT_RUNNING)
        return -1;

    /* ① 掩码清零：C 回调立即短路，不再触碰 Python 回调 */
    InterlockedExchange(&L->key_mask, 0);
    InterlockedExchange(&L->mouse_mask, 0);
    /* ② 清回调指针（回调内部另有判空兜底） */
    L->kcb = NULL;
    L->mcb = NULL;

    /* ③ 唤醒消息泵，④ 等待其 Unhook 后退出 */
    PostThreadMessageW(L->tid, WM_QUIT, 0, 0);
    wait_result = WaitForSingleObject(L->thread, 5000);

    if (L->thread) {
        CloseHandle(L->thread);
        L->thread = NULL;
    }
    if (L->init_event) {
        CloseHandle(L->init_event);
        L->init_event = NULL;
    }
    L->tid = 0;
    L->slot_state = AXH_SLOT_FREE;

    return (wait_result == WAIT_OBJECT_0) ? 0 : -2;
}

AXH_EXPORT int __stdcall axh_is_running(int handle) {
    if (handle < 0 || handle >= AXH_MAX_LISTENERS)
        return 0;
    return (g_listeners[handle].slot_state == AXH_SLOT_RUNNING) ? 1 : 0;
}

AXH_EXPORT void __stdcall axh_set_masks(int handle, unsigned int key_mask,
                                        unsigned int mouse_mask) {
    axh_listener* L;
    if (handle < 0 || handle >= AXH_MAX_LISTENERS)
        return;
    L = &g_listeners[handle];
    if (L->slot_state != AXH_SLOT_RUNNING)
        return;
    InterlockedExchange(&L->key_mask, (LONG)key_mask);
    InterlockedExchange(&L->mouse_mask, (LONG)mouse_mask);
}

AXH_EXPORT unsigned int __stdcall axh_get_key_state(unsigned int vk) {
    if (vk >= 256)
        return 0;
    return g_key_state[vk];
}

AXH_EXPORT int __stdcall axh_get_cursor_pos(int* x, int* y) {
    POINT pt;
    if (!GetCursorPos(&pt))
        return -1;
    if (x) *x = (int)pt.x;
    if (y) *y = (int)pt.y;
    return 0;
}

AXH_EXPORT const char* __stdcall axh_version(void) {
    return AXH_VERSION;
}

/* ---------- DLL 入口 ---------- */

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved) {
    (void)lpReserved;
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            g_hinst = hinstDLL; /* SetWindowsHookExW 的 hMod 参数 */
            g_tls_index = TlsAlloc();
            if (g_tls_index == TLS_OUT_OF_INDEXES)
                return FALSE;
            DisableThreadLibraryCalls(hinstDLL);
            break;
        case DLL_PROCESS_DETACH:
            if (g_tls_index != TLS_OUT_OF_INDEXES) {
                TlsFree(g_tls_index);
                g_tls_index = TLS_OUT_OF_INDEXES;
            }
            break;
        default:
            break;
    }
    return TRUE;
}
