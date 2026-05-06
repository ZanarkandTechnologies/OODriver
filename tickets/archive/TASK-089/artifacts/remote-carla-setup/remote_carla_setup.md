# Remote CARLA 0.9.16 Setup Probe

- host: RTX 6000 Ada RunPod `root@195.26.233.80:55050`
- install path: `/workspace/carla/CARLA_0.9.16`
- Python API: `carla` imports on remote Python.
- server launch: blocked by NVIDIA Vulkan ICD, non-root CARLA does not open port 2000.
- evidence: `carla_server_nonroot_3.log`, `client_probe_3.log`, `apt_xdg.log`.

## Client Probe

```json
{"connected": false, "error": "RuntimeError('time-out of 10000ms while waiting for the simulator, make sure the simulator is ready and connected to 127.0.0.1:2000')"}
```

## Vulkan Blocker

Remote `vulkaninfo --summary` returns `ERROR_INCOMPATIBLE_DRIVER` for `/etc/vulkan/icd.d/nvidia_icd.json` using `libGLX_nvidia.so.0`. This is a graphics-container/driver capability blocker, not a DriverX code blocker.
