uint8 INIT=0
uint8 TAKEOFF=1
uint8 IDLE=2
uint8 TRANSIT=3
uint8 SERVICE=4
uint8 FAILED=5
uint32 id
uint8 phase
bool alive
float64 x            # mission map frame (m)
float64 y
float64 z            # altitude (m)
float64 speed        # current horizontal ground speed (m/s)
float64 energy       # remaining energy proxy (metres of flight)
int32 current_task   # task being flown to / served, -1 = none
float64 ready_time   # nominal estimate of the mission time at which the current task is finished
float64 ready_x      # position at ready_time
float64 ready_y
float64 ready_energy # energy proxy at ready_time
uint32 plan_version  # last plan accepted by this UAV
