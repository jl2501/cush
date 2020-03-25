from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
import boto3
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner


class AwsS3ResourceProvisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='boto3.aws.s3.resource',\
        key='meta.client.meta.region_name'):

        nsid_exts = list()
        nsid_exts.append(lambda x: x.meta.client.meta.region_name)
        nsid_exts.append(lambda x: x._cush_credential_nsid)
        super().__init__(root_nsid=root_nsid, nsid_exts=nsid_exts)

    def make_implementors(self, sessions='boto3.aws.session'):
        log = LoggerAdapter(logger, {'name_ext' : 'provision_implementors'})
        log.info('provisioning boto3 s3 resource implementor')
        s3_resources = list()
        session_imps = self.lookup_implementor(sessions)
        for session_x in session_imps:
            s3_r = session_x.resource('s3')
            if s3_r:
                s3_r._cush_credential_nsid = session_x._cush_credential_nsid
                s3_resources.append(s3_r)
                fs = self.make_flipswitch(s3_r)
                session_fs = self.get_flipswitch_from_implementor(sessions, session_x)
                self.link_flipswitches(session_fs, fs)

        return s3_resources
