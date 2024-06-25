import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import cv2
import numpy as np
from PIL import Image
import os
import mediapipe as mp
import math
import serial
import time
import json
import openvino as ov

# 아두이노 연결 여부를 나타내는 변수 초기화
is_arduino_connected = False

# 아두이노 연결 확인
try:
    py_serial = serial.Serial(    
        # Window
        port='COM4',
        # 보드 레이트 (통신 속도)
        baudrate=9600,
    )
    is_arduino_connected = True
except serial.SerialException:
    print("No connection with Arduino")

# MTCNN과 ResNet 모델 초기화
mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# 사전학습할 회원 이미지 폴더 경로
member_folders = ["Images_face2/Images/Jaehyeok", "Images_face2/Images/Jeong", "Images_face2/Images/Jiwon", "Images_face2/Images/Kihoon"]

# 모든 회원의 인코딩과 이름 저장 리스트
known_encodings = []
known_names = []

# 사람 정보를 저장할 딕셔너리
#person_data = {}

# 사람 정보 파일 경로
person_data_file = "person_data.json"

# 함수 선언
def read_value(key):
    try:
        with open(person_data_file, "r") as file:
            data = json.load(file)
            if key in data:
                value1 = data[key]["value1"]
                value2 = data[key]["value2"]
                print(f"[{key}] value1: {value1}, value2: {value2}")
                return value1, value2
            else:
                print(f"'{key}' does't exist.")
                return None, None
    except FileNotFoundError:
        print("JSON file doesn't exist.")
        return None, None
    except json.JSONDecodeError:
        print("json.JSONDecodeError")
        return None, None
    
def write_value(key, value1, value2):
    try:
        if not os.path.exists(person_data_file):
            data = {}
        else:
            with open(person_data_file, "r") as file:
                data = json.load(file)

        data[key] = {
            "value1": value1,
            "value2": value2
        }

        with open(person_data_file, "w") as file:
            json.dump(data, file, indent=2)
            print(f"'{key}''s value is saved successfully.")
    except IOError:
        print("JSON file write Fail")

# 파일에서 사람 정보 읽어오기
# if os.path.exists(person_data_file):
#     with open(person_data_file, "r") as file:
#         person_data = json.load(file)

# 각 회원 폴더의 이미지를 로드하여 인코딩
for member_folder in member_folders:
    member_name = member_folder.split('/')[2]  # 폴더명에서 이름 추출
    print(member_name)
    for image_name in os.listdir(member_folder):
        image_path = os.path.join(member_folder, image_name)
        image = Image.open(image_path)
        face = mtcnn(image)
        if face is not None:
            encoding = resnet(face.unsqueeze(0)).detach().cpu()
            known_encodings.append(encoding)
            known_names.append(member_name)

# face_mesah 초기화
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# 얼굴 각도 추정 모델
core = ov.Core()
device = 'CPU'
model_path_head = "./models/head-pose-estimation-adas-0001/head-pose-estimation-adas-0001.xml"
model_head = core.read_model(model=model_path_head)
compiled_model_head = core.compile_model(model=model_head, device_name=device)

input_layer_head = compiled_model_head.input(0)
output_layer_pitch = compiled_model_head.output(1)
height_head, width_head = list(input_layer_head.shape)[2:4]

# 인식된 사람 변수
recognized_person = None
recognized_time = None
is_changed = True

# 웹캠 비디오 캡처 초기화
video_capture = cv2.VideoCapture(0)
prev_angle = 90
height = 0
angle = 0

