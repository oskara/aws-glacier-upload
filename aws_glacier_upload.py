#!/usr/bin/python

import argparse
import hashlib
import os
import boto3
import sys

from botocore.exceptions import ClientError, EndpointConnectionError

parser = argparse.ArgumentParser(description='Uploads a file to AWS glacier.')
parser.add_argument('vaultname', type=str, help='The AWS glacier vault to upload to.')
parser.add_argument('filename', type=str, help='The file to upload.')
parser.add_argument('--account', type=str, metavar="ID", default='-', help='Override the default account id to use.')
parser.add_argument('--profile', type=str, help='The AWS profile to use.')
parser.add_argument('--partsize', type=int, metavar="SIZE", default=256,
                    help='The size in megabytes of each part in multipart upload. Must within the range 1 to 4096 and '
                         'be a power of 2. Default: 256')
parser.add_argument('--description', type=str, default="AWS Glacier upload.",
                    help='The description of the upload.')
parser.add_argument('--verbose', action='store_true', help='Override the default account id to use.')
args = parser.parse_args()

if args.partsize < 1 or args.partsize > 4096:
    print("Error! Part size not within range 1-4096: %r" % args.partsize)
    sys.exit(1)

if args.partsize & (args.partsize - 1) != 0:
    print("Error! Part size not power of 2: %r" % args.partsize)
    sys.exit(1)

vault_name = args.vaultname
file_name = args.filename
account_id = args.account
profile = args.profile
part_size = args.partsize * 1024 * 1024
description = args.description
verbose = args.verbose

file_size = os.stat(file_name).st_size
one_mb_size = 1024 * 1024

log_level_normal = 0
log_level_verbose = 1

log_flag_same_line = 1


def print_log(level, message, flags=0):
    global verbose

    if level == log_level_verbose and not verbose:
        return

    if flags & log_flag_same_line:
        sys.stdout.write("\r" + message + "       ")
        sys.stdout.flush()
    else:
        print(message)


def sha256_to_hex(sha256):
    return ''.join(x.encode('hex') for x in sha256)


def compute_sha256_tree_hash(parts_sha256):
    prev_lvl_hashes = parts_sha256

    while len(prev_lvl_hashes) > 1:
        prev_length = len(prev_lvl_hashes)
        length = prev_length / 2

        if prev_length % 2 != 0:
            length += 1

        curr_lvl_hashes = [''] * length
        j = 0
        for i in range(0, 2*length, 2):
            if prev_length - i > 1:
                sha256obj = hashlib.sha256()
                sha256obj.update(prev_lvl_hashes[i])
                sha256obj.update(prev_lvl_hashes[i+1])
                curr_lvl_hashes[j] = sha256obj.digest()
            else:
                curr_lvl_hashes[j] = prev_lvl_hashes[i]
            j += 1

        prev_lvl_hashes = curr_lvl_hashes

    return prev_lvl_hashes[0]


def do_multipart_upload(client, upload_id, filename):
    global part_size, file_size, vault_name

    offset = 0
    prev_offset = 0
    part_sha256 = []
    full_sha256 = []
    part_buffer = ""

    f = open(filename, 'rb')
    try:
        while True:
            raw = f.read(one_mb_size)
            if raw == '':
                break
            part_buffer += raw

            sha256obj = hashlib.sha256()
            sha256obj.update(raw)

            sha256 = sha256obj.digest()
            part_sha256.append(sha256)
            full_sha256.append(sha256)

            offset += len(raw)

            prev_percent = (100 * (prev_offset + 1) / file_size)
            percent = (100 * (offset + 1) / file_size)
            if percent != prev_percent:
                print_log(log_level_normal, str(percent) + " %", log_flag_same_line)
                if percent == 100:
                    print_log(log_level_normal, "")

            if (offset % part_size == 0) or (offset == file_size):
                start_offset = prev_offset
                stop_offset = prev_offset + len(part_buffer) - 1

                sha256 = sha256_to_hex(compute_sha256_tree_hash(part_sha256))
                try:
                    response = client.upload_multipart_part(
                        vaultName=vault_name,
                        uploadId=upload_id,
                        checksum=sha256,
                        range="bytes " + str(start_offset) + "-" + str(stop_offset) + "/*",
                        body=part_buffer)
                except (EndpointConnectionError, ClientError) as e:
                    print_log(log_level_normal, e)
                    sys.exit(1)

                print_log(log_level_verbose, "part length = " + str(len(part_buffer)))
                print_log(log_level_verbose, str(start_offset) + " - " + str(stop_offset) + " / " + str(file_size))
                print_log(log_level_verbose, "tree hash for part: " + sha256)
                print_log(log_level_verbose, response)

                prev_offset += len(part_buffer)
                part_sha256 = []
                part_buffer = ""
    finally:
        f.close()

    return sha256_to_hex(compute_sha256_tree_hash(full_sha256))

if profile:
    session = boto3.Session(profile_name=profile)
else:
    session = boto3.Session()

client = session.client('glacier')
try:
    response = client.initiate_multipart_upload(
        vaultName=vault_name,
        archiveDescription=description,
        partSize=str(part_size))
except (EndpointConnectionError, ClientError) as e:
    print_log(log_level_normal, e)
    sys.exit(1)

upload_id = response['uploadId']

print_log(log_level_normal, "starting upload of " + file_name + " to vault " + vault_name)
print_log(log_level_verbose, "upload id = " + upload_id)
tree_hash = do_multipart_upload(client, upload_id, file_name)

print_log(log_level_verbose, "full sha256 = " + tree_hash)
try:
    response = client.complete_multipart_upload(
        accountId=account_id,
        vaultName=vault_name,
        uploadId=upload_id,
        archiveSize=str(file_size),
        checksum=tree_hash)
except (EndpointConnectionError, ClientError) as e:
    print_log(log_level_normal, e)
    sys.exit(1)

print_log(log_level_verbose, response)
print_log(log_level_normal, "finished.")
