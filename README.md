# aws-glacier-upload

## Introduction
aws-glacier-upload is a simple tool for uploading large archives to AWS Glacier. It implements the multipart upload flow needed for archives larger than 100 MB.

## Examples

$ aws_glacier_upload.py backup /var/backup/backup-archive-20160825.tar.gz

## Links

[AWS Glacier](http://docs.aws.amazon.com/amazonglacier/latest/dev/introduction.html)
