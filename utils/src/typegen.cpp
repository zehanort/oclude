#include "typegen.hpp"

namespace typegen {

typedef std::variant<std::pair<cl_int, cl_int>, std::pair<cl_uint, cl_uint>, std::pair<cl_float, cl_float>> limits_t;
typedef void (*genfunc_t) (void *, size_t, limits_t);

template <typename T>
void rand_fill(void *, size_t, limits_t);

class typeinfo_t {

private:
	std::unordered_map< std::string, std::tuple<size_t, genfunc_t, limits_t> > helpmap =
	{
		{ "int",   { sizeof(cl_int),   rand_fill<cl_int>,   std::pair<cl_int, cl_int>(0, 0)         } },
		{ "uint",  { sizeof(cl_uint),  rand_fill<cl_uint>,  std::pair<cl_uint, cl_uint>(0u, 0u)     } },
		{ "float", { sizeof(cl_float), rand_fill<cl_float>, std::pair<cl_float, cl_float>(.0f, .0f) } }
	};

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

void set_limits(int size) {
	std::get<std::pair<cl_int, cl_int>>(typeinfo.get_limits("int"))       = { -size, size };
	std::get<std::pair<cl_uint, cl_uint>>(typeinfo.get_limits("uint"))    = { 0u, (cl_uint)size };
	std::get<std::pair<cl_float, cl_float>>(typeinfo.get_limits("float")) = { (cl_float)-size, (cl_float)size };
}

std::pair<void*, size_t> generate_kernel_argument(std::string typestr, size_t nmemb) {
	size_t    typesize    = typeinfo.get_size(typestr);
	limits_t  typelimits  = typeinfo.get_limits(typestr);
	genfunc_t typegenfunc = typeinfo.get_genfunc(typestr);
	void *    buf         = malloc(typesize * nmemb);
	typegenfunc(buf, nmemb, typelimits);
	return std::make_pair(buf, typesize * nmemb);
}

} // end namespace typegen
