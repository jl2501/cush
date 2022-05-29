import boto3
from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner

class AwsSessionProvisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='.boto3.aws.session', priority=10):
        """
        priority: 10 to wait until after regions have been created
        """
        super().__init__(root_nsid=root_nsid, priority=priority)
        #- use region_name and _cush_credential_nsid for nsid extensions
        self.add_nsid_ext('region_name')
        #- this must be set by us as it does not exist yet
        self.add_nsid_ext('_cush_credential_nsid')



    def make_implementors(self, credentials='aws', regions='boto.aws.ec2.regions'):
        log = LoggerAdapter(logger, dict(name_ext='make_implementors'))
        log.info('provisioning boto3 session implementors')


        all_sessions = list()
        log.info(f"calling self.lookup_user({credentials})")
        creds = list(self.lookup_user(credentials))
        log.info(f"lookup_user returned these credentials: {creds}")

        log.info(f"calling self.lookup_implementor({regions})")
        region_imps = list(self.lookup_implementor(regions))
        log.info(f"lookup_implementor returned these region implementors: {region_imps}")

        #- create the implementors for each user credential
        for cred_x in creds:
            log.debug(f"using credential: {cred_x}")

            #- create implementors for each region
            for region_x in region_imps:
                session = boto3.session.Session(aws_access_key_id=cred_x.access_key_id,
                        aws_secret_access_key=cred_x.secret_access_key,
                        region_name = str(region_x))

                if session:
                    #- keep name of user credentials used to create
                    #- used to further namespace the implementors based on user
                    session._cush_credential_nsid = str(cred_x.nsid)

                    #- control sessions with both users and regions
                    region_fs = self.get_flipswitch_from_implementor(regions, region_x)
                    user_fs = self.get_flipswitch_from_user(credentials, cred_x)
                    session_fs = self.make_flipswitch(session)
                    self.link_flipswitches(region_fs, session_fs)
                    self.link_flipswitches(user_fs, session_fs)

                    all_sessions.append(session)

        return all_sessions
