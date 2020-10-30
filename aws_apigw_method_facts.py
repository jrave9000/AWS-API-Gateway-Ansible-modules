#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_apigw_method_facts
version_added: 0.1
short_description: Get AWS API Gateway Resources facts.
description:
  - Create Amazon API Gateway VPC link
requirements: [ boto3 ]
author: '@jr9000'
options:
  rest_api_id:
    description:
      - The identifier of the associated RestApi.
    type: str
    required: True
  resource_id:
    description:
      - The Resource identifier for the Method resource.
    type: str
    required: True
  http_method:
    description:
      - Specifies the method request's HTTP method type.
    type: str
    required: True
    choices: ['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'ANY', 'OPTIONS']

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Get resources
  aws_apigw_method_facts:
    rest_api_id: "{{ rest_api_id }}"
    resource_id: "{{ resource_id }}"
    http_method: GET
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
        rest_api_id=dict(type='str', required=True),
        resource_id=dict(type='str', required=True),
        http_method=dict(type='str', choices=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'ANY', 'OPTIONS'], required=True)
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    rest_api_id = module.params.get('rest_api_id')
    resource_id = module.params.get('resource_id')
    http_method = module.params.get('http_method')
    changed = False
    exit_args = {}

    client = module.client('apigateway')
    
    msg = camel_dict_to_snake_dict(get_method(client, rest_api_id, resource_id, http_method))

    exit_args['msg'] = camel_dict_to_snake_dict(msg)
    exit_args['changed'] = changed

    module.exit_json(**exit_args)

retry_params = {'retries': 10, 'delay': 10, 'catch_extra_error_codes': ['TooManyRequestsException']}

@AWSRetry.jittered_backoff(**retry_params)
def get_method(client, rest_api_id, resource_id, http_method):
    return client.get_method(restApiId=rest_api_id, resourceId=resource_id, httpMethod=http_method)

if __name__ == '__main__':
    main()

