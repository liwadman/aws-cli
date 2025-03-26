# Copyright 2013 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""
This customization allows the output from getsessiontoken be able to write directly to 
an AWS Profile so that it can immediately be used by the AWS CLI, or SDK
"""
from awscli.arguments import CustomArgument
import copy

class ProfileArgument(CustomArgument):
    """A new profile argument to be injected at the top level."""
    
    def __init__(self, name, help_text=None, cli_type_name=None, **kwargs):
        super(ProfileArgument, self).__init__(
            name=name,
            help_text=help_text,
            cli_type_name=cli_type_name
        )

    def add_to_params(self, parameters, value):
        # Don't add to the API parameters at all
        # Instead, store it in the handler_context which won't be passed to botocore
        if value is not None and 'handler_context' in parameters:
            parameters['handler_context']['target_profile'] = value
        
class ProfileArgumentHoister(object):
    def __init__(self):
        self._serialized_name = 'target-profile'
        self._name = 'target-profile'
    
    def hoist(self, session, argument_table, **kwargs):
        help_text = 'The credential profile to update with the session token'
        argument_table['target-profile'] = ProfileArgument(
            'target-profile',
            help_text=help_text,
            cli_type_name='string',
            nargs='1',
            default=None,
            required=False,
            group_name='target-profile'
        )

def register_sts_profile(cli):
    cli.register(
        'building-argument-table.sts.get-session-token',
        ProfileArgumentHoister().hoist
    )
    
    # Register a response handler to process the profile after the call
    cli.register(
        'after-call.sts.get-session-token',
        handle_profile_update
    )

def handle_profile_update(parsed, parsed_globals, **kwargs):
    # This is where we'll handle updating the profile with the session token
    pass


        # name,
        # help_text='',
        # dest=None,
        # default=None,
        # action=None,
        # required=None,
        # choices=None,
        # nargs=None,
        # cli_type_name=None,
        # group_name=None,
        # positional_arg=False,
        # no_paramfile=False,
        # argument_model=None,
        # synopsis='',
        # const=None,