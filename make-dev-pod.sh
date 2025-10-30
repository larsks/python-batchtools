#!/bin/bash

# exit on command failures
set -e

if [[ $1 = "-d" ]]; then
  echo "Delete dev pod"
  oc delete pod dev-pod --wait=false
  oc wait --for delete pod/dev-pod
fi

echo "Apply RBAC"
oc apply -f- <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dev-pod
rules:
  - apiGroups:
      - ""
    resources:
      - pods
      - pods/exec
    verbs:
      - create
      - delete
      - get
      - list
      - patch
      - update
      - watch
  - apiGroups:
      - ""
    resources:
      - pods/log
    verbs:
      - get
  - apiGroups:
      - "batch"
    resources:
      - jobs
    verbs:
      - create
      - delete
      - get
      - list
      - patch
      - update
      - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-pod
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: dev-pod
subjects:
  - kind: ServiceAccount
    name: default
EOF

if ! oc get pod dev-pod -o name >/dev/null 2>&1; then
  echo "Create dev pod"
  oc apply -f- <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: dev-pod
  labels:
    app: dev-pod
spec:
  containers:
  - command:
    - pause
    env:
      - name: HOME
        value: /home/batchtools
      - name: BATCHTOOLS_IMAGE
        value: ghcr.io/larsks/batchtools-dev:latest
      - name: BATCHTOOLS_GPU
        value: none
    image: ghcr.io/larsks/batchtools-dev:latest
    imagePullPolicy: Always
    name: dev-pod
    volumeMounts:
    - mountPath: /home/batchtools
      name: workdir
    workingDir: /home/batchtools
  volumes:
  - name: workdir
    emptyDir: {}
EOF
fi

echo "Wait for dev pod to start"

timeout 20 bash <<EOF
# First we wait until the pod is ready
oc wait --for condition=ready pod/dev-pod

# Then we wait until the container is responding
while ! oc rsh dev-pod true >/dev/null 2>&1; do sleep 1; done
EOF

echo "Copy local directory to dev pod"
tmpfile=$(mktemp excludeXXXXXX)
trap 'rm -f "$tmpfile"' EXIT
{
  echo "$tmpfile"
  ls -d .* | grep -v '^\.git'
  ls -d _*
} >>"$tmpfile"
RSYNC_RSH="oc rsh -c dev-pod" rsync --recursive --exclude-from="$tmpfile" . dev-pod:/home/batchtools/

echo "Install dependencies"
oc rsh dev-pod uv sync
