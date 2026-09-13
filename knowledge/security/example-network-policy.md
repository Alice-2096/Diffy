# Example network policy

## Public ingress

Fictional POC rule: production workloads should not accept `0.0.0.0/0` or
`::/0` directly. Public traffic should pass through an approved edge component.
