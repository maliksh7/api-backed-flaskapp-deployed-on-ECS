from aws_cdk import (
    # Duration,
    Stack,
    # core as cdk,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    # aws_sqs as sqs,
)
from constructs import Construct

# import logging as logs
import aws_cdk as cdk


class Sprint6SaadECSStack(Stack):

    # def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    #     super().__init__(scope, construct_id, **kwargs)

    def __init__(self, scope: Construct, construct_id: str, repo = ecr.Repository,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.repo = repo 
        cdk.CfnOutput(self, "SaadrepoName", value=repo.repository_name)
        self.create_ecs_cluster()
        self.create_task_definition()
        self.create_fargate_service()
    
    ## Create ecs
    def create_ecs_cluster(self):
        
        '''
           
           Docs:          https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/Cluster.html
           Description:   This function will create a ECS cluster
           @param:        self(constructor)
           Returns:       creates a cluster
           
        '''
        
        # virtual private cloud 
        self.vpc = ec2.Vpc(self, "saad_ecs_vpc", max_azs=2)
        
        # ecs cluster object
        self.ecs_cluster = ecs.Cluster(self, 'saad-ecs_cluster', 
            cluster_name = "Saad_FargetCluster",
            # If true CloudWatch Container Insights will be enabled for the cluster. Default: - Container Insights will be disabled
            container_insights=True,
            # Whether to enable Fargate Capacity Providers. Default: false
            # asking farget to manage servers and 
            enable_fargate_capacity_providers = True,
            # A virtual private cloud (VPC) is a virtual network dedicated to your AWS account. 
            # It is logically isolated from other virtual networks in the AWS Cloud.
            vpc = self.vpc,
        )
        
    # Create Task defination
    def create_task_definition(self):
        
        '''
           
           Description:   In this function task definition is created, 
                          that will tell us what we need for our services to run, specifically 
                          In this case we just have one container & one image, but lets suppose 
                          we have 3 images for 3 different purposes, like one for loading images, 
                          second for loading products and third for database operations. So, task
                          will tell whole service and what needed to run those services.
                          
           @param:        self(constructor)
           Returns:       creates task definition
           
        '''
        
        # roles for ecs task
        self.ecstask_role = self.create_ecs_task_role()
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_logs/LogGroup.html
        # Define a CloudWatch Log Group.
        ecs_task_log = logs.LogGroup(self, "saad-ecs-task-log-group", 
        # Name of the log group. Default: Automatically generated
            #log_group_name = "ecs-task-log-group1",
            # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_logs/RetentionDays.html#aws_cdk.aws_logs.RetentionDays
            # How long the logs contents will be retained
            retention = logs.RetentionDays.FIVE_DAYS
        )
        
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/FargateTaskDefination.html
        # capacity need to run a container
        self.fargate_task_definition = ecs.FargateTaskDefinition(self, "Saad_FargetTaskDef",
            # the number of cpu units used by the task
            cpu=256,
            # The count (in MiB) of memory used by the task.
            memory_limit_mib=512,
            # The amount (in GiB) of ephemeral storage to be allocated to the task. the maximum supported value is 200 GiB
            ephemeral_storage_gib = 21,
            # task_role (Optional[Role]) - The name of the IAM Role that grants conatiners in the task permissions to call AWS APIs on your behalf
            # Default: - A task roleia automatically created for you.
            task_role=self.ecstask_role,
            # family (Optional[str]) - The name oa a family that this task defination is registered to. A family group multiple version
            # Default: - Automatically generated name
            family="saad_ecs_task_family",
            
        )
        
        task_environment = {
            "ENV1": "environment variable",
        }
        
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/FargateTaskDefination.html@aws_cdk.aws_ecs.FargateTaskDefinition
        # adding a conatiner to task definition
        self.fargate_task_definition.add_container("SaadtaskContainer", 
            # The name of the conatiner. Default: - id of node associated with ContainerDefinition.
            container_name="SaadtaskContainer",
            # The minimum number of CPU units to reserve for the container
            cpu=256,
            # The amount (in MiB) of memory to present the container. If you container attempts to exceed the allocated memory,
            memory_limit_mib=512,
            # The environment variable to pass to the conatiner. Default: - No environment variable.
            environment = task_environment,
            # True: if the container fails or stops for any reason, all other containers that are part of the task are stopped.
            # False: then its failure does not afect the rest of the containers in a task. All tasks must have at least one essential
            # Default is True
            essential=True,
            # the image used to start a container. The sting is passed directly to the Docker daemon.
            # Images in the Docker Hub registry are availableby default. 
            image=ecs.ContainerImage.from_ecr_repository(repository=self.repo),
            # The log config specification for the conatiner. Default: - Conatiner use the same logging driver that Docker
            # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/LogDrivers.html@aws_cdk.aws_ecs.LogDriver
            logging=ecs.LogDriver.aws_logs(stream_prefix='saad-ecs-task', log_group=ecs_task_log),
            # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/PoortMapping.html#aws_cdk.aws_ecs.PortMapping
            # Port mappings allow containers to access ports on the host container instance to send or receive traffic.
            # The port mappings to add to the container definition. Default: - No ports are mapped.
            port_mappings=[ecs.PortMapping(
                # The port number on the container that is bound to the user-specfied
                container_port=8801,
                # The port number on the container instance to reverse for your container.
                #host_port=8801,
                # The protocol used for the port mapping
                protocol=ecs.Protocol.TCP
                )
                
            ],
            )
        
    def create_ecs_task_role(self):
        
        '''
           
           Description:   This fun creates ecs task role to give permission for microservices.
           @param:        self(constructor)
           Returns:       return iam role
           
        '''
   
        sts_policy = iam.PolicyStatement(actions=['sts:AssumRole'], resources = ["*"])
        cw_policy = iam.PolicyStatement(actions=['logs:*'], resources = ["*"])
        task_role_policy_document = iam.PolicyDocument(statements= [sts_policy, cw_policy])
        
        return iam.Role(self, "saad-ecs-task-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description = "ECS task role for package forecast app",
            managed_policies = [iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")],
            inline_policies = [task_role_policy_document]
        )        
    
    def create_fargate_service(self):
        
        '''
           
           Docs:          https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs?FargateService.html
           Description:   This creates a service using the Fargate lauch type on an ECS cluster.
           @param:        self(constructor)
           Returns:       creates a fargate service
           
        '''
        
        service = ecs.FargateService(self, "SaadEcsService",
            service_name="SaadEcsService",
            cluster=self.ecs_cluster,
            task_definition=self.fargate_task_definition,
            desired_count=200,
            min_healthy_percent=10,
            max_healthy_percent=100,
        )
        
        # Define an App Load Balancer
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationLoadBalancer.html
        lb = elbv2.ApplicationLoadBalancer(self, "LB", 
            vpc=self.vpc,
            internet_facing=True
        )
        
        listener = lb.add_listener("SaadListener", port=80)
        
        service.register_load_balancer_targets(
            ecs.EcsTarget(
                container_name="SaadtaskContainer",
                container_port=8801,
                new_target_group_id="ECS",
                listener=ecs.ListenerConfig.application_listener(listener, 
                    protocol=elbv2.ApplicationProtocol.HTTP
                ))
            )
            
        cdk.CfnOutput(self, "SaadLoadBalancerDNS", value=lb.load_balancer_dns_name)
    