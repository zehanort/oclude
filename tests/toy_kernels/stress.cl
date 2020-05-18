__kernel void iftest(__global int *buf) {
	int a, b, c, d, x;
	if (a && b || c && d) x = 42;
	return;
}

__kernel void muchiftest(__global int *buf) {
	int a, b, c, d, e, f, x;
	if (a && b || c) x = 1;
	else if (a || b && c && d) x = 2;
	else if (e || a + b) x = 3;
	else x = 4;
	if (a && !b && d * f) x = 5;
}

__kernel void whiletest(__global int *buf) {
	int a, b, c, d, x;
	a = b = c = 1;
	x = -10;
	// a simple while first
	while (x < -5) x += 2;
	while (a && x) x++;
	while (a && b && (x < 10)) x++;
	b = 2;
	while (!a && b && !c || (x < 20)) x++;
	// while with stuff inside
	while (a && (x < 30)) {
		x += 2;
		if (b || c && a) x--;
	}
	return;
}
