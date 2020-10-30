#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_apigw_vpc_links_facts
version_added: 0.1
short_description: Gets the VpcLinks collection under the caller's account in a selected region.
description:
  - Create Amazon API Gateway VPC link
requirements: [ boto3 ]
author: '@jr9000'
options:

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Get resources
  aws_apigw_vpc_links_facts:
'''

RETURN = r'''
"msg": {
}
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
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    changed = False
    exit_args = {}

    client = module.client('apigateway')
    
    msg = camel_dict_to_snake_dict(get_vpc_links(client))

    exit_args['msg'] = camel_dict_to_snake_dict(msg)
    exit_args['changed'] = changed

    module.exit_json(**exit_args)

retry_params = {'retries': 10, 'delay': 10, 'catch_extra_error_codes': ['TooManyRequestsException']}

@AWSRetry.jittered_backoff(**retry_params)
def get_vpc_links(client):
    return client.get_vpc_links(limit=500)

if __name__ == '__main__':
    main()

