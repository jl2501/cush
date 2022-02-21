from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
import boto.ec2.elb
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner


class AwsBotoElbProvisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='.boto.aws.ec2.elb.connections'):
        super().__init__(root_nsid=root_nsid)
        self.add_nsid_ext('region.name')
        self.add_nsid_ext('_cush_credential_nsid')

    def make_implementors(self, regions='boto.aws.ec2.regions', users='aws'):
        log = LoggerAdapter(logger, {'name_ext': 'provision_implementors'})
        log.info('provisioning boto elb implementor')
        elb_connections = list()
        user_objs = self.lookup_user(users)
        region_imps = self.lookup_implementor(regions)
        for cred_x in user_objs:
            for region_x in region_imps:
                elb_c = boto.ec2.elb.connect_to_region(\
                    aws_access_key_id=cred_x.access_key_id,\
                    aws_secret_access_key=cred_x.secret_access_key,\
                    region_name=str(region_x))

                if elb_c:
                    elb_c._cush_credential_nsid = str(cred_x.nsid)
                    elb_connections.append(elb_c)
                    fs = self.make_flipswitch(elb_c)

                    region_fs = self.get_flipswitch_from_implementor(regions,region_x)
                    self.link_flipswitches(region_fs, fs)
                    #- TODO: add user parent FS

        return elb_connections
