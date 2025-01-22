#!/usr/bin/env python

# This helper script will transfer the zip data and manifest files
# from the CQI working scratch directory to the appropriate archive
# directoryusing Globus and persistent authentication using
# a Globus refresh token. 
#
# This makes use of the Globus hosted native app "Archive_Tranfer".
# 
# Upon initial run it will open a web browser for initial authentication,
# after which a token file will be saved in the $CWD. Tokens can be 
# recinded by deleting the file or going to 
# https://app.globus.org/settings/consents, referencing the consent, and
# then deleting it.
#
# It requires two command line arguesments to function:
#    The $LOCATION variable, that specifies which CQI location src and dest
#    The $today variable, that specifies the date of the archive run and
#      location directory 
#
# Written by J. Nucciarone with assistance from Globus support
# April 29, 2024.
#
#  Version 1.0
#

import os

import argparse
import webbrowser

import globus_sdk
from globus_sdk import GroupsClient, NativeAppAuthClient, RefreshTokenAuthorizer
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from globus_sdk.scopes import TransferScopes

# Obtain command line args that contain the location and date info
parser = argparse.ArgumentParser()
parser.add_argument("DATA_LOCATION")
parser.add_argument("TODAY")
args = parser.parse_args()

# Set source and destination endpoint UUID
# Source is the Guest Collection "CQI Transfer Directory"
source_collection_id = "a7b0d0fe-f0ef-4186-a96b-fc89ee61679a" 
# Destination is the Guest Collection "CQI Archive Transfer"
dest_collection_id = "e3a52e0a-b824-4d4b-9b04-1dad86e54c07"

# My client ID - "Archive Transfer" native app
CLIENT_ID = "a619acea-bc58-40c7-ad6a-fd422c75bfd0"

auth_client = NativeAppAuthClient(CLIENT_ID)
my_file_adapter = SimpleJSONFileAdapter(
    os.path.expanduser("~/svc-acct-globus-groups-tokens.json")
)

if not my_file_adapter.file_exists():
    # requested_scopes specifies a list of scopes to request
    # instead of the defaults, only request access to the Transfer API
    auth_client.oauth2_start_flow(requested_scopes=TransferScopes.all, refresh_tokens=True)
    authorize_url = auth_client.oauth2_get_authorize_url()
    #print(f"Please go to this URL and login:\n\n{authorize_url}\n")
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


# Set the source and destination transfers, and build filters to
# eliminate the deletion file. Transfer all zips in the working scratch dir
# and ignore the MANIFESTS directory, otherwise it'll be placed into
# the DATA directory.
#

task_data.add_item(
    f"./{args.DATA_LOCATION}/{args.TODAY}/",  # Source
    f"./{args.DATA_LOCATION}/DATA/",  # Dest
    recursive=True
)

# Rules set following directions at 
# https://docs.globus.org/api/transfer/task_submit/#filter_rules

task_data.add_filter_rule(name="*.zip", method="include", type="file")
task_data.add_filter_rule(name="MANIFESTS", method="exclude", type="dir")
task_data.add_filter_rule(name=f"eligible_for_deletion_{args.TODAY}.txt", method="exclude", type="file")
#task_data.add_filter_rule(name="*", method="exclude", type="file")

# Now all the MANIFESTS directory back and transfer it to its own location

task_data.add_item(
    f"./{args.DATA_LOCATION}/{args.TODAY}/MANIFESTS/",  # Source
    f"./{args.DATA_LOCATION}/MANIFESTS/",  # Dest
    recursive=True
)

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
# Everything below here is old code from an example I could
# not get to work. Leaving it here in case I get inspired to 
# rewrite the function to manage the consents.

#    transfer_client = login_and_get_transfer_client(
#        scopes=err.info.consent_required.required_scopes
#    )
#    do_submit(transfer_client)

