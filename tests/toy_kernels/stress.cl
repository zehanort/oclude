__kernel void boolvartest(__global int *buf) {
	bool a = 12 < 13;
	bool b = true;
	bool c;
	c = a || b;
	bool d = !a && b;
	if (a && b && c || d)
		a = !a && !b;
	return;
}

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

__kernel void dowhiletest(__global int *buf) {
	int a, b, c, d, x;
	a = b = c = 1;
	x = -10;
	// a simple do-while first
	do x += 2; while (x < -5);
	do x++; while (a && x);
	do x++;	while (a && b && (x < 10));
	b = 2;
	// a simple while
	while (!a && b && !c || (x < 20)) x++;
	// a do-while with stuff inside
	do {
		x += 2;
		if (b || c && a) x--;
	} while (a && (x < 30));
	return;
}

__kernel void fortest(__global int *buf) {
	int a, b, c, d, x;
	a = b = c = 1;
	x = -10;
	for (int i = 0; i < 10; i++)
		x++;
	for (int i = 0; i < 10; i++)
		for (int j = 2; j < 100; j *= 2)
			x++;
	/* we assume that we will not find        *
	 * compound conditions if for statements, *
	 * for simplicity                         */
	// for (int i = 0; a && !b || i < 10; i++)
	// 	x++;
	// for (int i = 0; !a || i < 10; i++)
	// 	for (int j = 2; b && j < 100; j *= 2)
	// 		x++;
	for (int i = 0; i < 2; i++) {
		int kapa = 12;
		int trela = 43;
		for (int j = 0; j < 2; j++)
			x *= (kapa + trela);
	}
	return;
}
