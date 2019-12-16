This consists repositoty contains the functionality for transcribing TurnTheBus video files. All the code exists in ```transcribe.py``` file. The main function is ```transcribe_all```. It iterates through every video file in AWS S3 bucket ```INPUT_BUCKET_NAME``` and starts the transcription job by calling AWS Transcribe Service asynchronously. All the transcription output is stored in ```OUTPUT_BUCKET_NAME``` as individual json files. The code doesn't start a transcription job if the corresponding transcript file already exists in the output bucket. ```transcribe_all``` is wired to run as an AWS Lambda function.

### Example Output

```
{
  "zameendaar_video_small.mp4": "Transcript already exists in S3",
  "zameendaar_video_small_2.mp4": "Transcript already exists in S3",
  "zameendaar_video_small_3.mp4": "Transcript already exists in S3",
  "zameendaar_video_small_4.mp4": "Transcript already exists in S3"
}
```

### Logs

```
./transcribe.py
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:root:Starting Transcription of Video File: zameendaar_video_small.mp4
INFO:root:Transcript does not exist for video file: zameendaar_video_small.mp4. Checking the status of transcript job.
INFO:root:checking the status of Transcription Job: zameendaar_video_small_transcript_job
INFO:root:Transcript Job does not exist: zameendaar_video_small_transcript_job
INFO:root:Starting transcription job: zameendaar_video_small_transcript_job for input file: https://s3.us-east-1.amazonaws.com/turnthebus-video-transcription-input-ramnanib/zameendaar_video_small.mp4
INFO:root:Transcription job started: {u'TranscriptionJob': {u'TranscriptionJobName': u'zameendaar_video_small_transcript_job', u'LanguageCode': u'hi-IN', u'CreationTime': datetime.datetime(2019, 12, 15, 18, 10, 31, 711000, tzinfo=tzlocal()), u'TranscriptionJobStatus': u'IN_PROGRESS', u'Media': {u'MediaFileUri': u'https://s3.us-east-1.amazonaws.com/turnthebus-video-transcription-input-ramnanib/zameendaar_video_small.mp4'}}, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'd2ab24a0-27c9-4db4-92f4-164e0a243cf8', 'HTTPHeaders': {'date': 'Mon, 16 Dec 2019 02:10:31 GMT', 'x-amzn-requestid': 'd2ab24a0-27c9-4db4-92f4-164e0a243cf8', 'content-length': '343', 'content-type': 'application/x-amz-json-1.1', 'connection': 'keep-alive'}}}
INFO:root:Starting Transcription of Video File: zameendaar_video_small_2.mp4
INFO:root:Transcript already exists for video file: zameendaar_video_small_2.mp4
INFO:root:Starting Transcription of Video File: zameendaar_video_small_3.mp4
INFO:root:Transcript already exists for video file: zameendaar_video_small_3.mp4
INFO:root:Starting Transcription of Video File: zameendaar_video_small_4.mp4
INFO:root:Transcript does not exist for video file: zameendaar_video_small_4.mp4. Checking the status of transcript job.
INFO:root:checking the status of Transcription Job: zameendaar_video_small_4_transcript_job
INFO:root:Transcript Job does not exist: zameendaar_video_small_4_transcript_job
INFO:root:Starting transcription job: zameendaar_video_small_4_transcript_job for input file: https://s3.us-east-1.amazonaws.com/turnthebus-video-transcription-input-ramnanib/zameendaar_video_small_4.mp4
INFO:root:Transcription job started: {u'TranscriptionJob': {u'TranscriptionJobName': u'zameendaar_video_small_4_transcript_job', u'LanguageCode': u'hi-IN', u'CreationTime': datetime.datetime(2019, 12, 15, 18, 10, 33, 175000, tzinfo=tzlocal()), u'TranscriptionJobStatus': u'IN_PROGRESS', u'Media': {u'MediaFileUri': u'https://s3.us-east-1.amazonaws.com/turnthebus-video-transcription-input-ramnanib/zameendaar_video_small_4.mp4'}}, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'cf02f996-93da-48d5-87b2-4d5e6200d365', 'HTTPHeaders': {'date': 'Mon, 16 Dec 2019 02:10:33 GMT', 'x-amzn-requestid': 'cf02f996-93da-48d5-87b2-4d5e6200d365', 'content-length': '347', 'content-type': 'application/x-amz-json-1.1', 'connection': 'keep-alive'}}}
{u'zameendaar_video_small.mp4': 'Transcription Job Started', u'zameendaar_video_small_4.mp4': 'Transcription Job Started', u'zameendaar_video_small_2.mp4': 'Transcript already exists in S3', u'zameendaar_video_small_3.mp4': 'Transcript already exists in S3'}
```