#include <Python.h>
#include <windows.h>

static PyObject* pump_pump_messages(PyObject* self, PyObject* args) {
    MSG msg;
    BOOL ret;
    Py_BEGIN_ALLOW_THREADS
    while ((ret = GetMessageW(&msg, NULL, 0, 0)) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    Py_END_ALLOW_THREADS
    return PyLong_FromLong(ret);
}

static PyObject* pump_post_quit(PyObject* self, PyObject* args) {
    DWORD thread_id;
    if (!PyArg_ParseTuple(args, "k", &thread_id))
        return NULL;
    PostThreadMessageW(thread_id, WM_QUIT, 0, 0);
    Py_RETURN_NONE;
}

static PyMethodDef PumpMethods[] = {
    {"pump_messages", pump_pump_messages, METH_NOARGS, "Windows message pump with GIL released."},
    {"post_quit", pump_post_quit, METH_VARARGS, "Post WM_QUIT to a thread."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef pumpmodule = {
    PyModuleDef_HEAD_INIT, "_pump", NULL, -1, PumpMethods
};

PyMODINIT_FUNC PyInit__pump(void) {
    return PyModule_Create(&pumpmodule);
}
