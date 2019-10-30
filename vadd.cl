__kernel void vadd(__constant float* a, __constant float* b, __global float* c, const unsigned int count) {
	int i = get_global_id(0);
	if(i < count) c[i] = a[i] + b[i];
}
