#!/usr/bin/env python


# This script will list the contents of a user-defined Globus Guest Collection,
# using Globus and persistent authentication using a refresh token. 
#
# This makes use of the Globus-hosted native app "My Data Flow Application".
# 
# The first time this app is run, it will open a web browser for initial authentication,
# after which a token file will be saved in the $CWD. Tokens can be 
# recinded by deleting the file or going to 
# https://app.globus.org/settings/consents, referencing the consent, and
# then deleting it.
#
# Written by J. Nucciarone with assistance from Globus support
# April 29, 2024.
#
#  Version 1.0
#


import os

import webbrowser

 

import globus_sdk
from globus_sdk import GroupsClient, NativeAppAuthClient, RefreshTokenAuthorizer
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from globus_sdk.scopes import TransferScopes

 

Set source and destination endpoint UUID
# Source is the Guest Collection "nucci-share", which is the directory

# /storage/group/RISE/nucci/globus-share

source_collection_id = "606bef12-cf0b-4c90-9432-13039595d2b3"

 

# CLIENT_ID is the UUID of the registered app we will use for the authentication flow.
# For this example, this is the app "My Data Flow Application", created in the earlier section.
# This is part of the project "My Test Globus Project"

CLIENT_ID = "c3554afe-be59-4196-a9a0-3f5abc29f021"


# The refresh token will be saved in a file named "my-globus-refresh-token.json"
# that will be written to the current directory.


auth_client = NativeAppAuthClient(CLIENT_ID)
my_file_adapter = SimpleJSONFileAdapter(
    os.path.expanduser("./my-globus-refresh-token.json")
)


if not my_file_adapter.file_exists():
    # requested_scopes specifies a list of scopes to request
    # instead of the defaults, only request access to the Transfer API
    auth_client.oauth2_start_flow(requested_scopes=TransferScopes.all, refresh_tokens=True)
    authorize_url = auth_client.oauth2_get_authorize_url()

    print(f"Native App Authorizaion URL:\n{authorize_url}\n")

    # If a web browser is available, we'll open a web page for the authorization request, otherwise we 
    # will request the user manually enter the URL in another web browser.


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
# TransferClient operation


transfer_client = globus_sdk.TransferClient(authorizer=authorizer)


# Print out a directory listing. Refer to the Globus CLI documentation for details on the operation_ls command


try:
    for entry in transfer_client.operation_ls(source_collection_id,path="~/", orderby=["type", "name"]):
        print(entry["type"], "\t", entry["name"], entry["size"], entry["permissions"], entry["user"], entry["group"], entry["last_modified"])
except:
    print("Error encountered\n")
