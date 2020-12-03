import cush.defaults as defaults
#from cush import get_cush
from thewired import NamespaceConfigParser2

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)


class AwsCredential(object):
    """
    Description:
        AWS API Credentials object; just the access key id and secret access key
        strings
    """
    def __init__(self, access_key_id=None, secret_access_key=None, session_token=None):
        """
        Input:
            access_key_id: AWS API Access Key ID
            secret_access_key: AWS API Secret Access Key for this Access Key ID
        """
        self.access_key_id =  access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token

    def __str__(self):
        return 'AwsCredential: '  + self.access_key_id




class AwsRole(object):
    """
    Description:
        Container object for all the things needed to assume an AWS IAM Role
    """
    def __init__(self, nsroot, name, arn, source_creds_name, mfa=None,
            role_session_name=None):
        """
        Input:
            user_nsroot: nsroot of the user namespace (used to refer to source creds by
                nsid)
            arn: the arn of the AWS IAM role to assume
            mfa: the arn of the MFA device to use for MFA (optional)
            source_creds: nsid of another Cush User that can be used to retrieve the
                source credentials needed to assume the specified role
        """
        self.nsroot = nsroot
        self.name = name
        self.arn = arn
        self.source_creds_name = source_creds_name
        self.mfa = mfa
        self._source_creds = None
        self.role_session_name = role_session_name if  role_session_name else  f'cush_{self.name}'
        

        #- only filled in after assuming role
        self.access_key_id = None
        self.secret_access_key = None
        self.session_token = None

        #- assume role
        #self.assume_role()

    def __str__(self):
        desc = ''.join([
            f'{self.__class__.__name__}',
            f'(name={self.name}, '
            f'arn={self.arn}',
            f'source_creds_name={self.source_creds_name}',
            f'role_session_name={self.role_session_name})'])
        return desc


    @property
    def source_creds(self):
        """
        Description:
            dynamically return the source credentials
        Output:
            AwsCredential object with credentials created from self.source_creds_name
        """
        return self.nsroot.user.lookup(self.source_creds_name)
        

    def assume_role(self, session_name=None):
        """
        Description:
            Hit the AWS STS API and save the returned credentials
        """
        #TODO: use the botocore objects for role assumption that refresh themselves

        #from https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-api.html
        import boto3
        session = boto3.Session(
            access_key_id = self.source_creds.access_key_id,
            secret_access_key = self.source_creds.secret_access_key)

        sts = session.client('sts')
        response = sts.assume_role(
            RoleArn = self.arn,
            RoleSessionName = self.role_session_name)

        try:
            creds = response['Credentials']
            self.aws_credentials = AwsCredential(
                    access_key_id = response['Credentials']['access_key_id'],
                    secret_access_key = response['Credentials']['secret_access_key'],
                    session_token = response['Credentials']['session_token'])
        except KeyError as e:
            raise AwsError(f"AWS STS did not return a valid Credentials object in"\
                    "response: {e}")
        else:
            return self.aws_credentials
        


class CushUser(object):
    """
    Description:
        User object is just a named credential set
    """
    def __init__(self, name, credential):
        """
        Input:
            name: logical name for this user
            credential: sdk-specific credential object
        """
        super().__init__()
        self.name = name
        self.credential = credential


    def __str__(self):
        return 'CushUser: {} : {}'.format(self.name, self.credential)


    def __repr__(self):
        repr = 'CushUser(name={}, credential={})'.format(\
            self.name, self.credential)
        return  repr


    def __getattr__(self, attr):
        """
        Description:
            allow CushUser credential attributes to be accessed directly from the user
            object. Delegates all unknown attribtues to be looked up the in self.cred
        """
        return getattr(self.credential, attr)



class UserConfigParser(NamespaceConfigParser2):
    def __init__(self, dictConfig=None, users=None, merge=False, prefix=None, nsroot=None):
        """
        Description:
            Contain the configuration for all of the users.
            (Generally this means a set of named credentials for each loaded SDK.)
        Input:
            prefix: a prefix for the generated namespace items
            --all the rest is TODO--
            dictConfig: a dictionary configuration
            users: additional users passed directly
            merge: boolean controlling merging of users
                True: merge using a ChainMap
                False: later users override earlier users

        Output:
            None. Directly modifies the Root namespace nodes directly via _add_child()
        Notes:
            the users kwarg is processed after the dictConfig, thus effectively overriding
            any users configured in the dictConfig that may have the same name
        """
        super().__init__(prefix=prefix, nsroot=nsroot)
        self.creds_mark = '__creds__'
        self.role_mark = '__role__'

    def _is_starting_user(self, mapping):
        log = LoggerAdapter(logger, {'name_ext' :'{}.check_starting_user'.format(\
            self.__class__.__name__)})
        log.debug("mapping.keys(): {}".format(mapping.keys()))

        booley = len(mapping.keys()) == 1 and self.creds_mark in mapping.keys()

        log.debug("returning: {}".format(booley))
        return booley


    def _is_starting_role(self, mapping):
        """
        Description:
            utility method to check if the current point in the mapping parsing is a
            role assumption section
        Input:
            mapping: the dict we are parsing
        Output:
            True / False
        """
        log = LoggerAdapter(logger, {
                'name_ext' :
                f'{self.__class__.__name__}._is_starting_role' })
        log.debug(f"mapping: {mapping}")
        log.debug(f"mapping.keys(): {mapping.keys()}")
        booley = len(mapping.keys()) == 1 and self.role_mark in mapping.keys()
        log.debug(f"returning {booley}")
        return  booley


    def parse_submap(self, mapping, cur_ns, prev_ns=None):
        log = LoggerAdapter(logger, {'name_ext' : 'UserNsConfigParser.parse_submap'})
        log.debug("Parsing User Configuration Submaps")
        #- check if this is a credential item or another namespace item
        if self._is_starting_user(mapping):
            try:
                name = cur_ns._nsid.split('.')[-1]
                log.debug("Creating AWS Credential for Cush Username: {}".format(\
                    name))
                credential = AwsCredential(**mapping[self.creds_mark])
            except TypeError:
                msg = 'Error creating AwsCredential.'
                log.error(f"{msg}: args: {mapping}")
            else:
                user = CushUser(name, credential)
                log.debug("Created CushUser object: {}".format(user))
                log.debug("Adding user to current namespace '{}'".format(cur_ns._nsid))
                prev_ns._set_item(user.name, user, iter=True)
        elif self._is_starting_role(mapping):
            try:
                name = cur_ns._nsid.split('.')[-1]
                log.debug(f"Creating AWS Assume Role Credential named: {name}")
                role = AwsRole(self.nsroot, name, **mapping[self.role_mark])
                log.debug(f"Created AwsRole object: {role}")
            except TypeError as e:
                msg = "Error creating AWS Role"
                log.exception(f'{msg}: args: {mapping[self.role_mark]}')
            else:
                log.debug(f"Adding role to current namespace '{cur_ns._nsid}'")
                prev_ns._set_item(role.name, role, iter=True)

        else:
            super().parse_submap(mapping, cur_ns, prev_ns=prev_ns)



