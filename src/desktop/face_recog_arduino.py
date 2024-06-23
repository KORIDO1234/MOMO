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

py_serial = serial.Serial(
    
    # Window
    port='COM4',
    
    # 보드 레이트 (통신 속도)
    baudrate=9600,
)

# MTCNN과 ResNet 모델 초기화
mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# 사전학습할 회원 이미지 폴더 경로
member_folders = ["Images_face2/Images/Jaehyeok", "Images_face2/Images/Jeong", "Images_face2/Images/Jiwon", "Images_face2/Images/Kihoon"]

# 모든 회원의 인코딩과 이름 저장 리스트
known_encodings = []
known_names = []

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

# 웹캠 비디오 캡처 초기화
video_capture = cv2.VideoCapture(0)
prev_angle = 90
height = 0
angle = 0
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
        
        # 얼굴 주위에 사각형 그리기 및 이름 표시
        boxes, _ = mtcnn.detect(image)
        if boxes is not None:
            for box in boxes:
                cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 0, 255), 2)
                cv2.putText(frame, name, (int(box[0]), int(box[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                y_point = (box[1]+box[3])//2
                y_height = frame.shape[0]
                height = (y_point/y_height)*180
                if height <0:
                    height = 0
                elif height > 180 :
                    height = 180
            

    # 얼굴 각도 계산
    image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image)

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            landmarks = face_landmarks.landmark

            nose_tip = landmarks[1]
            left_eye_inner = landmarks[133]
            right_eye_inner = landmarks[362]
            left_eye_center = landmarks[159]
            right_eye_center = landmarks[386]

            left_eye = (left_eye_inner.x, left_eye_inner.y)
            right_eye = (right_eye_inner.x, right_eye_inner.y)
            nose = (nose_tip.x, nose_tip.y)

            # 좌우 기울기 각도 계산
            left_eye_to_nose = (left_eye[0] - nose[0], left_eye[1] - nose[1])
            right_eye_to_nose = (right_eye[0] - nose[0], right_eye[1] - nose[1])
            yaw_angle = math.degrees(math.atan2(right_eye_to_nose[1] - left_eye_to_nose[1],
                                                right_eye_to_nose[0] - left_eye_to_nose[0]))

            # 상하 기울기 각도 계산
            eyes_center = ((left_eye_center.x + right_eye_center.x) / 2, (left_eye_center.y + right_eye_center.y) / 2)
            eyes_to_nose = (nose[0] - eyes_center[0], nose[1] - eyes_center[1])
            pitch_angle = math.degrees(math.atan2(eyes_to_nose[1], eyes_to_nose[0]))
            
            angle = 180 - (100-pitch_angle)*5
            if angle <0:
                angle = 0
            elif angle > 180 :
                angle = 180
            if abs(angle-prev_angle) > 20 :
                print('angle')
                height = int(height)
                angle = int(angle)
                value = height*1000 + angle
                #angle_str = str(int(value)) + '\n'  # 정수를 문자열로 변환하고 개행 문자 추가
                print('height :', height, 'angle:',angle)
                angle_str = f"{int(value):06d}\n"  # 정수를 3자리 문자열로 변환하고 나머지 3자리는 "000"으로 채움, 개행 문자 추가
                print(angle_str)
                py_serial.write(angle_str.encode())  # 문자열을 바이트로 인코딩하여 전송
                time.sleep(0.1)
                prev_angle = angle
                

            cv2.putText(frame, f"Yaw Angle: {yaw_angle:.2f} degrees", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Pitch Angle: {pitch_angle:.2f} degrees", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

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