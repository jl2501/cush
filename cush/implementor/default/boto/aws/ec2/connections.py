from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
import boto.ec2
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner


class AwsBotoEc2Provisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='boto.aws.ec2.connections'):
        super().__init__(root_nsid=root_nsid)
        self.add_nsid_ext('region.name')
        self.add_nsid_ext('_cush_credential_nsid')

    def make_implementors(self, regions='boto.aws.ec2.regions', users='aws'):
        log = LoggerAdapter(logger, {'name_ext': 'provision_implementors'})
        log.info('provisioning boto ec2 connections implementor')
        ec2_connections = list()
        creds = self.lookup_user(users, nsids=True)
        region_imps = self.lookup_implementor(regions)
        for cred_nsid, cred_x in creds:
            for region_x in region_imps:
                log.debug('provisioning boto.aws.ec2.connections.{}'.format(region_x))
                ec2_c = boto.ec2.connect_to_region(\
                    aws_access_key_id=cred_x.access_key_id,\
                    aws_secret_access_key=cred_x.secret_access_key,\
                    region_name=str(region_x))

                if ec2_c:
                    ec2_c._cush_credential_nsid = cred_nsid
                    ec2_connections.append(ec2_c)
                    fs = self.make_flipswitch(ec2_c)

                    region_fs = self.get_flipswitch_from_implementor(regions, region_x)
                    self.link_flipswitches(region_fs, fs)
        return ec2_connections
