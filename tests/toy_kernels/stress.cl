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
	if (a) {
		x = 1;
	}
	else {
		if (d) {
			x = 2;
		}
	}
	if (a) if (c) x = 10;
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
	while (x < 10) {
		x += 2;
		if (b) x--;
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

__kernel void terntest(__global int *buf) {
	int a, b, c, d, e, f, g, h, i, j;
	a = 1;
	b = 2;
	c = 3;
	d = (a > b) ? e + f : c * j;
	int aaa = (!d) ? g + 2 : h * 3;
	const int bbb = (!e) ? h + 2 : i % 3;
	const int colId = 15 + ((a == 0) ? b%c : -3);
	return;
}

/************************************************************************
 * this is function findIndexBin from particlefilter/particle_single.cl *
 ************************************************************************/
int findIndexBin(__global float * CDF, int beginIndex, int endIndex, float value)
{
	if(endIndex < beginIndex)
		return -1;
	int middleIndex;
	while(endIndex > beginIndex)
	{
		middleIndex = beginIndex + ((endIndex-beginIndex)/2);
		if(CDF[middleIndex] >= value)
		{
			if(middleIndex == 0)
				return middleIndex;
			else if(CDF[middleIndex-1] < value)
				return middleIndex;
			else if(CDF[middleIndex-1] == value)
			{
				while(CDF[middleIndex] == value && middleIndex >= 0)
					middleIndex--;
				middleIndex++;
				return middleIndex;
			}
		}
		if(CDF[middleIndex] > value)
			endIndex = middleIndex-1;
		else
			beginIndex = middleIndex+1;
	}
	return -1;
}

/***************************************************************************
 * this is function dev_round_float from particlefilter/particle_single.cl *
 ***************************************************************************/
float dev_round_float(float value) {
    int newValue = (int) (value);
    if (value - newValue < .5f)
        return newValue;
    else
        return newValue++;
}

/**********************************************************************
 * this is function tex1Dfetch from particlefilter/particle_single.cl *
 **********************************************************************/
float tex1Dfetch(__read_only image2d_t img, int index){

	const sampler_t smp = CLK_NORMALIZED_COORDS_FALSE | //Natural coordinates
		CLK_ADDRESS_CLAMP | //Clamp to zeros
		CLK_FILTER_NEAREST; //Don't interpolate

	if (index < 0) return 0;
	//Divide desired position by 4 because there are 4 components per pixel
	int imgPos = index >> 2;

	int2 coords;
	coords.x = imgPos >> 13;
	coords.y = imgPos & 0x1fff;   //Reads the float4
	float4 temp = read_imagef(img, smp, coords);


	//Computes the remainder of imgPos / 4 to check if function should return x,y,z or w component.
	imgPos = index & 0x0003;

	if (imgPos < 2){
		if (imgPos == 0) return temp.x;
		else return temp.y;
	}
	else{
		if (imgPos == 2) return temp.z;
		else return temp.w;
	}
}

/***************************************************
 * this is function divRndUp from dwt2d/com_dwt.cl *
 ***************************************************/
int divRndUp(int n,
             int d)
{
    return (n / d) + ((n % d) ? 1 : 0);
}

/**************************************************************************
 * this is the only switch of rodinia suite: myocyte/kernel_gpu_opencl.cl *
 **************************************************************************/
int fmod(int x, int y) { return x % y; }

__kernel void switchtest(__global int *dummy) {
	float I_app, R_clamp;
	int timeinst = 2;
	int cycleLength = 2;
	int state = 1;
	int V_hold, V_test, V_clamp, d_initvalu_39;
	switch(state){
		case 0:
			I_app = 0;
			break;
		case 1:
			if(fmod(timeinst,cycleLength) <= 5){
				I_app = 9.5;
			}
			else{
				I_app = 0.0;
			}
			break;
		case 2:
			V_hold = -55;
			V_test = 0;
			if(timeinst>0.5 & timeinst<200.5){
				V_clamp = V_test;
			}
			else{
				V_clamp = V_hold;
			}
			R_clamp = 0.04;
			I_app = (V_clamp-d_initvalu_39)/R_clamp;
			break;
	}
	state = 42;
}
