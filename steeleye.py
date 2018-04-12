from __future__ import print_function

import os
import logging
import json
import wget
import ssl
# import pandas as pd
import pyexcel
from boto3 import resource as boto_res


###############################################################################
#                             Required Defaults                               #
###############################################################################
DEFAULT_FILE_URL = "https://www.iso20022.org/sites/default/files/" \
                   "ISO10383_MIC/ISO10383_MIC.xls"
DEFAULT_XLS_SHEET_NAME = "MICs List by CC"
DEFAULT_S3_BUCKET = "S3-Bucket-Name"
DEFAULT_S3_REGION = "us-east-1"

KEYS = ['FILE_URL', 'XLS_SHEET_NAME', 'S3_BUCKET', 'S3_REGION']


###############################################################################
#                      Configuring logging framework                          #
###############################################################################
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


###############################################################################
#                          Lambda Entry Point                                 #
###############################################################################
def lambda_handler(event, context):
    try:
        # Setting all required parameters to proceed
        parameter_values = get_all_required_parameter_value(KEYS)

        downloaded_file = download_file(
            file_url=parameter_values.get('FILE_URL')
        )

        if downloaded_file is not None:
            output_list = extract_excel_sheet_content(
                downloaded_file_path=downloaded_file,
                xls_sheet_name=parameter_values.get('XLS_SHEET_NAME')
            )

            # Removing the file from local directory
            os.remove(downloaded_file)

            if len(output_list) != 0:
                upload_as_filename = create_json_filename(
                    downloaded_file_path=downloaded_file,
                    xls_sheet_name=parameter_values.get('XLS_SHEET_NAME')
                )

                # Uploading json data to S3
                if write_to_s3(
                    bucket=parameter_values.get('S3_BUCKET'),
                    region=parameter_values.get('S3_REGION'),
                    data=json.dumps(output_list),
                    s3_key=upload_as_filename
                ):
                    logger.info("{} file uploaded successfully to S3.".format(
                        upload_as_filename
                    ))
            else:
                logger.error("No data found to upload to AWS S3")
    except Exception as lh_e:
        logger.error("{}".format(lh_e))


###############################################################################
#                               Functions                                     #
###############################################################################

###############################################################################
# Set the required parameters either from ENV or from default values
# AWS Lambda environment variables expected to read:
# FILE_URL          url to download the expected xls file
# XLS_SHEET_NAME    Sheet name in the excel file to read
# S3_BUCKET         S3 Bucket name
# S3_REGION         S3 Bucket region
#
# return: value of the expected key either from ENV or from defaults
###############################################################################
def get_env_value(key, default_value):
    return str(os.environ[key]).strip() if os.getenv(key) else default_value


###############################################################################
# Iterate over a list of required keys and set their values either from env
# or from default values.
#
# return: dict of all keys with their values
###############################################################################
def get_all_required_parameter_value(keys):
    return dict(
        (key, get_env_value(key, eval('DEFAULT_'+key))) for key in keys
    )


###############################################################################
# Download excel file using wget module
#
# return: filename where URL is downloaded to
###############################################################################
def download_file(file_url):
    downloaded_file = None

    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        # Will not work in Lambda
        # downloaded_file = wget.download(file_url, out='/tmp')
        downloaded_file = wget.download(file_url,
                                        '/tmp/' + file_url.split("/")[-1])

        logger.info("{} file got downloaded.".format(downloaded_file))
    except IOError as io_e:
        logger.error("Error occurred during file download: {}".format(io_e))

    return downloaded_file


###############################################################################
# Create a file name for json file to upload to S3
#
# return: filename
###############################################################################
def create_json_filename(downloaded_file_path, xls_sheet_name):
    return downloaded_file_path.split("/")[2].split(".")[0] + \
           "-" + \
           xls_sheet_name.replace(" ", "_") + \
           ".json"


###############################################################################
# Read the sheet from the excel file and specified sheet and convert into a
# list of dictionary
#
# return: list with dicts, where each dict contains each row of the
# mentioned excel sheet.
###############################################################################
# def extract_excel_sheet_content(downloaded_file_path, xls_sheet_name):
#     output_list = []
#
#     try:
#         df = pd.read_excel(downloaded_file_path, sheet_name=xls_sheet_name)
#
#         if not df.empty:
#             for row in df.iterrows():
#                 output_list.append(row[1].to_dict())
#     except Exception as esc_e:
#         logger.error("Error occurred during extracting info from data-frame:"
#                      "{}".format(esc_e))
#
#     return output_list
def extract_excel_sheet_content(downloaded_file_path, xls_sheet_name):
    output_list = []
    col_headers = None

    try:
        sheet_content = pyexcel.get_sheet(
            file_name=downloaded_file_path,
            sheet_name=xls_sheet_name
        )

        for each_row in sheet_content.rows():
            if col_headers is None:
                col_headers = each_row
                continue

            output_list.append(dict(zip(col_headers, each_row)))
    except Exception as esc_e:
        logger.error("Error occurred during extracting data: {}".format(esc_e))

    return output_list


###############################################################################
# Upload the list of dicts(each row) as a json file to AWS S3 bucket
#
# return: True/False as per upload status
###############################################################################
def write_to_s3(bucket, region, data, s3_key):
    upload_succeed = False
    try:
        s3_resource = boto_res('s3', region_name=region)

        s3_resource.Bucket(bucket).put_object(Key=s3_key, Body=data)

        upload_succeed = True
    except Exception as wts_e:
        logger.error("Error occurred during upload data to AWS S3: "
                     "{}".format(wts_e))

    return upload_succeed
