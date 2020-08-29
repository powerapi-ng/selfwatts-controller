#include <Python.h>
#include <cpuid.h>
#include <linux/perf_event.h>
#include <perfmon/pfmlib_perf_event.h>

static PyObject *
get_available_perf_counters(PyObject * Py_UNUSED(self), PyObject * Py_UNUSED(args))
{
    const unsigned int leaf = 0x0000000A; /* Architectural Performance Monitoring Leaf */
    unsigned int eax, ebx, ecx, edx;
    long available_perf_counter;

    if (!__get_cpuid(leaf, &eax, &ebx, &ecx, &edx)) {
        PyErr_SetString(PyExc_RuntimeError, "number of available perf counter is unknown for this CPU.");
        return NULL;
    }

    available_perf_counter = (eax >> 8) & 0xFF; /* Bits 15 - 08: Number of general-purpose performance monitoring counter per logical processor. */
    return PyLong_FromLong(available_perf_counter);
}

static int
populate_available_pmus(PyObject *available_pmus_list)
{
    pfm_pmu_t pmu = {0};
    pfm_pmu_info_t pmu_info = {0};
    PyObject *pmu_name_str = NULL;

    for (pmu = PFM_PMU_NONE; pmu < PFM_PMU_MAX; pmu++) {
        if (pfm_get_pmu_info(pmu, &pmu_info) != PFM_SUCCESS)
            continue;

        if (pmu_info.is_present) {
            pmu_name_str = PyUnicode_FromFormat("%s", pmu_info.name);
            if (!pmu_name_str)
                return -1;

            if (PyList_Append(available_pmus_list, pmu_name_str))
                return -1;
        }
    }

    return 0;
}

static PyObject *
get_available_pmus(PyObject * Py_UNUSED(self), PyObject * Py_UNUSED(args))
{
    PyObject *available_pmus_list = NULL;

    available_pmus_list = PyList_New(0);
    if (!available_pmus_list)
        return NULL;

    if (populate_available_pmus(available_pmus_list))
        return NULL;

    return available_pmus_list;
}

static int
setup_pmu(const char *name, pfm_pmu_info_t *info)
{
    pfm_pmu_t pmu = {0};
    pfm_pmu_info_t pmu_info = {0};

    for (pmu = PFM_PMU_NONE; pmu < PFM_PMU_MAX; pmu++) {
        if (pfm_get_pmu_info(pmu, &pmu_info) != PFM_SUCCESS)
            continue;

        if (pmu_info.is_present && !strcmp(pmu_info.name, name)) {
            *info = pmu_info;
            return 0;
        }
    }

    return -1;
}

static int
populate_available_events(const pfm_pmu_info_t *pmu_info, PyObject *available_events_list)
{
    pfm_event_info_t event_info = {0};
    pfm_event_attr_info_t attr_info = {0};
    int ide, ida;
    PyObject *event_name_str = NULL;

    for (ide = pmu_info->first_event; ide != -1; ide = pfm_get_event_next(ide)) {
        if (pfm_get_event_info(ide, PFM_OS_NONE, &event_info) != PFM_SUCCESS)
            continue;

        if (event_info.equiv != NULL)
            continue;

        if (event_info.nattrs == 0) {
            event_name_str = PyUnicode_FromFormat("%s", event_info.name);
            if (!event_name_str)
                return -1;

            if (PyList_Append(available_events_list, event_name_str))
                return -1;
        }

        for (ida = 0; ida <= event_info.nattrs; ida++) {
            if (pfm_get_event_attr_info(ide, ida, PFM_OS_NONE, &attr_info) != PFM_SUCCESS)
                continue;

            if (attr_info.equiv != NULL)
                continue;

            if (attr_info.type != PFM_ATTR_UMASK)
                continue;

            event_name_str = PyUnicode_FromFormat("%s:%s", event_info.name, attr_info.name);
            if (!event_name_str)
                return -1;

            if (PyList_Append(available_events_list, event_name_str))
                return -1;
        }
    }

    return 0;
}

static PyObject *
get_available_events_for_pmu(PyObject * Py_UNUSED(self), PyObject *args)
{
    const char *pmu_name = NULL;
    pfm_pmu_info_t pmu_info = {0};
    PyObject *available_events_list = NULL;

    if (!PyArg_ParseTuple(args, "s", &pmu_name))
        return NULL;

    if (setup_pmu(pmu_name, &pmu_info)) {
        PyErr_SetString(PyExc_ValueError, "invalid PMU name.");
        return NULL;
    }

    available_events_list = PyList_New(0);
    if (!available_events_list)
        return NULL;

    if (populate_available_events(&pmu_info, available_events_list))
        return NULL;

    return available_events_list;
}

static void
libpfm_wrapper_deinitialize(void * Py_UNUSED(self))
{
    pfm_terminate();
}

static PyMethodDef libpfm_wrapper_methods[] = {
    {"get_available_perf_counters", get_available_perf_counters, METH_NOARGS, "Returns the number of available performance counters."},
    {"get_available_pmus", get_available_pmus, METH_NOARGS, "Returns the list of available PMUs."},
    {"get_available_events_for_pmu", get_available_events_for_pmu, METH_VARARGS, "Returns the list of available events name for the given PMU."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef libpfm_wrapper_definition = {
    PyModuleDef_HEAD_INIT,
    "libpfm_wrapper",
    "Wrapper to the libpfm4 library.",
    -1,
    libpfm_wrapper_methods,
    NULL,
    NULL,
    NULL,
    libpfm_wrapper_deinitialize
};

PyMODINIT_FUNC
PyInit_libpfm_wrapper(void)
{
    int pfm_ret;

    pfm_ret = pfm_initialize();
    if (pfm_ret != PFM_SUCCESS) {
        PyErr_Format(PyExc_RuntimeError, "failed to initialize libpfm: %s", pfm_strerror(pfm_ret));
        return NULL;
    }

    return PyModule_Create(&libpfm_wrapper_definition);
}

