import json
import boto3
import codecs
import logger

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

INPUT_BUCKET_NAME = 'turnthebus-video-transcription-input-ramnanib'
OUTPUT_BUCKET_NAME = 'turnthebus-video-transcription-output-ramnanib'
FORCE_TRANSCRIBE = False

s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')


def list_video_files():
	try:
		response = s3_client.list_objects_v2(Bucket=INPUT_BUCKET_NAME)
		logger.info("Response obtained from S3 when listing objects from bucket (%s), Response: %s" % (INPUT_BUCKET_NAME, response))
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


def get_transcript_from_s3(video_file):
	transcript_file_name = transcript_file_name_from_video_file_name(video_file_name)
	response = s3_client.get_object(Bucket=OUTPUT_BUCKET_NAME, Key=transcript_file_name)

	assert 'Body' in response, "'Body' is not a key in the s3 get_object response for video_file: %s" % video_file

	body = response['Body']
	output = body.read

	#for ln in codecs.getreader('utf-8')(body):
	#	output += ln

	return output
	

def transcribe_video_file(video_file, force_transcribe = False):
	# Step 1: Check if the transcription already exists
	if (not force_transcribe):
		# Check if transcription already exists
		try:
			return get_transcript_from_s3(video_file)
		except ClientError as e:
			error_code = e.response['Error']['Code']
		    
		    if error_code == '404':
        		logger.info("Transcript does not exist for video file: %s. Creating one " % video_file)
        	else
        		raise e        		
	# TODO: Step 2: Check if the transcription is on-going
	# TODO: Step 3: Start the transcription


def transcript_file_name_from_video_file_name(video_file_name):
	if (video_file_name is None):
		return None
	
	split_str = video_file_name.rplit('.', 1)

	if (len(split_str) == 0):
		return ''

	return split_str[0] + "_transcript.txt"


def transcript_job_name_from_video_file_name(video_file_name):
	if (video_file_name is None):
		return None
	
	split_str = video_file_name.rplit('.', 1)

	if (len(split_str) == 0):
		return ''

	return split_str[0] + "_transcript_job"


video_files = list_video_files()

for video_file in video_files:
	transcribe_video_file(video_file, FORCE_TRANSCRIBE)


   