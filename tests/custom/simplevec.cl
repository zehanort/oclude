__kernel void dotprod(float4 a, float4 b, __global float *c) {
   int i = get_global_id(0);
   if(c[i] != 0)
       c[i] = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}

__kernel void vecadd(__global float4 *a, __constant float4 *b, __global float4 *c) {
   int i = get_global_id(0);
   if(a[i].x != 0) {
       c[i].x = a[i].x + b[i].x;
       c[i].y = a[i].y + b[i].y;
       c[i].z = a[i].z + b[i].z;
       c[i].w = a[i].w + b[i].w;
   }
}
