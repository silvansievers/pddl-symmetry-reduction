#ifndef TASKS_ROOT_TASK_H
#define TASKS_ROOT_TASK_H

#include "../abstract_task.h"

namespace tasks {
extern std::shared_ptr<AbstractTask> g_root_task;
extern std::vector<std::vector<int>> g_permutations;
extern std::vector<int> g_dom_sum_by_var;
extern std::vector<int> g_var_by_val;
extern int g_permutation_length;
extern void read_root_task(std::istream &in);
}
#endif
