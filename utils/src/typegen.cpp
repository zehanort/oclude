#include "typegen.hpp"

/*
 * To add a new OpenCL primitive type, just add the type name (without "cl_") in the TYPELIST below,
 * making sure that the last one is inserted with LASTTYPE and not with TYPE (see default TYPELIST below)
 * !!! BE WARNED !!! This source code is NOT guaranteed to compile on every machine out there:
 * cl_bool and cl_ushort are emitted due to collisions with other types, and some of the existing ones
 * may lead to unpredicted collisions based on the underlying OS/hardware.
 * So, edit TYPELIST until it compiles and proceed with caution... :)
 */

#define CL(X) cl_ ## X

// NOTE: cl_bool is the same as cl_uint (that is, unsigned int), so it is emitted from limits_t
// NOTE: cl_ushort breaks the helpmap, because ushort is basically half

#define TYPELIST TYPE(char)     \
                 TYPE(uchar)    \
                 TYPE(short)    \
                 TYPE(int)      \
                 TYPE(uint)     \
                 TYPE(long)     \
                 TYPE(ulong)    \
                 TYPE(float)    \
                 TYPE(double)   \
                 LASTTYPE(half)

#define TYPE(X) LASTTYPE(X) DELIM
#define LASTTYPE(X) EACH(X)

namespace typegen {

#define EACH(X) std::pair<CL(X), CL(X)>
#define DELIM ,
typedef std::variant<TYPELIST> limits_t;
#undef EACH
#undef DELIM

typedef void (*genfunc_t) (void *, size_t, limits_t);

template <typename T>
void rand_fill(void *, size_t, limits_t);

class typeinfo_t {

private:

#define EACH(X) { #X, { sizeof(CL(X)), rand_fill<CL(X)>, std::pair<CL(X), CL(X)>(0, 0) } }
#define DELIM ,
    std::unordered_map< std::string, std::tuple<size_t, genfunc_t, limits_t> > helpmap = { TYPELIST };
#undef EACH
#undef DELIM

public:

    size_t    get_size    (std::string typestr) { return std::get<0>(helpmap[typestr]); };
    genfunc_t get_genfunc (std::string typestr) { return std::get<1>(helpmap[typestr]); };
    limits_t& get_limits  (std::string typestr) { return std::get<2>(helpmap[typestr]); };

};

std::random_device rd;
std::mt19937 gen(rd());
typeinfo_t typeinfo;

template<typename T>
using uniform_distribution =
typename std::enable_if
<
    std::is_integral<T>::value || std::is_floating_point<T>::value,
    typename std::conditional
    <
        std::is_floating_point<T>::value,
        std::uniform_real_distribution<T>,
        std::uniform_int_distribution<T>
    >::type
>::type;

template <typename T>
void generate_rand_values(T& a, limits_t limits) {
    T l, h;
    auto limits_pair = std::get<std::pair<T, T>>(limits);
    l = limits_pair.first;
    h = limits_pair.second;
    uniform_distribution<T> d(l, h);
    a = d(gen);
}

template <typename T>
void rand_fill(void * buf, size_t nmemb, limits_t limits) {
    T * trubuf = (T *)buf;
    for(size_t i = 0; i < nmemb; i++)
        generate_rand_values<T>(trubuf[i], limits);
    return;
}

#define MAX(X, Y) (X > Y ? X : Y)
#define MIN(X, Y) (X < Y ? X : Y)
/*
 * min limit -> the max between the type min value and -size
 * max limit -> the min between the type max value and size
 */
#define EACH(X) std::get<std::pair<CL(X), CL(X)>>(typeinfo.get_limits(#X)) = \
{                                                                            \
    ( std::numeric_limits<CL(X)>::min() == 0 ? 0 :                           \
        (CL(X))MAX(std::numeric_limits<CL(X)>::min(), -size)                 \
    ),                                                                       \
    ( (CL(X))MIN((long long)std::numeric_limits<CL(X)>::max(), size) )       \
}
#define DELIM ;
void set_limits(int size) { TYPELIST; }
#undef EACH
#undef DELIM

std::pair<void*, size_t> generate_kernel_argument(std::string typestr, size_t nmemb) {
    size_t    typesize    = typeinfo.get_size(typestr);
    limits_t  typelimits  = typeinfo.get_limits(typestr);
    genfunc_t typegenfunc = typeinfo.get_genfunc(typestr);
    void *    buf         = malloc(typesize * nmemb);
    typegenfunc(buf, nmemb, typelimits);
    return std::make_pair(buf, typesize * nmemb);
}

} // end namespace typegen
