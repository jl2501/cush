from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)
import boto.ec2.elb
from cush.implementorlib.implementorprovisioner import ImplementorProvisioner

class AwsRegionProvisioner(ImplementorProvisioner):
    def __init__(self, root_nsid='boto.aws.ec2.regions', priority=1):
        super().__init__(root_nsid=root_nsid, priority=priority)
        #- region string is the nsid extension
        self.add_nsid_ext(lambda x: x)

    def make_implementors(self):
        log = LoggerAdapter(logger, {'name_ext': 'provision_implementors'})
        log.info("provisioning EC2 regions")
        regions = [
          'ap-northeast-1',
          'ap-northeast-2',
          'ap-south-1',
          'ap-southeast-1',
          'ap-southeast-2',
          'ca-central-1',
          'eu-central-1',
          'eu-west-1',
          'eu-west-2',
          'eu-west-3',
          'sa-east-1',
          'us-east-1',
          'us-east-2',
          'us-west-1',
          'us-west-2'
        ]

        for region in regions:
            fs = self.make_flipswitch(region)

        return regions
