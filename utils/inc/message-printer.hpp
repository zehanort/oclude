#ifndef __MP_HPP__
#define __MP_HPP__

#include <iostream>
#include <string>

class MessagePrinter {

private:

    std::string appname, prompt, usagestr;

public:

    MessagePrinter(std::string sourcefile, std::string _usagestr) : usagestr(_usagestr) {
        appname = sourcefile.substr(sourcefile.find_last_of("/") + 1, sourcefile.size() - 1);
        appname = appname.substr(0, appname.find_last_of("."));
        prompt = "[" + appname + "] ";
    }

    void operator()(std::string message, bool nl=true) {
        std::cerr << prompt << message;
        if (nl) std::cerr << std::endl;
    }

    void usage() {
        std::cerr << "usage: ./" << appname << ' ' << usagestr << std::endl;
    }

};

#endif
