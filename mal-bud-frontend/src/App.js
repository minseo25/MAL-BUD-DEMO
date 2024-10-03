import React, { useState } from 'react';
import { ToastContainer, toast, Bounce } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';
import iphoneImage from './assets/images/iphone.png';
import robotImage from './assets/images/robot.png';

function App() {
  const [useClipboard, setUseClipboard] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);

  const onStartRecording = async () => {
    try {
      // 마이크 권한 요청 및 스트림 가져오기
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      // state로 두면 비동기로 즉시 업데이트가 안 됨
      const audioChunks = [];

      recorder.ondataavailable = (e) => {
        audioChunks.push(e.data);
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        await sendDataToServer(audioBlob);

        // reset media recorder and clipboard image
        setMediaRecorder(null);
      }

      recorder.start();
      setMediaRecorder(recorder);

      toast('녹음 시작', {
        position: "top-center",
        autoClose: 500,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: false,
        draggable: true,
        progress: undefined,
        theme: "light",
        transition: Bounce,
      });
    } catch (err) {
      console.error("마이크 접근 오류");
    }
  }

  const onStopRecording = async () => {
    if(mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  }

  const fetchClipboardImage = async () => {
    try {
      const clipboardItems = await navigator.clipboard.read();
      for (const clipboardItem of clipboardItems) {
        for (const type of clipboardItem.types) {
          if (type.startsWith('image/')) {
            const blob = await clipboardItem.getType(type);
            return blob;
          }
        }
      }
      return null;
    } catch (err) {
      console.error("클립보드 접근 오류");
      return null;
    }
  }

  const sendDataToServer = async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    console.log("audioBlob: ", audioBlob);

    if(useClipboard) {
      const imageBlob = await fetchClipboardImage();
      if(imageBlob) {
        console.log("imageBlob: ", imageBlob);
        formData.append('image', imageBlob, 'image.png');
      }
    }

    try {
      toast('말벗에게 물어볼게요...', {
        position: "top-center",
        autoClose: 1000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: false,
        draggable: true,
        progress: undefined,
        theme: "light",
        transition: Bounce,
      });

      const response = await fetch('http://localhost:8000/demo/vlm/', {
        method: 'POST',
        body: formData,
      });

      if(response.ok) {
        const reponseBlob = await response.blob();
        const url = URL.createObjectURL(reponseBlob);
        const audio = new Audio(url);
        audio.play();
      } else {
        toast.error('서버 오류', {
          position: "top-center",
          autoClose: 1000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: false,
          draggable: true,
          progress: undefined,
          theme: "light",
          transition: Bounce,
        });
      }
    } catch (err) {
      console.error("서버 접근 오류");
    }
  }

  const handleCheckboxChange = () => {
    setUseClipboard(!useClipboard);
  }

  return (
    <div className="App">
      <ToastContainer />
      <div className="relative">
        <img src={iphoneImage} alt="iPhone" className="max-w-full h-auto" />
        <div className="absolute inset-0 flex flex-col justify-center items-center space-y-4">
          <img src={robotImage} alt="Robot" className="w-1/5 mb-2" />
          <button className="w-1/3 py-2 bg-green-500 text-white rounded" onClick={onStartRecording}>
            녹음 시작
          </button>
          <button className="w-1/3 py-2 bg-red-500 text-white rounded" onClick={onStopRecording}>
            녹음 종료
          </button>
          <div className="flex flex-col items-center mt-4">
            <label className="mb-2 text-center">클립보드 내용 전송 여부</label>
            <input type="checkbox" className="form-checkbox h-5 w-5 text-blue-600" checked={useClipboard} onChange={handleCheckboxChange} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
