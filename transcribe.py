#!/usr/local/bin/python3.7

import json
import boto3
import codecs
import logging

from botocore.exceptions import ClientError
import botocore.errorfactory


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Transcription Parameters
INPUT_BUCKET_NAME = 'turn-the-bus-video-transcription-input'
OUTPUT_BUCKET_NAME = 'turn-the-bus-video-transcription-output'
LANGUAGE_CODE = 'hi-IN'
FORCE_TRANSCRIBE = False
AWS_REGION = 'us-east-1'


s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')


def list_files_in_S3(bucket_name):
	try:
		response = s3_client.list_objects_v2(Bucket=bucket_name)
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


def upload_to_s3(bucket_name, file_name, content):
	assert bucket_name is not None
	assert file_name is not None
	assert content is not None

	s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=content.encode("utf-8"))
	logger.info("Successfully uploaded %s to %s " % (file_name, bucket_name))


def download_from_s3(bucket_name, file_name):
	assert bucket_name is not None
	assert file_name is not None

	response = s3_client.get_object(Bucket=bucket_name, Key=file_name)

	assert response is not None and response['Body'] is not None
	return response['Body']


def list_video_files():
	return list_files_in_S3(INPUT_BUCKET_NAME)


def list_transcript_files():
	return list_files_in_S3(OUTPUT_BUCKET_NAME)


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


## Subtitle functionality
def generate_srt(transcript):
	phrases = generate_phrases(transcript)
	srt_content = generate_srt_from_phrases(phrases)
	return srt_content


def generate_srt_file(transcript_file_name, transcript_file_streaming_body):
	assert transcript_file_streaming_body is not None
	assert transcript_file_name is not None

	logger.info("generating srt file for transcript file: %s " % transcript_file_name)
	srt_content = generate_srt(transcript_file_streaming_body)

	logger.info("Successfully generated srt content for %s. Uploading to S3" % transcript_file_name)
	upload_to_s3(OUTPUT_BUCKET_NAME, transcript_file_name.replace("json", "srt"), srt_content)


def generate_transcript_text(transcript_file_name, transcript_file_streaming_body):
	assert transcript_file_name is not None
	assert transcript_file_streaming_body is not None

	ts = json.load(transcript_file_streaming_body)

	if ts is None:
		logger.warning("could not parse json content for file: %s" % transcript_file_name)
		return

	transcript_list = ts['results']['transcripts']

	if transcript_list is None or len(transcript_list) == 0:
		logger.warning("no transcript list in json content for file: %s" % transcript_file_name)
		return

	transcript_content = transcript_list[0]['transcript']

	logger.info("Uploading transcript text content to S3 for file: %s" % transcript_file_name)
	upload_to_s3(OUTPUT_BUCKET_NAME, transcript_file_name.replace("json", "txt"), transcript_content)


## Phrase contains start_time, end_time and the max 10 word text
def generate_phrases(transcript):
	ts = json.load(transcript)
	items = ts['results']['items']

	phrase =  {}
	phrases = []
	nPhrase = True
	puncDelimiter = False
	x = 0

	for item in items:
        # if it is a new phrase, then get the start_time of the first item
		if nPhrase == True:
			if item["type"] == "pronunciation":
				phrase["start_time"] = get_time_code(float(item["start_time"]))
				nPhrase = False         
		else:    
            # We need to determine if this pronunciation or puncuation here
            # Punctuation doesn't contain timing information, so we'll want
            # to set the end_time to whatever the last word in the phrase is.
            # Since we are reading through each word sequentially, we'll set 
            # the end_time if it is a word
			if item["type"] == "pronunciation":
				phrase["end_time"] = get_time_code(float(item["end_time"]) )
			else:
				puncDelimiter = True

		# in either case, append the word to the phrase...
		transcript_word = item['alternatives'][0]["content"]

		if ("words" not in phrase):
			phrase["words"] = [ transcript_word ]
		else:
			phrase["words"].append(transcript_word)

		x += 1

		# now add the phrase to the phrases, generate a new phrase, etc.
		if x == 10 or puncDelimiter:
			#print c, phrase
			phrases.append(phrase)
			phrase = {}
			nPhrase = True
			puncDelimiter = False
			x = 0

	return phrases


def generate_srt_from_phrases(phrases):
	tokens = []
	c = 1

	for phrase in phrases:
		tokens.append(str(c))
		tokens.append(phrase["start_time"] + " --> " + phrase["end_time"])
		tokens.append(" ".join(phrase["words"]))
		tokens.append("\n")
		c += 1

	output = "\n".join(tokens)
	return output


def get_time_code(seconds):
# Format and return a string that contains the converted number of seconds into SRT format
	thund = int(seconds % 1 * 1000)
	tseconds = int(seconds)
	tsecs = ((float(tseconds) / 60) % 1) * 60
	tmins = int(tseconds / 60)
	return str( "%02d:%02d:%02d,%03d" % (00, tmins, int(tsecs), thund))


def transcribe_all():
	video_files = list_video_files()
	output = {}

	for video_file in video_files:
		logger.info("Starting Transcription of Video File: %s" % video_file)
		comment = transcribe_video_file(video_file)
		output[video_file] = comment

	return output


# For every transcript json in S3, create an srt file and a text file containing the transcript
def post_process_transcripts():
	transcript_files = list_transcript_files()

	assert transcript_files is not None

	for transcript_file in transcript_files:
		logger.info("Processing transcript file: %s" % transcript_file)

		assert transcript_file is not None

		if transcript_file.endswith("json"):
			logger.info("Downloading transcript file from S3: %s from bucket: %s" % (transcript_file, OUTPUT_BUCKET_NAME))
			transcript_file_streaming_body = download_from_s3(OUTPUT_BUCKET_NAME, transcript_file)

			logger.info("generating srt file for transcript file: %s " % transcript_file)
			generate_srt_file(transcript_file, transcript_file_streaming_body)

			transcript_file_streaming_body = download_from_s3(OUTPUT_BUCKET_NAME, transcript_file)
			logger.info("generating transcript text file: %s " % transcript_file)
			generate_transcript_text(transcript_file, transcript_file_streaming_body)


def transcribe_all_lambda_handler(event, context):
	output = transcribe_all()
	post_process_transcripts()
	return output

