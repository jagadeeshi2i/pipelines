# Copyright 2019 kubeflow.org.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import datetime
from distutils.util import strtobool
import json
import os
import logging
import yaml
import launch_crd

from kubernetes import client as k8s_client
from kubernetes import config

def yamlOrJsonStr(str):
    if str == "" or str == None:
        return None
    return yaml.safe_load(str)

PyTorchJobGroup = "kubeflow.org"
PyTorchJobPlural = "pytorchjobs"

class PyTorchJob(launch_crd.K8sCR):
    def __init__(self, version="v1", client=None):
        super(PyTorchJob, self).__init__(PyTorchJobGroup, PyTorchJobPlural, version, client)

    def is_expected_conditions(self, inst, expected_conditions):
        conditions = inst.get('status', {}).get("conditions")
        if not conditions:
            return False, ""
        if conditions[-1]["type"] in expected_conditions and conditions[-1]["status"] == "True":
            return True, conditions[-1]["type"]
        else:
            return False, conditions[-1]["type"]

def main(argv=None):
    parser = argparse.ArgumentParser(description='Kubeflow PyTorchJob launcher')
    parser.add_argument('--name', type=str,
                        help='PyTorchJob name.')
    parser.add_argument('--namespace', type=str,
                        default='kubeflow',
                        help='PyTorchJob namespace.')
    parser.add_argument('--version', type=str,
                        default='v1',
                        help='PyTorchJob version.')
    parser.add_argument('--cleanPodPolicy', type=str,
                        default="Running",
                        help='Defines the policy for cleaning up pods after the PyTorchJob completes.')
    parser.add_argument('--ttlSecondsAfterFinished', type=int,
                        default=-1,
                        help='Defines the TTL for cleaning up finished PyTorchJobs.')
    parser.add_argument('--masterSpec', type=yamlOrJsonStr,
                        default={},
                        help='PyTorchJob master replicaSpecs.')
    parser.add_argument('--workerSpec', type=yamlOrJsonStr,
                        default={},
                        help='PyTorchJob worker replicaSpecs.')
    parser.add_argument('--deleteAfterDone', type=strtobool,
                        default=True,
                        help='When pytorchjob done, delete the pytorchjob automatically if it is True.')
    parser.add_argument('--pytorchjobTimeoutMinutes', type=int,
                        default=60*24,
                        help='Time in minutes to wait for the TFJob to reach end')

    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    logging.info('Generating pytorchjob template.')

    config.load_incluster_config()
    api_client = k8s_client.ApiClient()
    pytorchjob = PyTorchJob(version=args.version, client=api_client)
    inst = {
        "apiVersion": "%s/%s" % (PyTorchJobGroup, args.version),
        "kind": "PyTorchJob",
        "metadata": {
            "name": args.name,
            "namespace": args.namespace,
        },
        "spec": {
            "cleanPodPolicy": args.cleanPodPolicy,
            "pytorchReplicaSpecs": {
            },
        },
    }
    if args.ttlSecondsAfterFinished >=0:
        inst["spec"]["ttlSecondsAfterFinished"] = args.ttlSecondsAfterFinished
    if args.masterSpec:
        inst["spec"]["pytorchReplicaSpecs"]["Master"] = args.masterSpec
    if args.workerSpec:
        inst["spec"]["pytorchReplicaSpecs"]["Worker"] = args.workerSpec

    create_response = pytorchjob.create(inst)

    expected_conditions = ["Succeeded", "Failed"]
    pytorchjob.wait_for_condition(
        args.namespace, args.name, expected_conditions,
        timeout=datetime.timedelta(minutes=args.pytorchjobTimeoutMinutes))
    if args.deleteAfterDone:
        pytorchjob.delete(args.name, args.namespace)

if __name__== "__main__":
    main()
