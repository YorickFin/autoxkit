/*
 * autoxhook.h - autoxkit 低级键盘/鼠标钩子 DLL（纯 Win32 C，无 Python 依赖）
 *
 * 设计要点：
 *   1. DLL 不链接任何 Python 运行时；Python 侧通过 ctypes 传入
 *      WINFUNCTYPE 函数指针，本 DLL 以纯 C 整数参数调用之。
 *      因此一份 DLL 可跨 Python 3.10~3.13+ 所有版本使用。
 *   2. 钩子安装、消息泵线程、结构体解析、订阅掩码短路、按键状态跟踪
 *      全部在本 DLL 内完成（核心事件链路整体迁出 Python）。
 *   3. 回调返回 1 = 拦截（吞事件），返回 0 = 放行，保持拦截语义。
 */
#ifndef AUTOXHOOK_H
#define AUTOXHOOK_H

#ifdef __cplusplus
extern "C" {
#endif

#define AXH_EXPORT __declspec(dllexport)

/*
 * Python 侧回调原型（由 ctypes WINFUNCTYPE 传入，DLL 持有并调用）。
 * 返回值：1 = 拦截事件（不再向系统传播），0 = 放行。
 *
 * 键盘：msg = WM_KEYDOWN/WM_KEYUP/WM_SYSKEYDOWN/WM_SYSKEYUP
 *       vk   = 虚拟键码, scan = 扫描码,
 *       flags= KBDLLHOOKSTRUCT.flags 原始值（LLKHF_INJECTED=0x10 等）
 * 鼠标：msg = WM_LBUTTONDOWN/UP, WM_RBUTTONDOWN/UP, WM_MBUTTONDOWN/UP,
 *             WM_MOUSEWHEEL, WM_XBUTTONDOWN/UP（未启用 MOVE）
 *       x/y  = 屏幕坐标（支持多显示器负值）
 *       data = WM_MOUSEWHEEL: 有符号原始 delta（约 ±120 的倍数）
 *              WM_XBUTTONDOWN/UP: 1=XBUTTON1, 2=XBUTTON2
 *              其他: 0
 *       flags= MSLLHOOKSTRUCT.flags 原始值（LLMHF_INJECTED=0x10 等）
 */
typedef int (*axh_key_cb)(int msg, int vk, int scan, int flags, unsigned int time);
typedef int (*axh_mouse_cb)(int msg, int x, int y, int data, int flags, unsigned int time);

/* 键盘事件掩码位 */
enum {
    AXH_KEY_DOWN = 1 << 0,   /* WM_KEYDOWN / WM_SYSKEYDOWN */
    AXH_KEY_UP   = 1 << 1    /* WM_KEYUP   / WM_SYSKEYUP   */
};

/* 鼠标事件掩码位 */
enum {
    AXH_M_LDOWN = 1 << 0,
    AXH_M_LUP   = 1 << 1,
    AXH_M_RDOWN = 1 << 2,
    AXH_M_RUP   = 1 << 3,
    AXH_M_MDOWN = 1 << 4,
    AXH_M_MUP   = 1 << 5,
    AXH_M_WHEEL = 1 << 6,   /* 任一 down/up 回调列表非空即应置位 */
    AXH_M_XDOWN = 1 << 7,
    AXH_M_XUP   = 1 << 8,
    AXH_M_MOVE  = 1 << 9    /* 预留：未订阅时高频移动事件在 C 层直接短路 */
};

/*
 * axh_start：安装钩子并启动消息泵线程。
 *   hook_keyboard / hook_mouse：是否安装对应钩子（0/1）
 *   kcb / mcb：Python 侧回调函数指针（不需要的类型可传 NULL）
 * 返回：>=0 为监听器句柄；<0 为错误码：
 *   -1 无空闲槽位  -2 创建线程失败  -3 初始化超时
 *   -4 键盘钩子安装失败  -5 鼠标钩子安装失败
 *   -6 参数无效（两类钩子均未请求）  -7 创建同步事件失败
 */
AXH_EXPORT int __stdcall axh_start(int hook_keyboard, int hook_mouse,
                                   axh_key_cb kcb, axh_mouse_cb mcb);

/* axh_stop：停止并卸载钩子。返回 0 成功；-1 句柄无效；-2 等待线程退出超时。 */
AXH_EXPORT int __stdcall axh_stop(int handle);

/* axh_is_running：句柄有效且正在运行返回 1，否则 0。 */
AXH_EXPORT int __stdcall axh_is_running(int handle);

/*
 * axh_set_masks：设置订阅掩码。只有置位的事件类型才会进入 Python 回调；
 * 未置位的事件在 C 回调内直接 CallNextHookEx，完全不触碰 Python/GIL。
 * 掩码位取值见上方枚举。滚轮需按"down 或 up 列表非空"置 AXH_M_WHEEL。
 */
AXH_EXPORT void __stdcall axh_set_masks(int handle, unsigned int key_mask,
                                        unsigned int mouse_mask);

/* axh_get_key_state：查询 DLL 维护的修饰键/锁键状态。
 * 仅跟踪 Alt/Shift/Ctrl（含 L/R 合成）与 NumLock/CapsLock/ScrollLock。
 * 值：修饰键 0x80=按下；锁键 0x01=开启。其他键恒为 0。 */
AXH_EXPORT unsigned int __stdcall axh_get_key_state(unsigned int vk);

/* axh_get_cursor_pos：GetCursorPos 包装。返回 0 成功，-1 失败。 */
AXH_EXPORT int __stdcall axh_get_cursor_pos(int* x, int* y);

/* axh_version：返回版本字符串（静态存储期）。 */
AXH_EXPORT const char* __stdcall axh_version(void);

#ifdef __cplusplus
}
#endif

#endif /* AUTOXHOOK_H */