# 3초 동안 비디오 프레임 보여주기
start_time = time.time()
while time.time() - start_time < 3:
    ret, frame = video_capture.read()
    cv2.imshow('Video', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

while True:
    # 비디오 프레임 읽기
    ret, frame = video_capture.read()
    if not ret:
        break

    # 현재 프레임에서 얼굴 찾기
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face = mtcnn(image)

    if face is not None:
        encoding = resnet(face.unsqueeze(0)).detach().cpu()

        # 얼굴 인코딩 비교
        distances = [torch.dist(encoding, known_encoding).item() for known_encoding in known_encodings]
        min_distance = min(distances)
        min_index = distances.index(min_distance)
        
        name = "Unknown"
        is_member = False
        if min_distance < 1.0:  # 임계값 설정 (필요에 따라 조정 가능)
            name = known_names[min_index]
            is_member = True

            # 첫 번째 인식된 사람 설정
            if recognized_person is None:
                recognized_person = name
                recognized_time = time.time()
            else:
                # 10초 동안 다른 사람으로 인식되면 새로운 작업 수행
                if name != recognized_person and time.time() - recognized_time >= 10:
                    print(f"새로운 사람 인식: {name}")
                    # 여기에 새로운 작업 코드 추가
                    recognized_person = name
                    recognized_time = time.time() 
                    is_changed = True
        
        # 얼굴 주위에 사각형 그리기 및 이름 표시
        boxes, _ = mtcnn.detect(image)
        if boxes is not None:
            for box in boxes:
                cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 0, 255), 2)
                cv2.putText(frame, name, (int(box[0]), int(box[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        # 저장 값이 있고 사람 변경 시
        if is_member :#and is_changed:
            is_changed = False
            height_saved, angle_saved = read_value(name)
            #print(f"name = {name}, {height_saved}, {angle_saved}")
            
            if True:#height_saved == -1 or angle_saved == -1 :
                for box in boxes:
                    y_point = (box[1]+box[3])//2
                    y_height = frame.shape[0]
                    height = (y_point/y_height)*180
                    if height < 0:
                        height = 0
                    elif height > 180:
                        height = 180
                    if len(box) == 0:
                        break

                    # 얼굴 좌표가 유효한지 확인
                    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                    if x1 < 0 or y1 < 0 or x2 > frame.shape[1] or y2 > frame.shape[0]:
                        continue

                    # 얼굴 이미지 추출
                    input_head = frame[y1:y2, x1:x2]
                    if input_head.size == 0:
                        continue

                    input_head = cv2.resize(src=input_head, dsize=(width_head, height_head), interpolation=cv2.INTER_AREA)
                    input_head = input_head.transpose((2, 0, 1))
                    input_head = input_head[np.newaxis, ...]

                    # 각도 추정
                    results_pitch = compiled_model_head([input_head])[output_layer_pitch]
                    angle = np.squeeze(results_pitch)
                    height = int(height)
                    angle = int(angle+90)
                    value = height*1000 + angle
                    #angle_str = str(int(value)) + '\n'  # 정수를 문자열로 변환하고 개행 문자 추가
                    print('height :', height, 'angle:',angle)
                    angle_str = f"{int(value):06d}\n"  # 정수를 3자리 문자열로 변환하고 나머지 3자리는 "000"으로 채움, 개행 문자 추가
                    print(angle_str)
                    
                    if is_arduino_connected:
                        py_serial.write(angle_str.encode())  # 문자열을 바이트로 인코딩하여 전송
                        time.sleep(0.1)
            else :
                height = int(height_saved)
                angle = int(angle_saved)
                value = height*1000 + angle
                angle_str = f"{int(value):06d}\n" 
                if is_arduino_connected:
                    py_serial.write(angle_str.encode())  # 문자열을 바이트로 인코딩하여 전송
                    time.sleep(0.1)                                                

            cv2.putText(frame, f"Height: {height:.2f} degrees", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Angle: {angle:.2f} degrees", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 시리얼 포트로부터 데이터 읽기        
        if is_arduino_connected and py_serial.in_waiting > 0:
            data = py_serial.readline().decode('utf-8').rstrip()
            if len(data) > 0:
                first_char = data[0]
                
                if first_char.isdigit():
                    # 첫 글자가 숫자인 경우 처리
                    values = data.split(',')
                    try:
                        value1 = int(values[0])
                        value2 = int(values[1])
                        print(f"Received values: {value1}, {value2}")
                        # 필요한 처리 작업 수행
                    except (ValueError, IndexError):
                        print("Invalid input. Expected two integer values separated by a comma.")
                else:
                    # 첫 글자가 문자인 경우 무시
                    print("Ignoring line starting with a character.")

    # 결과 비디오 출력
    cv2.imshow('Video', frame)
      # 딜레이 시간 조정 (필요에 따라 조정)
    #     print(angle)
    #     py_serial.write(str(int(angle)))
    #     time.sleep(5)
    # 'q' 키를 누르면 루프 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 웹캠 릴리스 및 모든 윈도우 닫기
video_capture.release()
cv2.destroyAllWindows()