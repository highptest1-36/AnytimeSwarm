cmake_minimum_required(VERSION 3.8)
project(atswarm_interfaces)
find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Task.msg" "msg/TaskArray.msg" "msg/UavState.msg" "msg/FleetState.msg"
  "msg/Route.msg" "msg/Plan.msg" "msg/TaskReport.msg" "msg/UavCommand.msg"
  DEPENDENCIES builtin_interfaces)
ament_export_dependencies(rosidl_default_runtime)
ament_package()
