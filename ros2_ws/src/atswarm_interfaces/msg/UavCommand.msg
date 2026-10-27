uint8 FAIL=0         # inject a UAV failure: the UAV lands and leaves the mission
uint8 START=1        # mission clock starts (uav_id ignored)
uint8 END=2          # mission over: every UAV returns above its take-off point and lands (uav_id ignored)
uint8 HOLD=3         # planning in progress: finish the current task, then wait for the next plan (uav_id ignored)
uint32 uav_id
uint8 kind
float64 mission_time
