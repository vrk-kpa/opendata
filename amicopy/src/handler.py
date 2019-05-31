import boto3

ec2client = boto3.client("ec2")
image_waiter = ec2client.get_waiter("image_available")
ec2resource = boto3.resource("ec2")


def copy_image(event, context):

    artifact_id = event["builds"][0]["artifact_id"]
    packer_custom_data = event["builds"][0]["custom_data"]
    image_id = artifact_id.split(":")[1]
    image_name = ec2resource.Image(image_id).name
    region = boto3.session.Session().region_name
    tags = [{'Key': k, 'Value': v} for k, v in packer_custom_data.items()]

    print("Wait for source image {} to become available".format(image_id))

    image_waiter.wait(ImageIds=[image_id])

    copied_image = ec2client.copy_image(
        SourceRegion=region,
        Name=image_name,
        SourceImageId=image_id)

    print("Source image available")

    print("Wait for target image {} to become available".format(copied_image["ImageId"]))

    image_waiter.wait(ImageIds=[copied_image["ImageId"]])

    print("Copied image available")

    print("Copy tags to image")
    ec2client.create_tags(
        Resources=[
            copied_image["ImageId"]
        ],
        Tags=tags
    )
    print("Tags copied")

    print("Image copied. Original image id: {}, Copied image id: {}. Image name: {}".format(
        image_id, copied_image["ImageId"], image_name))
    
    return copied_image["ImageId"]