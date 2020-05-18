__kernel void condtest(__global int *buf) {
	int a, b, c, d, x;
	if (a && b || c && d) x = 42;
	return;
}	
