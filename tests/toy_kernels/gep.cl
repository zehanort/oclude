__kernel void geptest(__global int *a, __constant int *b, __local int *c) {
    int lid = get_local_id(0);
    int i = get_global_id(0);
    a[i] = 2 * b[i];
    if (lid == 0) c[i] = 3 * b[i];
}

// __kernel void addrspacetest(__global int *x) {
//     int i = get_global_id(0);
//     if (i > 500)
//         x[i] = 10;
// }
