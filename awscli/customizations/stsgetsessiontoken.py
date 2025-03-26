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
THis customization allows the output from getsessiontoken be able to write directly to 
an AWS Profile so that it can immediately be used by the AWS CLI, or SDK
"""
import os
import configparser

from awscli.customizations.arguments import StatefulArgument
from awscli.customizations.arguments import resolve_given_outfile_path
from awscli.customizations.arguments import is_parsed_result_successful



class STSGETSessionTokenWrapper(object):
    def __init__(self, event_handler):
        self._event_handler = event_handler
        self._target_profile = StatefulArgument(
            'target-profile',
            help_text='The credential profile to update with the session token',
            required=False,
            cli_type_name='string'
        )
        # Register for building arguments
        self._event_handler.register(
            'building-argument-table.sts.get-session-token',
            self._add_options,
        )
        # Register for completion
        self._event_handler.register(
            'complete-command.sts.get-session-token',
            self._complete_command
        )
        # Register for handling the response
        self._event_handler.register(
            'after-call.sts.get-session-token',
            self._handle_credentials
        )

    def _add_completion(self, command_table, **kwargs):
        """Add completion support for aws_completer"""
        if 'sts' in command_table:
            command_table['sts'].ARGUMENT_TABLE['target-profile'] = self._target_profile

    def _complete_command(self, parsed_args, **kwargs):
        """
        Handle command completion for the get-session-token command
        """
        completions = {}
        # Add argument name completion
        if not parsed_args.command_options:
            completions['_arg_names'] = ['--target-profile']
        # If we're in the middle of typing an argument name
        elif parsed_args.command_options and parsed_args.command_options[-1].startswith('--'):
            current_arg = parsed_args.command_options[-1]
            if '--target-profile'.startswith(current_arg):
                completions['_arg_names'] = ['--target-profile']
        # Add argument value completion
        elif not hasattr(parsed_args, 'target_profile') or parsed_args.target_profile is None:
            completions['target-profile'] = self._get_profile_choices(None, parsed_args)
        return completions
        
    def _get_profile_choices(self, parsed_args, **kwargs):
        """Return list of available profile names"""
        config = configparser.ConfigParser()
        config.read(os.path.expanduser('~/.aws/credentials'))
        config.read(os.path.expanduser('~/.aws/config'))
        return [profile for profile in config.sections()]

    def _add_options(self, argument_table, **kwargs):
        argument_table['target-profile'] = self._target_profile
    def _handle_credentials(self, parsed, **kwargs):
        if not is_parsed_result_successful(parsed):
            return
        
        if self._target_profile.value:
            profile_name = self._target_profile.value
            credentials = parsed.get('Credentials', {})
            
            try:
                self._update_profile_credentials(profile_name, credentials)
            except Exception as e:
                raise Exception(f"Failed to update profile {profile_name}: {str(e)}")

    def _update_profile_credentials(self, profile_name, credentials):
        """
        Helper method to update the AWS credentials file with session token
        """
        import configparser
        import os
        
        credentials_path = os.path.expanduser('~/.aws/credentials')
        
        config = configparser.ConfigParser()
        config.read(credentials_path)
        
        if not config.has_section(profile_name):
            config.add_section(profile_name)
            
        # Update the profile with the session token credentials
        config[profile_name]['aws_access_key_id'] = credentials.get('AccessKeyId')
        config[profile_name]['aws_secret_access_key'] = credentials.get('SecretAccessKey')
        config[profile_name]['aws_session_token'] = credentials.get('SessionToken')
        
        with open(credentials_path, 'w') as configfile:
            config.write(configfile)
            
def awscli_initialize(cli):
    """
    The entry point for the STS get-session-token customization.
    """
    cli.register('building-command-table.main', register_sts_getsessiontoken)

def register_sts_getsessiontoken(command_table, session, **kwargs):
    """
    The entry point for the STS get-session-token customization.
    """
    STSGETSessionTokenWrapper(session.get_component('event_emitter'))
