C:\source> py -m venv taihan
C:\source> taihan\scripts\activate
(taihan) C:\source> python.exe -m pip install --upgrade pip

# install CUDA verseion: 11.8
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics

pip install roboflow
pip install pypylon
pip install pymodbus==3.6.9

pip uninstall opencv-python
pip install opencv-python

# 설치된 모듈 확인
pip list | grep 모듈명 # 리눅스
pip list | findstr 모듈명 # 리눅스

# git 사용자, 이메일 추가
git config user.name "[user name]"
git config user.email "[user email]"