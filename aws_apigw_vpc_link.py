#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_apigw_vpc_link
version_added: 0.1
short_description: Manage VPC link
description:
  - Manage Amazon API Gateway VPC link
requirements: [ boto3 ]
author: '@jr9000'
options:
  name:
    description:
      - The name used to label and identify the VPC link.
      - Required when I(state=present)
    type: str
  target_arns:
    description:
      - The ARN of the network load balancer of the VPC targeted by the VPC link. The network load balancer must be owned by the same AWS account of the API owner.
      - Required when I(state=present)
    type: list
    elements: str
  state:
    description:
      - Create or delete VPC link.
      - When I(state=absent), I(id) is required.
      - When I(state=present), then I(name) and I(target_arns) are required.
    default: present
  id:
    description:
      - The identifier of the Vpc link.
      - Required when I(state=absent)
    type: str
  description:
    description: The description of the VPC link.
    type: str
  tags:
    description:
      - The key-value map of strings. The valid character set is I([a-zA-Z+-=._:/]). The tag key can be up to 128 characters and must not start with I(aws:). The tag value can be up to 256 characters.
    type: dict
  wait:
    description:
      - Wait for the VPC link to reach its desired state before returning.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 300
    type: int
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Create VPC Link
  aws_apigw_vpc_link:
    name: mylink
    state: present
    description: 'some description'
    target_arns:
      - 'arn:aws:elasticloadbalancing:region-code:account-id:loadbalancer/net/load-balancer-name/load-balancer-id'
    tags:
      version: 15
      sometag: yes
- name: Delete VPC Link
  aws_apigw_vpc_link:
    id: zhbmrd
    state: absent
'''

RETURN = r'''
msg:
  description: Message
  returned: success
  type: dict
  sample: ''
'''

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

import traceback
import time
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def main():
    argument_spec = dict(
        name=dict(type='str'),
        target_arns=dict(type='list', elements='str'),
        description=dict(type='str', default=''),
        state=dict(default='present', choices=['present', 'absent']),
        id=dict(type='str'),
        tags=dict(type='dict'),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=300)
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_if=[
                ['state', 'present', ['name', 'target_arns']],
                ['state', 'absent', ['id']]
        ]
    )

    name = module.params.get('name')
    target_arns = module.params.get('target_arns')
    description = module.params.get('description')
    id = module.params.get('id')
    state = module.params.get('state')
    tags = module.params.get('tags')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    changed = True
    exit_args = {}
    msg = ''

    client = module.client('apigateway')

    if state == 'absent':
        msg = delete_vpc_link(client, id)
        if wait:
            if check_vpc_link(client, id, wait, wait_timeout) != 'NOTFOUND':
                error_msg = 'VPC link status: ' + status
                module.fail_json(msg=error_msg)

    elif state == 'present':
        vpc_link_list = camel_dict_to_snake_dict(get_vpc_link_list(client))
        for i in vpc_link_list['items']:
            if i['target_arns'] == target_arns:
                if i['name'] == name and i['status'] != 'FAILED':
                    module.exit_json(changed=False, msg=i)
                else:
                    error_msg = 'VPC link for target arns already exists with the different name: ' + i['name']
                    module.fail_json(msg=error_msg)
        msg = create_vpc_link(client, name, target_arns, description, tags)
        if wait:
            status = check_vpc_link(client, msg['id'], wait, wait_timeout)
            if status != 'AVAILABLE':
                error_msg = 'VPC link status: ' + status
                module.fail_json(msg=error_msg)
            # Changes VPC link status in module responce, otherwise it's confusing (outdated)
            msg['status'] = status

    exit_args['msg'] = camel_dict_to_snake_dict(msg)
    exit_args['changed'] = changed

    module.exit_json(**exit_args)

retry_params = {'retries': 10, 'delay': 10, 'catch_extra_error_codes': ['TooManyRequestsException']}

def check_vpc_link(client, id, wait, wait_timeout):
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        try:
            status = camel_dict_to_snake_dict(client.get_vpc_link(vpcLinkId=id))['status']
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'NotFoundException':
                return 'NOTFOUND'
        if status == 'FAILED':
            return status
        if status != 'AVAILABLE':
            time.sleep(5)
        else:
            return status
    if wait_timeout <= time.time():
        return 'ERROR: TIMEOUT'

@AWSRetry.jittered_backoff(**retry_params)
def get_vpc_link_list(client):
    return client.get_vpc_links(limit=500)

@AWSRetry.jittered_backoff(**retry_params)
def delete_vpc_link(client, id):
    return client.delete_vpc_link(vpcLinkId=id)

@AWSRetry.jittered_backoff(**retry_params)
def create_vpc_link(client, name,target_arns, description=None, tags={}):
    return client.create_vpc_link(name=name, description=description, targetArns=target_arns, tags=tags)

if __name__ == '__main__':
    main()

