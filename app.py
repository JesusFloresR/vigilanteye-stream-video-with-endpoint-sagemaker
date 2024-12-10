import cv2
import time
import boto3
import json
from collections import deque
import os
from datetime import datetime

# AWS SageMaker variables
number_intrusion_detections = 0
sequenceIntruder = False
intruder_detected = False
start_time_record = 0
init_record = False
init_record_aux = False
i=1

DURATION_BEFORE_EVENT = 10  # Segundos a grabar antes del evento
FRAME_RATE = 30  # Tasa de cuadros por segundo (fps)

frame_buffer = deque(maxlen=DURATION_BEFORE_EVENT * FRAME_RATE)

sagemaker_runtime = boto3.client('runtime.sagemaker',
                                 region_name='us-east-2')
s3_client = boto3.client('s3',
                             region_name='us-east-2')
current_datetime = None

endpoint_name = os.getenv('ENDPOINT_NAME')
url = os.getenv('PLAYBACK_URL')
# endpoint_name = 'vigilanteye-endpoint-5'

# url = "https://f52d5bfcf060.us-east-1.playback.live-video.net/api/video/v1/us-east-1.741448944443.channel.o1vOLgias3k7.m3u8"
vcap = cv2.VideoCapture(url)
if not vcap.isOpened():
    print("No se pudo abrir la transmisión.")
    exit() 
fps = vcap.get(cv2.CAP_PROP_FPS)
# w = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
# h = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
wt = 1 / fps
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
path_video = 'output.mp4'
out = None

def get_video_writter():
    w = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    return cv2.VideoWriter(path_video, fourcc, 20.0, (int(w),int(h)))

def record_video(frame, frame_buffer):
    global out
    # Guardar los últimos 10 segundos de video desde el buffer
    if frame_buffer is not None:
        for old_frame in frame_buffer:
            out.write(old_frame)  # Escribe en el archivo de salida

    if frame is not None:
       out.write(frame)

def isIntruder(predictions):
    global number_intrusion_detections
    global sequenceIntruder
    
    for prediction in predictions:
        label = prediction[0]
        if label == 'Desconocido':
            sequenceIntruder = True
            number_intrusion_detections = number_intrusion_detections + 1
            break
        else:
            sequenceIntruder = False

    if(sequenceIntruder == False):
        number_intrusion_detections = 0
        
    if number_intrusion_detections == 4:
        number_intrusion_detections = 0
        return True
    return False

def record_intruder(frame, frame_buffer):
    global init_record
    global sequenceIntruder
    global start_time_record
    global intruder_detected

    if init_record:
        print("Guardando Buffer")
        record_video(None, frame_buffer)
    else:
        print("Guardando video")
        record_video(frame, None)

    if sequenceIntruder:
        start_time_record = time.time()

    current_time_record = time.time()

    if current_time_record - start_time_record > 15:
        intruder_detected = False
        user_id_string = endpoint_name.split('-')[-1]

        s3_bucket_name = 'vigilanteye-intruder-videos'
        s3_key = f'{user_id_string}/{current_datetime}.mp4'
        out.release()
        s3_client.upload_file(path_video, s3_bucket_name, s3_key)
        time.sleep(1)
        os.remove(path_video)

        print("Grabación finalizada")


while True:
    # Agregar el frame al buffer circular
    ret, frame = vcap.read()
    if frame is not None:
        # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame_buffer.append(frame)
        if i%10 == 0:
            start_time = time.time()
                # Convert frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)

            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/x-image',
                Body=buffer.tobytes()
            )

            # Read the response from SageMaker
            result = json.loads(response['Body'].read().decode())
            print(result)
            isIntruderFlag = isIntruder(result)
            if isIntruderFlag:
                start_time_record = time.time()
                intruder_detected = True
                if init_record == False and init_record_aux == False:
                    init_record = True
                    init_record_aux = True
                    out = get_video_writter()            
                print('Se ha detectado a un intruso')

            # Press q to close the video windows before it ends if you want
            if cv2.waitKey(22) & 0xFF == ord('q'):
                break

            dt = time.time() - start_time
            if wt - dt > 0:
                time.sleep(wt - dt)
        
        if intruder_detected:
            print('Grabando')
            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

            record_intruder(frame, frame_buffer)
        init_record = False
    else:
        print("Frame is None")
    i = i + 1

# Release capture and close windows
vcap.release()
print("Video stop")
