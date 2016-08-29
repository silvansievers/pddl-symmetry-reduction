#include "dummy.hh"

#include <iostream>

using namespace std;

Dummy::Dummy(int value) : value(value) {
}

void Dummy::dump() const {
    cout << value << endl;
}
