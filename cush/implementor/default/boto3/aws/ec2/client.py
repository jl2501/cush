from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
import boto3
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner



class AwsEc2ClientProvisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='.boto3.aws.ec2.client'):
        super().__init__(root_nsid=root_nsid)
        self.add_nsid_ext('meta.region_name')
        self.add_nsid_ext('_cush_credential_nsid')

    def make_implementors(self, sessions='boto3.aws.session'):
        log = LoggerAdapter(logger, {'name_ext' : 'provision_implementors'})
        log.info('provisioning boto3 ec2 client implementor')
        ec2_clients = list()
        session_imps = self.lookup_implementor(sessions)
        for session_x in session_imps:
            ec2_c = session_x.client('ec2')
            if ec2_c:
                ec2_c._cush_credential_nsid = session_x._cush_credential_nsid
                ec2_clients.append(ec2_c)
                fs = self.make_flipswitch(ec2_c)
                session_fs = self.get_flipswitch_from_implementor(sessions, session_x)
                self.link_flipswitches(session_fs, fs)

        return ec2_clients
