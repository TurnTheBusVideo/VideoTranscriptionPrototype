#!/usr/bin/python

import json
import boto3
import codecs
import logging

from botocore.exceptions import ClientError
import botocore.errorfactory

#logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Transcription Parameters
INPUT_BUCKET_NAME = 'turnthebus-video-transcription-input-ramnanib'
OUTPUT_BUCKET_NAME = 'turnthebus-video-transcription-output-ramnanib'
LANGUAGE_CODE = 'hi-IN'
FORCE_TRANSCRIBE = False
AWS_REGION = 'us-east-1'

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')


def list_video_files():
	try:
		response = s3_client.list_objects_v2(Bucket=INPUT_BUCKET_NAME)
		assert response is not None
		output = []
		
		if 'Contents' not in response:
			return output
		
		video_files = response['Contents']

		for video_file in video_files:
			assert 'Key' in video_file, "'Key' is not part of video_file obtained from S3 list_objects_v2"
			output.append(video_file['Key'])

		return output
	except:
		logger.exception("Failed to list video files from bucket: " + INPUT_BUCKET_NAME)
		raise


def transcript_exists_in_s3(video_file):
	try:
		transcript_file_name = transcript_file_name_from_video_file_name(video_file)
		response = s3_client.get_object(Bucket=OUTPUT_BUCKET_NAME, Key=transcript_file_name)

		return (response is not None) and ('Body' in response) and (response['Body'] is not None)

	except ClientError as e:
		if e.response['Error']['Code'] == 'NoSuchKey':
			return False
		else:
			raise e


def should_start_transcript_job(video_file):
	try:
		transcription_job_name = transcript_job_name_from_video_file_name(video_file)

		logger.info("checking the status of Transcription Job: %s" % transcription_job_name)
		response = transcribe_client.get_transcription_job(TranscriptionJobName=transcription_job_name)
		
		assert response is not None
		assert 'TranscriptionJob' in response

		response_job = response['TranscriptionJob']
		assert 'TranscriptionJobStatus' in response_job

		
		status = response_job['TranscriptionJobStatus']

		if(status == 'IN_PROGRESS'):
			comment = "Transcription job: %s, is already IN_PROGRESS." % transcription_job_name
			logger.info(comment)
			return False, comment

		if(status == 'COMPLETED'):
			assert 'Transcript' in response_job
			comment = "Transcription job: %s, has COMPLETED. Transcript is located here: %s" % (transcription_job_name, response_job['Transcript'])
			logger.info(comment)
			return False, comment

		if (status == 'FAILED'):
			assert 'FailureReason' in response_job
			comment = "Transcription job: %s has FAILED. Failure reason: %s. We'll try again" % (transcription_job_name, response_job['FailureReason'])
			logger.info(comment)
			return True, comment

		comment = "Transcription job in unknown status: %s" % status
		return True, comment
	except ClientError as err:
		if (err.response['Error']['Code'] == 'BadRequestException'):
			comment = "Transcript Job does not exist: %s" % transcription_job_name
			logger.info(comment)
			return True, comment
		else:
			raise err


def transcribe_video_file(video_file, force_transcribe = False):
	# Step 1: Check if the transcription already exists
	if (not force_transcribe):
		transcript_exists = transcript_exists_in_s3(video_file)

		if(transcript_exists):
			logger.info("Transcript already exists for video file: %s" % video_file)
			return "Transcript already exists in S3"

	logger.info("Transcript does not exist for video file: %s. Checking the status of transcript job." % (video_file))
	should_start_transcription, comment = should_start_transcript_job(video_file)

	if (should_start_transcription):
		transcription_job_name = transcript_job_name_from_video_file_name(video_file)

		# Step 3: Start the transcription
		input_uri = "https://s3." + AWS_REGION + ".amazonaws.com/" + INPUT_BUCKET_NAME + "/" + video_file
		logger.info("Starting transcription job: %s for input file: %s" % (transcription_job_name, input_uri))

		response = transcribe_client.start_transcription_job(TranscriptionJobName=transcription_job_name, LanguageCode=LANGUAGE_CODE, 
			OutputBucketName=OUTPUT_BUCKET_NAME, Media={ 'MediaFileUri' : input_uri })
		logger.info("Transcription job started: %s" % response)
		return "Transcription Job Started"

	return comment


def transcript_job_name_from_video_file_name(video_file_name):
	if (video_file_name is None):
		return None
	
	split_str = video_file_name.rsplit('.', 1)

	if (len(split_str) == 0):
		return ''

	return split_str[0] + "_transcript_job"


def transcript_file_name_from_video_file_name(video_file_name):
	transcript_job_name = transcript_job_name_from_video_file_name(video_file_name)

	if (transcript_job_name is None):
		return None

	return transcript_job_name + ".json"


def transcribe_all():
	video_files = list_video_files()
	output = {}

	for video_file in video_files:
		logger.info("Starting Transcription of Video File: %s" % video_file)
		comment = transcribe_video_file(video_file)
		output[video_file] = comment

	return output


def handler_name(event, context):
	return transcribe_all()

