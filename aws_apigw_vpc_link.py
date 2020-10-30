#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_create_vpc_link
version_added: 0.1
short_description: Create VPC link
description:
  - Create Amazon API Gateway VPC link
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
  id:
    description:
      - The identifier of the Vpc link.
      - Required when I(state=absent)
    type: str
  description:
    description: The description of the VPC link.
    type: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Create VPC Link
  aws_vpc_link:
    name: mylink
    state: present
    description: 'some description'
      target_arns:
        - 'arn:aws:elasticloadbalancing:region-code:account-id:loadbalancer/net/load-balancer-name/load-balancer-id'

- name: Delete VPC Link
  aws_vpc_link:
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
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def main():
    argument_spec = dict(
        name=dict(type='str'),
        target_arns=dict(type='list', elements='str'),
        description=dict(type='str', default=''),
        state=dict(default='present', choices=['present', 'absent']),
        id=dict(type='str')
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
    changed = True
    exit_args = {}
    msg = ''
  
    client = module.client('apigateway')
    
    if state == 'absent':
        delete_vpc_link(client, id)
    elif state == 'present':
        vpc_link_list = camel_dict_to_snake_dict(get_vpc_link_list(client))
    for i in vpc_link_list['items']:
        if i['target_arns'] == target_arns:
            if i['name'] == name and i['status'] != 'FAILED':
                module.exit_json(changed=False, msg=i)
            else:
                error_msg = 'VPC link for target arns already exists with the different name: ' + i['name']
                module.fail_json(msg=error_msg)

    msg = create_vpc_link(client, name, target_arns, description)
    
    exit_args['msg'] = camel_dict_to_snake_dict(msg)
    exit_args['changed'] = changed

    module.exit_json(**exit_args)

retry_params = {'retries': 10, 'delay': 10, 'catch_extra_error_codes': ['TooManyRequestsException']}

@AWSRetry.jittered_backoff(**retry_params)
def get_vpc_link_list(client):
    return client.get_vpc_links(limit=500)

def delete_vpc_link(client, id):
    return client.delete_vpc_link(vpcLinkId=id)

@AWSRetry.jittered_backoff(**retry_params)
def create_vpc_link(client, name,target_arns, description=None):
    return client.create_vpc_link(name=name, description=description, targetArns=target_arns)

if __name__ == '__main__':
    main()

