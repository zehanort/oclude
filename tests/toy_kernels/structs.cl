typedef struct {
    uint u;
    int i1, i2;
    float f;
} data_struct;

struct reduce_struct_t {
    float as, bs;
};

struct damnyou_st {
    bool b;
    long l;
};

typedef int myint;

typedef struct damnyou_st damnyou;
typedef struct reduce_struct_t reduce_struct;

__kernel void stest(__global data_struct *a, __global data_struct *b, __global reduce_struct *c) {
  int i = get_global_id(0);
  c[i].as = a[i].i1 + a[i].i2 + a[i].f;
  c[i].bs = b[i].i1 + b[i].i2 + b[i].f;
}
