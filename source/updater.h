#pragma once
#include <stdbool.h>

// Checks Github API for new releases and downloads/overwrites the current NRO
void check_and_apply_updates(int argc, char* argv[]);
