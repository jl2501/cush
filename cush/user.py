import cush.defaults as defaults
from thewired import NamespaceConfigParser2, NamespaceNodeBase

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)


class AwsCredential(object):
    """
    Description:
        AWS API Credentials object; just the access key id and secret access key
        strings
    """
    def __init__(self, access_key_id, secret_access_key, session_token=None):
        """
        Input:
            access_key_id: AWS API Access Key ID
            secret_access_key: AWS API Secret Access Key for this Access Key ID
        """
        super().__init__()
        self.access_key_id =  access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token

    def __str__(self):
        return 'AwsCredential: ' + self.access_key_id




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
