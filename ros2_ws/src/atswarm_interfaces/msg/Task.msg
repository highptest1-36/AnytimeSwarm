# One task of the mission. Coordinates in the mission map frame (metres, x = East, y = North, depot at map centre).
uint8 HIDDEN=0
uint8 OPEN=1
uint8 ASSIGNED=2
uint8 IN_SERVICE=3
uint8 SERVED=4
uint8 LATE=5
uint8 MISSED=6
uint32 id
float64 x
float64 y
float64 release      # mission time (s)
float64 deadline     # mission time (s), current (possibly tightened) value
float64 service      # nominal service duration (s)
float64 reward
uint8 status
int32 uav            # assigned UAV, -1 = none
