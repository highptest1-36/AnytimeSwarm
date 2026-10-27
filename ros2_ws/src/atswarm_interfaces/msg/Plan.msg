builtin_interfaces/Time stamp
uint32 version
string trigger          # start | event | deviation | periodic
string method
float64 t_trigger       # mission time of the trigger
float64 t_snapshot      # mission time of the planning snapshot
float64 t_publish       # mission time at which the plan is released (snapshot + kappa * planning time)
float64 planning_ms     # wall-clock CPU time of the planning call
uint32 iterations
string stop_reason
float64 objective
Route[] routes
