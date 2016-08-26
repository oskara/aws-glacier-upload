# aws-glacier-upload

## Introduction
aws-glacier-upload is a simple tool for uploading large archives to AWS Glacier. It implements the multipart upload flow needed for archives larger than 100 MB.

## Usage

    $ aws_glacier_upload.py -h
    usage: aws_glacier_upload.py [-h] [--account ID] [--profile PROFILE]
                             [--partsize SIZE] [--description DESCRIPTION]
                             [--verbose]
                             vaultname filename

    Uploads a file to AWS glacier.

    positional arguments:
      vaultname             The AWS glacier vault to upload to.
      filename              The file to upload.

    optional arguments:
      -h, --help            show this help message and exit
      --account ID          Override the default account id to use.
      --profile PROFILE     The AWS profile to use.
      --partsize SIZE       The size in megabytes of each part in multipart
                            upload. Must within the range 1 to 4096 and be a power
                            of 2. Default: 256
      --description DESCRIPTION
                            The description of the upload.
      --verbose             Override the default account id to use.

## Examples

    $ aws_glacier_upload.py backup /var/backup/backup-archive-20160825.tar.gz

## Links

[AWS Glacier](http://docs.aws.amazon.com/amazonglacier/latest/dev/introduction.html)
