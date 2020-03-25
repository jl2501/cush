import boto3
from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner



class AwsEc2ResourceProvisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='boto3.aws.ec2.resource'):
        """
        Create the boto3 aws ec2 resource implementors
        """
        super().__init__(root_nsid=root_nsid)
        self.add_nsid_ext('meta.client.meta.region_name')
        self.add_nsid_ext('_cush_credential_nsid')


    def make_implementors(self, sessions='boto3.aws.session'):
        log = LoggerAdapter(logger, {'name_ext' : 'AwsEc2ResourceProvisioner'})
        log.info('provisioning boto3 ec2 resource implementor')

        ec2_resources = list()
        for session_x in self.lookup_implementor(sessions):
            ec2_r = session_x.resource('ec2')
            if ec2_r:
                ec2_r._cush_credential_nsid = session_x._cush_credential_nsid
                ec2_resources.append(ec2_r)

                fs = self.make_flipswitch(ec2_r)
                session_fs = self.get_flipswitch_from_implementor(sessions, session_x)
                self.link_flipswitches(session_fs, fs)

        return ec2_resources
