import unittest
import steeleye
import os
import pyexcel
import json
import warnings


class SteelEyeTest(unittest.TestCase):
    def setUp(self):
        self.DEFAULT_FILE_URL = "https://demo.com/demofile.xls"
        self.DEFAULT_XLS_SHEET_NAME = "Default Tab"
        self.DEFAULT_S3_BUCKET = "s3-test-bucket"
        self.DEFAULT_S3_REGION = "us-east-2"
        self.KEYS = ['FILE_URL', 'XLS_SHEET_NAME', 'S3_BUCKET', 'S3_REGION']

        # To ignore
        # ResourceWarning: unclosed <ssl.SSLSocket fd=7 after s3 upload due
        # to issue in boto3
        # warnings.simplefilter("ignore", ResourceWarning)

    ###########################################################################
    #                   Unit Tests of Function: get_env_value                 #
    ###########################################################################
    def test_get_env_value_from_default(self):
        self.assertEqual(steeleye.get_env_value(
            key='DEFAULT_FILE_URL', default_value=self.DEFAULT_FILE_URL
        ), self.DEFAULT_FILE_URL)

    def test_get_env_value_from_env(self):
        test_tab_name = 'Test Tab From ENV'
        os.environ['DEFAULT_XLS_SHEET_NAME'] = test_tab_name

        self.assertEqual(steeleye.get_env_value(
            key='DEFAULT_XLS_SHEET_NAME',
            default_value=self.DEFAULT_XLS_SHEET_NAME
        ), test_tab_name)

    ###########################################################################
    #        Unit Tests of Function: get_all_required_parameter_value         #
    # ###########################################################################
    def test_get_all_required_parameter_value_with_default(self):
        if os.getenv('FILE_URL'):
            del os.environ['FILE_URL']
        if os.getenv('XLS_SHEET_NAME'):
            del os.environ['XLS_SHEET_NAME']
        if os.getenv('S3_BUCKET'):
            del os.environ['S3_BUCKET']
        if os.getenv('S3_REGION'):
            del os.environ['S3_REGION']

        parameters = steeleye.get_all_required_parameter_value(self.KEYS)

        self.assertEqual(parameters.get('FILE_URL'),
                         steeleye.DEFAULT_FILE_URL)
        self.assertEqual(parameters.get('XLS_SHEET_NAME'),
                         steeleye.DEFAULT_XLS_SHEET_NAME)
        self.assertEqual(parameters.get('S3_BUCKET'),
                         steeleye.DEFAULT_S3_BUCKET)
        self.assertEqual(parameters.get('S3_REGION'),
                         steeleye.DEFAULT_S3_REGION)

    def test_get_all_required_parameter_value_from_env(self):
        os.environ['FILE_URL'] = self.DEFAULT_FILE_URL
        os.environ['XLS_SHEET_NAME'] = self.DEFAULT_XLS_SHEET_NAME
        os.environ['S3_BUCKET'] = self.DEFAULT_S3_BUCKET
        os.environ['S3_REGION'] = self.DEFAULT_S3_REGION

        parameters = steeleye.get_all_required_parameter_value(self.KEYS)

        self.assertEqual(parameters.get('FILE_URL'),
                         self.DEFAULT_FILE_URL)
        self.assertEqual(parameters.get('XLS_SHEET_NAME'),
                         self.DEFAULT_XLS_SHEET_NAME)
        self.assertEqual(parameters.get('S3_BUCKET'),
                         self.DEFAULT_S3_BUCKET)
        self.assertEqual(parameters.get('S3_REGION'),
                         self.DEFAULT_S3_REGION)

    ###########################################################################
    #                   Unit Tests of Function: download_file                 #
    ###########################################################################
    def test_download_file_with_wrong_url(self):
        file_url = "https://www.iso20022.org/sites/default/files/" \
                   "ISO10383_MIC/ISO10383_MIC.xls.wrong"

        downloaded_file = steeleye.download_file(file_url=file_url)
        self.assertIsNone(downloaded_file)

    def test_download_file_with_correct_url(self):
        file_url = "https://www.iso20022.org/sites/default/files/" \
                   "ISO10383_MIC/ISO10383_MIC.xls"

        downloaded_file = steeleye.download_file(file_url=file_url)
        self.assertIsNotNone(downloaded_file)
        os.remove(downloaded_file)

    def test_download_file_name(self):
        file_url = "https://www.iso20022.org/sites/default/files/" \
                   "ISO10383_MIC/ISO10383_MIC.xls"

        downloaded_file = steeleye.download_file(file_url=file_url)
        self.assertEqual(downloaded_file, "/tmp/ISO10383_MIC.xls")
        os.remove(downloaded_file)

    ###########################################################################
    #              Unit Tests of Function: create_json_filename               #
    ###########################################################################
    def test_create_json_filename_1(self):
        self.assertEqual(
            steeleye.create_json_filename(
                downloaded_file_path="/tmp/ISO10383_MIC.xls",
                xls_sheet_name="MICs List by CC"
            ),
            "ISO10383_MIC-MICs_List_by_CC.json"
        )

    def test_create_json_filename_2(self):
        self.assertEqual(
            steeleye.create_json_filename(
                downloaded_file_path="/tmp/ISO10383_MIC.xls",
                xls_sheet_name="TestTab"
            ),
            "ISO10383_MIC-TestTab.json"
        )

    ###########################################################################
    #          Unit Tests of Function: extract_excel_sheet_content            #
    ###########################################################################
    def test_extract_excel_sheet_rows(self):
        sheet_content_by_pyexcel = pyexcel.get_sheet(
            file_name="tests/ISO10383_MIC.xls",
            sheet_name=steeleye.DEFAULT_XLS_SHEET_NAME
        )

        sheet_content_list = steeleye.extract_excel_sheet_content(
            downloaded_file_path="tests/ISO10383_MIC.xls",
            xls_sheet_name=steeleye.DEFAULT_XLS_SHEET_NAME
        )

        # As number of rows content the header row too
        self.assertEqual(len(sheet_content_list),
                         sheet_content_by_pyexcel.number_of_rows()-1)

    def test_extract_excel_sheet_wrong_sheet(self):
        sheet_content_list = steeleye.extract_excel_sheet_content(
            downloaded_file_path="tests/ISO10383_MIC.xls",
            xls_sheet_name="TestTab"
        )

        self.assertEqual(len(sheet_content_list), 0)

    ###########################################################################
    #                   Unit Tests of Function: write_to_s3                   #
    # ###########################################################################
    def test_write_to_s3_error(self):
        data_to_upload = [
            {'R1C1': 'Val11', 'R1C2': 'Val12'},
            {'R2C1': 'Val21', 'R2C2': 'Val22'}
        ]

        self.assertFalse(steeleye.write_to_s3(
            bucket=self.DEFAULT_S3_BUCKET,
            region=self.DEFAULT_S3_REGION,
            data=json.dumps(data_to_upload),
            s3_key="test_error_upload.json"
        ))

    def test_write_to_s3_success(self):
        data_to_upload = [
            {'R1C1': 'Val11', 'R1C2': 'Val12'},
            {'R2C1': 'Val21', 'R2C2': 'Val22'}
        ]

        self.assertTrue(steeleye.write_to_s3(
            bucket=steeleye.DEFAULT_S3_BUCKET,
            region=steeleye.DEFAULT_S3_REGION,
            data=json.dumps(data_to_upload),
            s3_key="test_success_upload.json"
        ))


if __name__ == '__main__':
    unittest.main()
