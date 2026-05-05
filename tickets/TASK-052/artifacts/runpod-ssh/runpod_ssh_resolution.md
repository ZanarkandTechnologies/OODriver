# RunPod SSH Resolution

- Pod: `thundering_apricot_locust` (`zqqmn9ryopmmro`)
- SSH host: `root@195.26.233.80`
- SSH options: `-p 55050 -i /Users/kenjipcx/.ssh/id_ed25519_runpod`
- Source: `rest_port_mappings`

## Shell

```bash
export GPU_SSH_HOST='root@195.26.233.80'
export GPU_SSH_OPTS='-p 55050 -i /Users/kenjipcx/.ssh/id_ed25519_runpod'
```

## Probe

```bash
ssh -p 55050 -i /Users/kenjipcx/.ssh/id_ed25519_runpod root@195.26.233.80 'nvidia-smi && df -h /workspace /'
```
