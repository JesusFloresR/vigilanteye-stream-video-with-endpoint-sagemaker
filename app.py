import cv2
import time
import boto3
import json

# AWS SageMaker variables
sagemaker_runtime = boto3.client('runtime.sagemaker',
                             region_name='us-east-2')
endpoint_name = 'vigilanteye-endpoint-5-1729579541'  # Cambia esto al nombre de tu endpoint

url = "https://188a2110c0c0aa3d.mediapackage.us-east-2.amazonaws.com/out/v1/31fbe5644a0642028661e76796d79ed2/index.m3u8"
vcap = cv2.VideoCapture(url)
fps = vcap.get(cv2.CAP_PROP_FPS)
wt = 1 / fps

while True:
    start_time = time.time()
    ret, frame = vcap.read()

    if frame is not None:
        # Convert frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        # img_as_text = base64.b64encode(buffer).decode('utf-8')

        # # Create payload for SageMaker
        # payload = json.dumps({"image": img_as_text})

        # Invoke SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/x-image',
            Body=buffer.tobytes()
        )

        # Read the response from SageMaker
        result = json.loads(response['Body'].read().decode())
        print(result)
        break
        # Display the frame
        # cv2.imshow('frame', frame)

        # Press q to close the video windows before it ends if you want
        if cv2.waitKey(22) & 0xFF == ord('q'):
            break

        dt = time.time() - start_time
        if wt - dt > 0:
            time.sleep(wt - dt)
    else:
        print("Frame is None")
        break

# Release capture and close windows
vcap.release()
print("Video stop")
