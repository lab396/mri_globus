#!/usr/bin/env python

# This script will list the contents of a user-defined Globus Guest Collection,
# using Globus and persistent authentication using a refresh token. 
#
# This makes use of the Globus-hosted native app "MRI_2_RC_Test_App".
# 
# The first time this app is run, it will open a web browser for initial authentication,
# after which a token file will be saved in the $CWD. Tokens can be 
# recinded by deleting the file or going to 
# https://app.globus.org/settings/consents, referencing the consent, and
# then deleting it.
#
# Written by Lindsay Wells adapted from J. Nucciarone and Globus support
# January 23, 2025.
#
# Version 1.0
#
import os

import time

import argparse

import webbrowser

import globus_sdk
from globus_sdk import GroupsClient, NativeAppAuthClient, RefreshTokenAuthorizer
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from globus_sdk.scopes import TransferScopes

# Obtain command line args that contain the location and date info
# parser = argparse.ArgumentParser()
# parser.add_argument("DATA_LOCATION")
# parser.add_argument("TODAY")
# args = parser.parse_args()
 
# Set source and destination endpoint UUID
# Source is the Guest Collection "MRI_Converge_Guest_Collection"
# This guest collection corrsponds to directory /storage/long/ on converge.mri.psu.edu

source_collection_id = "095bd11b-e263-44dc-ad19-6dd4b463207e" 

# Destination is the Guest Collection "MRI_Data_Transfer_Guest_Collection"
# This guest collection corresponds to directory /storage/group/MCL/default/globus-share/

# dest_collection_id = "dbbff0bc-6329-45b1-9bfe-50624cc42ce6"

dest_collection_id = "eef905af-dc3e-4f55-8c87-7b804cfb654f"

# My client ID - "MRI_2_RC_Test_App" native app

CLIENT_ID = "0ba8e7a7-3f08-49bd-adde-61491161882c"

# Set the source and destination paths
source_path = '/lab396'
destination_path = '/'

auth_client = NativeAppAuthClient(CLIENT_ID)
my_file_adapter = SimpleJSONFileAdapter(
    os.path.expanduser("/root/globus_auth_scripts/my-globus-refresh-token.json")
)

if not my_file_adapter.file_exists():
    # requested_scopes specifies a list of scopes to request
    # instead of the defaults, only request access to the Transfer API

    auth_client.oauth2_start_flow(requested_scopes=TransferScopes.all, refresh_tokens=True)
    authorize_url = auth_client.oauth2_get_authorize_url()
     
    print(f"Native App Authorizaion URL:\n{authorize_url}\n")
    
    try:
        webbrowser.open(authorize_url, new=1)
    except:
        print(f"Please go to this URL and login:\n\n{authorize_url}\n")

    auth_code = input("Please enter the code here: ").strip()

    token_response = auth_client.oauth2_exchange_code_for_tokens(auth_code)

    # Store tokens for later
    my_file_adapter.store(token_response)

    # Use the current transfer tokens

    transfer_tokens = token_response.by_resource_server["transfer.api.globus.org"]
else:
    # otherwise, we already did this whole song-and-dance, so just
    # load the tokens from that file
    transfer_tokens = my_file_adapter.get_token_data("transfer.api.globus.org")

authorizer = globus_sdk.RefreshTokenAuthorizer(
    transfer_tokens["refresh_token"],
    auth_client,
    access_token=transfer_tokens["access_token"],
    expires_at=transfer_tokens["expires_at_seconds"],
    on_refresh=my_file_adapter.on_refresh,
)

# construct an AccessTokenAuthorizer and use it to construct the
# TransferClient

transfer_client = globus_sdk.TransferClient(authorizer=authorizer)

# create a Transfer task consisting of one or more items
task_data = globus_sdk.TransferData(
    transfer_client,source_endpoint=source_collection_id, destination_endpoint=dest_collection_id
)

# Create a transfer data object
transfer_data = globus_sdk.TransferData(
    transfer_client,
    source_collection_id,
    dest_collection_id,
    label="Transfer from /storage/long to /storage/group/MCL/default/globus-share",
    sync_level="checksum",  # Use "checksum" for data validation
)

# Add file paths to the transfer data object
transfer_data.add_item(source_path, destination_path)

task_data.add_filter_rule(name="*", method="include", type="dir")

# Start the transfer
print("Starting transfer...")
transfer_result = transfer_client.submit_transfer(transfer_data)

# Monitor the transfer status
transfer_id = transfer_result['task_id']
print(f"Transfer started with task ID: {transfer_id}")

while True:
    task = transfer_client.get_task(transfer_id)
    status = task['status']
    
    if status == 'SUCCEEDED':
        print(f"Transfer completed successfully.")
        break
    elif status == 'FAILED':
        print(f"Transfer failed. Check Globus dashboard for details.")
        break
    
    print(f"Transfer status: {status}. Waiting 5 seconds...")
    time.sleep(5)


# Set the source and destination transfers, and build filters to
# eliminate the deletion file. Transfer all zips in the working scratch dir
# and ignore the MANIFESTS directory, otherwise it'll be placed into
# the DATA directory.
#

# task_data.add_item(
#    f"./{args.DATA_LOCATION}/{args.TODAY}/",  # Source
#    f"./{args.DATA_LOCATION}/DATA/",  # Dest
#    recursive=True
#)


# Rules set following directions at 
# https://docs.globus.org/api/transfer/task_submit/#filter_rules


# task_data.add_filter_rule(name="*", method="include", type="dir")
# task_data.add_filter_rule(name="MANIFESTS", method="exclude", type="dir")
# task_data.add_filter_rule(name=f"eligible_for_deletion_{args.TODAY}.txt", method="exclude", type="file")
 

# Now all the MANIFESTS directory back and transfer it to its own location

# task_data.add_item(
#    f"./{args.DATA_LOCATION}/{args.TODAY}/MANIFESTS/",  # Source
#    f"./{args.DATA_LOCATION}/MANIFESTS/",  # Dest
#    recursive=True
#)

task_data.add_filter_rule(name="*.txt", method="include", type="file")


def do_submit(client):
    task_doc = client.submit_transfer(task_data)
    task_id = task_doc["task_id"]
    print(f"submitted transfer, task_id={task_id}")


try:
    do_submit(transfer_client)
except globus_sdk.TransferAPIError as err:
    if not err.info.consent_required:
        raise
    print(
        "Encountered a ConsentRequired error.\n"
        "You must login a second time to grant consents.\n\n"
    )
#
