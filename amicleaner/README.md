# ami cleaner

Simple Lambda for deleting old AMI images, runs on a schedule. Uses [aws-amicleaner](https://github.com/bonclay7/aws-amicleaner)


```bash
.
├── README.md                   <-- This instructions file
├── src                         <-- Source code for a lambda function
│   ├── handler.py
│   ├── cleaner.py              <-- Lambda function code
│   ├── requirements.txt        <-- Lambda function code
└── template.yaml               <-- SAM Template
```

## Requirements

* AWS CLI already configured with Administrator permission
* [AWS SAM installed](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* [Docker installed](https://www.docker.com/community-edition)
## Packaging and deployment

S3 bucket for storing Lambda code:

```bash
aws s3 mb s3://<NAME FOR BUCKET>
```

Build using a container:

```bash
sam build --use-container -s src
```

Package to S3:

```bash
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket <NAME OF BUCKET>
```

Create and deploy:

```bash
aws cloudformation deploy \
	--template-file packaged.yaml \
	--stack-name <NAME FOR STACK> \
	--capabilities CAPABILITY_IAM
```