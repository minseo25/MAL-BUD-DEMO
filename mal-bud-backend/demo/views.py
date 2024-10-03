import os
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse
from django.conf import settings
from dotenv import load_dotenv
import requests
from groq import Groq
import base64

# 환경 변수 로드
load_dotenv()

# STT and LLM : Groq API
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
# TTS : SK Open API
SK_APP_KEY = os.getenv('SK_OPEN_API_KEY')

@api_view(['POST'])
@parser_classes([MultiPartParser])
def voice_api(request):
    # 업로드된 파일들 가져오기
    audio_file = request.FILES.get('audio')
    image_file = request.FILES.get('image')

    if not audio_file:
        return HttpResponse('No audio file provided', status=400)

    # STT 처리
    user_input = stt_process(audio_file)

    if not user_input:
        return HttpResponse('STT processing failed', status=500)
    
    # print(f"user_input: {user_input}")

    # VLM 요청
    llm_response = vlm_request(user_input, image_file)

    if not llm_response:
        return HttpResponse('LLM request failed', status=500)
    
    # print(f"llm_response: {llm_response}")

    # TTS 처리
    audio_response = tts_process(llm_response)

    if not audio_response:
        return HttpResponse('TTS processing failed', status=500)
    
    # 응답 전송
    response = HttpResponse(audio_response, content_type='audio/wav')
    response['Content-Disposition'] = 'attachment; filename="response.wav"'
    return response

def stt_process(audio_file):
    # 음성 파일을 읽어들임
    audio_bytes = audio_file.read()
    filename = audio_file.name

    # Groq API를 사용하여 STT 처리
    try:
        transcription = groq_client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3",
            language="ko",
            temperature=0.0
        )
        user_input = transcription.text.strip()
        return user_input
    except Exception as e:
        print(f"STT request error: {e}")
        return None

def vlm_request(user_input, image_file):
    # 이미지 파일을 base64로 인코딩
    if image_file:
        image_bytes = image_file.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image_file.content_type  # 예: 'image/png'
        image_data_url = f"data:{mime_type};base64,{base64_image}"

        # Groq VLM API를 사용하여 LLM 요청
        try:
            print("VLM request with image")
            completion = groq_client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_input + "Answer in Korean in 150 characters or less. 한국어로 150자 이내로 답변해주세요."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url
                                }
                            }
                        ]
                    }
                ],
                temperature=1.0,
                max_tokens=150,
                top_p=1.0,
                stream=False,
                stop=None,
            )
            llm_response = completion.choices[0].message.content.strip()
            return llm_response
        except Exception as e:
            print(f"LLM request error: {e}")
            return None
    else:
        # 이미지가 없을 경우 처리
        try:
            print("LLM request without image")
            completion = groq_client.chat.completions.create(
            messages=[
                    {'role': 'system', 'content': 'You are a helpful korean assistant. 지금부터 너는 한국어로 대답을 할거야'},
                    {'role': 'user', 'content': user_input},
                ],
                model='llama-3.1-8b-instant',
                max_tokens=150,
            )
            llm_response = completion.choices[0].message.content.strip()
            return llm_response
        except Exception as e:
            print(f"LLM request error: {e}")
            return None
    

def tts_process(text):
    # SK Open API를 사용하여 TTS 처리
    speakers = ['aria', 'aria_dj', 'jiyoung', 'juwon', 'jihun', 'hamin']
    headers = {
        'Content-Type': 'application/json',
        'appKey': SK_APP_KEY,
    }
    data = {
        'text': text,
        'voice': speakers[2],
        'lang': 'ko-KR',
        'speed': '1.0',
        'sformat': 'wav',
        'sr': '16000',
    }
    try:
        tts_response = requests.post(
             'https://apis.openapi.sk.com/tvoice/tts', headers=headers, json=data,
        )

        if tts_response.status_code != 200:
            print(f"TTS API error: {tts_response.status_code}")
            return None

        return tts_response.content
    except Exception as e:
        print(f"TTS request error: {e}")
        return None
