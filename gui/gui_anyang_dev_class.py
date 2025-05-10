import tkinter as tk
from tkinter import ttk # ttk 위젯 사용 권장
from tkinter import messagebox
from pypylon import pylon
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image, ImageTk
import traceback
import os
import sys
import time
import logging
import threading
import queue
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

# --- 프로젝트 경로 설정 ---
# 이 파일을 기준으로 상대 경로를 사용하거나 환경 변수 사용을 고려
PROJECT_ROOT = 'C:/source'
sys.path.append(PROJECT_ROOT)

# --- 유틸리티 및 SQL 모듈 임포트 ---
# 임포트 실패 시 에러 처리를 추가하면 더 좋습니다.
try:
    import util.format_date_time as date_util # 이름 충돌 방지
    import util.merge as imgmerge
    import SQL.insert_sqllite_start as start_db
    import SQL.insert_sqllite_detect as detect_db
    # import SQL.insert_sqllite_area as areadb # 코드에서 사용되지 않는 것으로 보임
except ImportError as e:
    print(f"필수 모듈 임포트 실패: {e}")
    sys.exit(1) # 프로그램 종료

# --- 로깅 설정 ---
LOG_DIR = os.path.join(PROJECT_ROOT, 'log')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"app_{date_util.get_date_in_yyyymmdd()}.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- 설정값 상수 ---
# 경로
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models/taihanfiber_14-1_20250406_yolo11m-seg_best.pt')
IMAGE_SAVE_BASE_PATH = 'C:/image'
AREA_DB_BASE_PATH = 'C:/areaDB' # 코드에서 실제 사용 부분 확인 필요

# YOLO 설정
DEFAULT_IMG_SIZE = 640
DEFAULT_CONFIDENCE = 0.48
MIN_SAVE_CONFIDENCE = 0.50 # 저장 기준 Confidence

# PLC 설정
PLC_IP = '192.168.102.20'
PLC_PORT = 502
PLC_TIMEOUT = 1 # 초 단위
PLC_COILS = {
    'START_STOP': 0x01, # 시작/정지 (M1)
    'RESET': 0x04,      # 리셋 (M4) - 사용 로직 확인 필요
    'DETECT_SIGNAL': 0x20, # 불량 검출 신호 (M32)
    'STATUS_1': 0x53,   # 상태 1 (M53)
    'STATUS_2': 0x54,   # 상태 2 (M54)
}
PLC_REGISTERS = {
    'ERROR_COUNT': 0x0008, # 에러 카운트 (D8)
    'SERIAL_START': 120,   # 제품번호 시작 주소 (D120)
    'SERIAL_COUNT': 5,     # 제품번호 레지스터 개수
    'START_YEAR': 632,    # 시작 년도 (D632)
    'START_MONTH': 621,   # 시작 월 (D621)
    'START_DAY': 622,     # 시작 일 (D622)
    'START_HOUR': 623,    # 시작 시 (D623)
    'START_MINUTE': 624,  # 시작 분 (D624)
    'START_SECOND': 625,  # 시작 초 (D625)
    'ERROR_METER_BASE': 1000 # 불량 미터 기본 주소 (D1000) - 확인 필요
}

# 카메라 설정
DEFAULT_EXPOSURE_TIME = 300
EXPOSURE_CHECK_FRAMES = 100 # 노출 시간 조정을 위한 프레임 수
EXPOSURE_CHECK_START_FRAME = 50 # 밝기 평균 계산 시작 프레임
BRIGHTNESS_THRESHOLD_HIGH = 70
BRIGHTNESS_THRESHOLD_LOW = 35
EXPOSURE_HIGH = 150 # 밝을 때 노출값
EXPOSURE_LOW = 300  # 어두울 때 노출값

# 기타
GAMMA_CORRECTION_VALUE = 0.6
UI_UPDATE_INTERVAL_MS = 30 # UI 업데이트 주기 (밀리초)
PLC_POLL_INTERVAL_MS = 500 # PLC 상태 확인 주기 (밀리초)
THREAD_STOP_TIMEOUT = 2 # 스레드 종료 대기 시간 (초)

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Detection Display")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- 상태 변수 ---
        self.is_running = False
        self.plc_connected = False
        self.last_plc_status = {'m01': None, 'm04': None, 'm53': None, 'm54': None}
        self.current_plc_status = {'m01': False, 'm04': False, 'm53': False, 'm54': False}
        self.product_start_time_str = "N/A"
        self.detection_count = 0
        self.last_detection_time = 0
        self.confidence_threshold = DEFAULT_CONFIDENCE
        self.cable_area_base = 0

        # --- *** 중요: UI 관련 초기화 먼저 수행 *** ---
        self.ui_vars = {} # UI 변수 딕셔너리 초기화
        self._create_widgets() # UI 위젯 생성 (이 안에서 self.ui_vars가 채워짐)

        # --- 객체 초기화 ---
        self.model = self._load_yolo_model()
        self.cameras = self._initialize_cameras()
        self.converter = self._initialize_pylon_converter()
        self.plc_client = ModbusTcpClient(PLC_IP, port=PLC_PORT, timeout=PLC_TIMEOUT)

        # --- *** PLC 연결은 UI 생성 후에 수행 *** ---
        self._connect_plc() # 초기 PLC 연결 시도 (이제 self.ui_vars가 존재함)

        # --- 스레딩 및 큐 ---
        self.ui_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.camera_thread = None
        self.plc_thread = None

        # --- 초기 상태 업데이트 ---
        # self._update_ui_status_labels() # _create_widgets 후에 호출되므로 여기서 필요 없을 수 있음
        # self._update_plc_display() # _connect_plc 내부에서 이미 호출됨

        # --- 주기적 작업 시작 ---
        self.root.after(UI_UPDATE_INTERVAL_MS, self._process_ui_queue)
        self._start_plc_polling() # PLC 폴링 시작


    def _load_yolo_model(self):
        """YOLO 모델 로드"""
        try:
            model = YOLO(MODEL_PATH)
            print("YOLO 모델 로드 성공")
            return model
        except Exception as e:
            logging.error(f"YOLO 모델 로드 실패: {traceback.format_exc()}")
            messagebox.showerror("오류", f"YOLO 모델 로드 실패:\n{e}")
            self.root.destroy()
            return None

    def _initialize_cameras(self):
        """Pylon 카메라 초기화 및 설정"""
        cameras = []
        try:
            tlf = pylon.TlFactory.GetInstance()
            devices = tlf.EnumerateDevices()
            if not devices:
                messagebox.showerror("오류", "연결된 카메라를 찾을 수 없습니다.")
                self.root.destroy()
                return []

            for device in devices:
                camera = pylon.InstantCamera(tlf.CreateDevice(device))
                camera.Open() # 설정 전에 Open 필요
                # 초기 노출 시간 설정
                try:
                    camera.ExposureTimeAbs.SetValue(DEFAULT_EXPOSURE_TIME)
                except Exception as e:
                    print(f"카메라 초기 노출 시간 설정 실패 (계속 진행): {e}")
                    logging.warning(f"카메라 초기 노출 시간 설정 실패: {traceback.format_exc()}")

                camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                cameras.append(camera)
            print(f"{len(cameras)}개의 카메라 초기화 성공")
            return cameras
        except Exception as e:
            logging.error(f"카메라 초기화 실패: {traceback.format_exc()}")
            messagebox.showerror("오류", f"카메라 초기화 실패:\n{e}")
            self.root.destroy()
            return []

    def _initialize_pylon_converter(self):
        """Pylon 이미지 변환기 초기화"""
        try:
            converter = pylon.ImageFormatConverter()
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            return converter
        except Exception as e:
            logging.error(f"Pylon 변환기 초기화 실패: {traceback.format_exc()}")
            messagebox.showerror("오류", f"Pylon 변환기 초기화 실패:\n{e}")
            self.root.destroy()
            return None

    def _connect_plc(self):
        """PLC 연결 시도"""
        try:
            self.plc_connected = self.plc_client.connect()
            if not self.plc_connected:
                print("PLC 연결 실패")
                # UI에 연결 실패 상태 표시
                self.ui_vars['m01_value'].set("PLC 연결 실패")
                # 필요시 재시도 로직 추가
            else:
                print("PLC 연결 성공")
                # 초기 상태 읽기
                self._read_plc_status()
                self._update_plc_display()

        except Exception as e:
            self.plc_connected = False
            print(f"PLC 연결 중 오류: {e}")
            logging.error(f"PLC 연결 오류: {traceback.format_exc()}")
            self.ui_vars['m01_value'].set("PLC 연결 오류")


    def _create_widgets(self):
        """Tkinter 위젯 생성 및 배치"""
        # 프레임 사용으로 레이아웃 개선
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky="nw")

        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.grid(row=1, column=0, sticky="nw")

        plc_frame = ttk.Frame(self.root, padding="10")
        plc_frame.grid(row=2, column=0, sticky="nw")

        image_frame = ttk.Frame(self.root, padding="10")
        image_frame.grid(row=0, column=1, rowspan=3, sticky="nsew")

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1) # 이미지 프레임이 확장되도록 설정

        # --- 제어 버튼 ---
        ttk.Button(control_frame, text="검사 시작/재개", command=self.start_inspection).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="일시 정지", command=self.pause_inspection).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="프로그램 종료", command=self.on_closing).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="수동 Start 버튼", command=self.manual_start_button).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="수동 리셋 버튼", command=self.manual_reset_button).grid(row=1, column=1, padx=5, pady=5)
        # ttk.Button(control_frame, text="면적 초기화", command=self.reset_area_base).grid(row=1, column=2, padx=5, pady=5) # 기능 구현 필요

        # --- 상태 표시 ---
        row_idx = 0
        self.ui_vars['inspection_status'] = tk.StringVar(value="준비 중")
        self._create_label_value_pair(status_frame, row_idx, "검사 상태:", self.ui_vars['inspection_status'])
        row_idx += 1
        self.ui_vars['cable_area_base'] = tk.StringVar(value="N/A")
        self._create_label_value_pair(status_frame, row_idx, "면적 기준:", self.ui_vars['cable_area_base']) # 면적 관련 라벨 수정
        row_idx += 1
        self.ui_vars['current_confidence'] = tk.StringVar(value=f"{self.confidence_threshold:.2f}")
        self._create_label_value_pair(status_frame, row_idx, "현재 Confidence:", self.ui_vars['current_confidence'])
        row_idx += 1

        # Confidence 변경
        ttk.Label(status_frame, text="Confidence 변경:").grid(row=row_idx, column=0, sticky="w", pady=2)
        self.ui_vars['confidence_entry'] = tk.StringVar(value=f"{self.confidence_threshold:.2f}")
        entry_confidence = ttk.Entry(status_frame, textvariable=self.ui_vars['confidence_entry'], width=10)
        entry_confidence.grid(row=row_idx, column=1, sticky="w", pady=2)
        ttk.Button(status_frame, text="변경", command=self.change_confidence).grid(row=row_idx, column=2, padx=5, pady=2)
        ttk.Button(status_frame, text="기본값", command=self.reset_confidence).grid(row=row_idx, column=3, padx=5, pady=2)
        row_idx += 1

        # 처리 속도
        self.ui_vars['proc_speed_ms'] = tk.StringVar(value="N/A")
        self._create_label_value_pair(status_frame, row_idx, "처리 속도 (ms):", self.ui_vars['proc_speed_ms'])
        row_idx += 1
        self.ui_vars['proc_speed_fps'] = tk.StringVar(value="N/A")
        self._create_label_value_pair(status_frame, row_idx, "처리 속도 (fps):", self.ui_vars['proc_speed_fps'])
        row_idx += 1
        # 최대 처리 속도 계산 로직 확인 필요
        # self.ui_vars['max_proc_speed_cms'] = tk.StringVar(value="N/A")
        # self._create_label_value_pair(status_frame, row_idx, "최대 처리 (cm/s):", self.ui_vars['max_proc_speed_cms'])
        # row_idx += 1

        # --- PLC 상태 표시 ---
        row_idx = 0
        self.ui_vars['m01_value'] = tk.StringVar(value="읽는 중...")
        self._create_label_value_pair(plc_frame, row_idx, "시작/정지 (M1):", self.ui_vars['m01_value'])
        row_idx += 1
        self.ui_vars['m53_value'] = tk.StringVar(value="읽는 중...")
        self._create_label_value_pair(plc_frame, row_idx, "상태 1 (M53):", self.ui_vars['m53_value'])
        row_idx += 1
        self.ui_vars['m54_value'] = tk.StringVar(value="읽는 중...")
        self._create_label_value_pair(plc_frame, row_idx, "상태 2 (M54):", self.ui_vars['m54_value'])
        row_idx += 1
        self.ui_vars['m04_value'] = tk.StringVar(value="읽는 중...")
        self._create_label_value_pair(plc_frame, row_idx, "리셋 (M4):", self.ui_vars['m04_value'])
        row_idx += 1

        # --- 이미지 표시 ---
        # 초기 빈 이미지 설정
        placeholder_img = Image.new('RGB', (530, 530), color = 'grey')
        self.tk_image = ImageTk.PhotoImage(placeholder_img)
        self.image_label = ttk.Label(image_frame, image=self.tk_image)
        self.image_label.pack(expand=True, fill="both")

    def _create_label_value_pair(self, parent, row, label_text, string_var):
        """라벨과 값(StringVar) 쌍을 생성하고 배치하는 헬퍼 함수"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(parent, textvariable=string_var).grid(row=row, column=1, sticky="w", padx=5, pady=2, columnspan=3) # 값 표시 라벨은 여러 컬럼 차지하도록

    # --- UI 업데이트 메서드 ---
    def _update_ui_status_labels(self):
        """UI 상태 관련 라벨 업데이트"""
        status_text = "검사 중" if self.is_running else "일시 정지" if self.camera_thread else "준비 중"
        self.ui_vars['inspection_status'].set(status_text)
        # self.ui_vars['cable_area_base'].set(f"{self.cable_area_base:.2f}" if isinstance(self.cable_area_base, (int, float)) else "N/A") # 면적 계산 로직 추가 필요
        self.ui_vars['current_confidence'].set(f"{self.confidence_threshold:.2f}")

    def _update_plc_display(self):
        """PLC 상태 값 UI 업데이트"""
        if not self.plc_connected:
            val = "연결 끊김"
            self.ui_vars['m01_value'].set(val)
            self.ui_vars['m53_value'].set(val)
            self.ui_vars['m54_value'].set(val)
            self.ui_vars['m04_value'].set(val)
        else:
            self.ui_vars['m01_value'].set(str(self.current_plc_status.get('m01', 'N/A')))
            self.ui_vars['m53_value'].set(str(self.current_plc_status.get('m53', 'N/A')))
            self.ui_vars['m54_value'].set(str(self.current_plc_status.get('m54', 'N/A')))
            self.ui_vars['m04_value'].set(str(self.current_plc_status.get('m04', 'N/A')))

    def _update_image_display(self, image_array):
        """카메라 이미지 UI 업데이트"""
        try:
            resized_img = cv2.resize(image_array, (530, 530)) # UI 크기에 맞게 조절
            img = Image.fromarray(resized_img)
            self.tk_image = ImageTk.PhotoImage(image=img)
            self.image_label.configure(image=self.tk_image)
            self.image_label.image = self.tk_image # 참조 유지
        except Exception as e:
            print(f"이미지 표시 오류: {e}")
            logging.warning(f"이미지 표시 오류: {traceback.format_exc()}")

    def _update_speed_display(self, proc_time_ms):
        """처리 속도 UI 업데이트"""
        try:
            if proc_time_ms > 0:
                fps = 1000.0 / proc_time_ms
                # max_speed_cms = fps * 6 # 이 계산의 근거 확인 필요
                self.ui_vars['proc_speed_ms'].set(f"{proc_time_ms:.0f}")
                self.ui_vars['proc_speed_fps'].set(f"{fps:.1f}")
                # self.ui_vars['max_proc_speed_cms'].set(f"{max_speed_cms:.0f}")
            else:
                self.ui_vars['proc_speed_ms'].set("N/A")
                self.ui_vars['proc_speed_fps'].set("N/A")
                # self.ui_vars['max_proc_speed_cms'].set("N/A")
        except Exception as e:
            print(f"속도 표시 오류: {e}")
            logging.warning(f"속도 표시 오류: {traceback.format_exc()}")


    # --- PLC 통신 메서드 ---
    def _read_plc_status(self):
        """PLC 상태 코일 읽기"""
        if not self.plc_client.is_socket_open():
            print("PLC 연결 시도 중...")
            self._connect_plc() # 연결 재시도

        if not self.plc_connected:
            return False # 연결 실패 시 읽기 중단

        try:
            # 각 코일 주소 읽기
            m01_res = self.plc_client.read_coils(PLC_COILS['START_STOP'], 1)
            m04_res = self.plc_client.read_coils(PLC_COILS['RESET'], 1)
            m53_res = self.plc_client.read_coils(PLC_COILS['STATUS_1'], 1)
            m54_res = self.plc_client.read_coils(PLC_COILS['STATUS_2'], 1)

            # 결과 확인 및 저장
            status = {}
            if not m01_res.isError(): status['m01'] = m01_res.bits[0]
            if not m04_res.isError(): status['m04'] = m04_res.bits[0]
            if not m53_res.isError(): status['m53'] = m53_res.bits[0]
            if not m54_res.isError(): status['m54'] = m54_res.bits[0]

            # 이전 상태와 비교
            changed = False
            for key, value in status.items():
                 # 처음 읽거나 값이 변경된 경우
                if self.current_plc_status.get(key) is None or self.current_plc_status[key] != value:
                    changed = True
                self.current_plc_status[key] = value # 현재 상태 업데이트

            # # 상태 변경 시 로그 (옵션)
            # if changed:
            #     print(f"PLC 상태 변경 감지: {self.current_plc_status}")

            return True # 성공적으로 읽음

        except ConnectionException:
            print("PLC 연결 끊김 감지")
            self.plc_connected = False
            self._update_plc_display()
            return False
        except Exception as e:
            print(f"PLC 상태 읽기 오류: {e}")
            logging.error(f"PLC 상태 읽기 오류: {traceback.format_exc()}")
            return False

    def _get_plc_start_time(self):
        """PLC에서 제품 시작 시간 읽기"""
        if not self.plc_connected: return None
        try:
            # 레지스터 읽기
            year_res = self.plc_client.read_holding_registers(PLC_REGISTERS['START_YEAR'], 1)
            month_res = self.plc_client.read_holding_registers(PLC_REGISTERS['START_MONTH'], 1)
            day_res = self.plc_client.read_holding_registers(PLC_REGISTERS['START_DAY'], 1)
            hour_res = self.plc_client.read_holding_registers(PLC_REGISTERS['START_HOUR'], 1)
            min_res = self.plc_client.read_holding_registers(PLC_REGISTERS['START_MINUTE'], 1)
            sec_res = self.plc_client.read_holding_registers(PLC_REGISTERS['START_SECOND'], 1)

            # 에러 체크 및 값 추출
            if any(res.isError() for res in [year_res, month_res, day_res, hour_res, min_res, sec_res]):
                print("PLC 시작 시간 읽기 오류 (부분 실패)")
                return None

            yyyy = year_res.registers[0]
            mm = str(month_res.registers[0]).zfill(2)
            dd = str(day_res.registers[0]).zfill(2)
            hh = str(hour_res.registers[0]).zfill(2)
            nn = str(min_res.registers[0]).zfill(2)
            ss = str(sec_res.registers[0]).zfill(2)

            return f"{yyyy}{mm}{dd}{hh}{nn}{ss}"

        except ConnectionException:
            print("PLC 연결 끊김 감지 (시작 시간)")
            self.plc_connected = False
            self._update_plc_display()
            return None
        except Exception as e:
            print(f"PLC 시작 시간 읽기 오류: {e}")
            logging.error(f"PLC 시작 시간 읽기 오류: {traceback.format_exc()}")
            return None

    def _get_plc_serial_number(self):
        """PLC에서 제품 시리얼 번호 읽기"""
        if not self.plc_connected: return None
        try:
            serial_chars = []
            for i in range(PLC_REGISTERS['SERIAL_COUNT']):
                reg_addr = PLC_REGISTERS['SERIAL_START'] + i
                result = self.plc_client.read_holding_registers(reg_addr, 1)
                if result.isError():
                    print(f"PLC 시리얼 번호 읽기 오류 (주소: {reg_addr})")
                    return None # 부분 실패 시 중단

                value = result.registers[0]
                char1 = (value & 0x00FF)
                char2 = value >> 8
                # 유효한 ASCII 범위인지 확인 (옵션)
                if 32 <= char1 <= 126: serial_chars.append(chr(char1))
                if 32 <= char2 <= 126: serial_chars.append(chr(char2))

            return "".join(serial_chars).strip() # 공백 제거

        except ConnectionException:
            print("PLC 연결 끊김 감지 (시리얼 번호)")
            self.plc_connected = False
            self._update_plc_display()
            return None
        except Exception as e:
            print(f"PLC 시리얼 번호 읽기 오류: {e}")
            logging.error(f"PLC 시리얼 번호 읽기 오류: {traceback.format_exc()}")
            return None

    def _get_plc_error_count(self):
        """PLC에서 에러 카운트 읽기"""
        if not self.plc_connected: return None
        try:
            result = self.plc_client.read_holding_registers(PLC_REGISTERS['ERROR_COUNT'], 1)
            if result.isError():
                print("PLC 에러 카운트 읽기 오류")
                return None
            return result.registers[0]
        except ConnectionException:
            print("PLC 연결 끊김 감지 (에러 카운트)")
            self.plc_connected = False
            self._update_plc_display()
            return None
        except Exception as e:
            print(f"PLC 에러 카운트 읽기 오류: {e}")
            logging.error(f"PLC 에러 카운트 읽기 오류: {traceback.format_exc()}")
            return None

    def _get_plc_error_meter(self, error_index):
        """PLC에서 특정 에러 발생 미터 읽기"""
        if not self.plc_connected: return None
        try:
            # 주소 계산 방식 확인 필요 (D1000 + error_index?)
            reg_addr = PLC_REGISTERS['ERROR_METER_BASE'] + error_index
            result = self.plc_client.read_holding_registers(reg_addr, 1)
            if result.isError():
                print(f"PLC 에러 미터 읽기 오류 (주소: {reg_addr})")
                return None
            return result.registers[0]
        except ConnectionException:
            print("PLC 연결 끊김 감지 (에러 미터)")
            self.plc_connected = False
            self._update_plc_display()
            return None
        except Exception as e:
            print(f"PLC 에러 미터 읽기 오류: {e}")
            logging.error(f"PLC 에러 미터 읽기 오류: {traceback.format_exc()}")
            return None

    def _send_plc_detection_signal(self):
        """PLC로 불량 검출 신호 전송 (M32 On -> Off)"""
        if not self.plc_connected: return False
        try:
            # M32 ON
            write_res_on = self.plc_client.write_coil(PLC_COILS['DETECT_SIGNAL'], True)
            if write_res_on.isError():
                print("PLC 검출 신호 쓰기 오류 (ON)")
                return False
            # 잠시 대기 (필요한 경우)
            # time.sleep(0.05)
            # M32 OFF
            write_res_off = self.plc_client.write_coil(PLC_COILS['DETECT_SIGNAL'], False)
            if write_res_off.isError():
                print("PLC 검출 신호 쓰기 오류 (OFF)")
                return False # OFF 실패 시도 문제될 수 있음
            print("PLC 검출 신호 전송 완료")
            return True
        except ConnectionException:
            print("PLC 연결 끊김 감지 (검출 신호)")
            self.plc_connected = False
            self._update_plc_display()
            return False
        except Exception as e:
            print(f"PLC 검출 신호 전송 오류: {e}")
            logging.error(f"PLC 검출 신호 전송 오류: {traceback.format_exc()}")
            return False

    def _write_plc_coil(self, coil_address, value):
         """PLC 코일 쓰기"""
         if not self.plc_client.is_socket_open():
             print("PLC 연결 시도 중...")
             self._connect_plc()

         if not self.plc_connected:
             print("PLC 쓰기 실패: 연결되지 않음")
             return False

         try:
             result = self.plc_client.write_coil(coil_address, value)
             if result.isError():
                 print(f"PLC 코일 쓰기 오류 (주소: {coil_address}, 값: {value})")
                 return False
             # 성공 시 현재 상태 즉시 업데이트 (옵션)
             # self._read_plc_status()
             # self._update_plc_display()
             return True
         except ConnectionException:
             print("PLC 연결 끊김 감지 (쓰기)")
             self.plc_connected = False
             self._update_plc_display()
             return False
         except Exception as e:
             print(f"PLC 코일 쓰기 오류: {e}")
             logging.error(f"PLC 코일 쓰기 오류: {traceback.format_exc()}")
             return False

    # --- 카메라 및 처리 관련 메서드 ---
    def _grab_and_merge_images(self):
        """모든 카메라에서 이미지를 가져와 병합"""
        images = []
        grab_results = []
        if not self.cameras: return None

        try:
            for i, camera in enumerate(self.cameras):
                try:
                    grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    grab_results.append(grab_result)

                    if grab_result.GrabSucceeded():
                        img_converted = self.converter.Convert(grab_result)
                        img_array = img_converted.GetArray()
                        # 모델 입력 크기에 맞게 리사이즈
                        img_resized = cv2.resize(img_array, (DEFAULT_IMG_SIZE, DEFAULT_IMG_SIZE))
                        images.append(img_resized)
                    else:
                        print(f"카메라 {i} Grab 실패: {grab_result.GetErrorCode()} {grab_result.GetErrorDescription()}")
                        # 실패 시 빈 이미지 추가 또는 다른 처리
                        images.append(np.zeros((DEFAULT_IMG_SIZE, DEFAULT_IMG_SIZE, 3), dtype=np.uint8)) # BGR 형식 가정

                    grab_result.Release() # 중요: 결과 해제

                except pylon.TimeoutException:
                    print(f"카메라 {i} Grab 타임아웃")
                    logging.warning(f"카메라 {i} Grab 타임아웃")
                    images.append(np.zeros((DEFAULT_IMG_SIZE, DEFAULT_IMG_SIZE, 3), dtype=np.uint8))
                    continue # 다음 카메라로
                except Exception as e:
                    print(f"카메라 {i} Grab 중 오류: {e}")
                    logging.error(f"카메라 {i} Grab 오류: {traceback.format_exc()}")
                    images.append(np.zeros((DEFAULT_IMG_SIZE, DEFAULT_IMG_SIZE, 3), dtype=np.uint8))
                    continue # 다음 카메라로

            if not images:
                print("병합할 이미지가 없습니다.")
                return None

            # 이미지 병합 (util.merge 사용)
            # 채널 수 확인 (첫 번째 이미지만 확인)
            channel = 3 if len(images[0].shape) == 3 else 1 # 흑백 카메라 고려
            merged_img = imgmerge.merge(images, channel) # 병합 함수 확인 필요
            return merged_img

        except Exception as e:
            print(f"이미지 병합 중 오류: {e}")
            logging.error(f"이미지 병합 오류: {traceback.format_exc()}")
            return None

    def _adjust_camera_exposure(self):
        """카메라 밝기를 측정하고 노출 시간 조정"""
        if not self.cameras: return

        brightness_values = []
        print("노출 시간 조정을 위한 밝기 측정 시작...")
        try:
            for frame_count in range(EXPOSURE_CHECK_FRAMES):
                for i, camera in enumerate(self.cameras):
                    try:
                        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                        if grab_result.GrabSucceeded():
                            # 특정 프레임부터 밝기 계산
                            if frame_count >= EXPOSURE_CHECK_START_FRAME:
                                img_converted = self.converter.Convert(grab_result)
                                brightness = np.mean(img_converted.GetArray())
                                brightness_values.append(brightness)
                        grab_result.Release()
                    except pylon.TimeoutException:
                        print(f"노출 조정 중 카메라 {i} Grab 타임아웃")
                        continue # 다음 카메라
                    except Exception as grab_e:
                        print(f"노출 조정 중 카메라 {i} Grab 오류: {grab_e}")
                        continue # 다음 카메라
                # 약간의 딜레이 (필요시)
                # time.sleep(0.01)

            if not brightness_values:
                print("밝기 측정값 없음. 노출 시간 조정 건너뜀.")
                return

            mean_brightness = np.mean(brightness_values)
            print(f"평균 밝기: {mean_brightness:.2f}")

            new_exposure = None
            if mean_brightness > BRIGHTNESS_THRESHOLD_HIGH:
                new_exposure = EXPOSURE_HIGH
                print(f"밝기가 높아 노출 시간을 {new_exposure}으로 조정합니다.")
            elif mean_brightness < BRIGHTNESS_THRESHOLD_LOW:
                new_exposure = EXPOSURE_LOW
                print(f"밝기가 낮아 노출 시간을 {new_exposure}으로 조정합니다.")
            else:
                print("현재 밝기가 적절하여 노출 시간을 조정하지 않습니다.")

            if new_exposure is not None:
                for i, camera in enumerate(self.cameras):
                    try:
                        # 현재 노출 시간 확인 (옵션)
                        # current_exp = camera.ExposureTimeAbs.GetValue()
                        # print(f"카메라 {i} 현재 노출: {current_exp}, 새 노출: {new_exposure}")
                        camera.ExposureTimeAbs.SetValue(new_exposure)
                    except Exception as set_e:
                        print(f"카메라 {i} 노출 시간 설정 오류: {set_e}")
                        logging.warning(f"카메라 {i} 노출 시간({new_exposure}) 설정 오류: {traceback.format_exc()}")

        except Exception as e:
            print(f"노출 시간 조정 중 오류 발생: {e}")
            logging.error(f"노출 시간 조정 오류: {traceback.format_exc()}")


    def _run_detection(self, image):
        """주어진 이미지에 대해 YOLO 탐지 수행"""
        if self.model is None or image is None:
            return None, None # 모델 또는 이미지가 없으면 None 반환

        try:
            results = self.model.predict(image, save=False, imgsz=DEFAULT_IMG_SIZE, conf=self.confidence_threshold, half=True) # GPU 사용 시 half=True
            # 결과 분석 및 시각화
            annotated_frame = results[0].plot() # plot()은 시각화된 numpy 배열 반환
            return results[0], annotated_frame
        except Exception as e:
            print(f"YOLO 탐지 중 오류: {e}")
            logging.error(f"YOLO 탐지 오류: {traceback.format_exc()}")
            return None, image # 오류 시 원본 이미지 반환


    def _process_detection_result(self, result, original_image, annotated_image):
        """탐지 결과를 처리하고 필요한 동작 수행 (이미지 저장, DB 저장 등)"""
        current_time_ms = int(date_util.get_time_millisec()) # 마이크로초 대신 밀리초

        if result is None or not hasattr(result, 'boxes') or result.boxes.shape[0] == 0:
             # 탐지되지 않은 경우 (옵션: 일정 주기로 미탐지 이미지 저장)
             if current_time_ms - self.last_detection_time > 5000: # 예: 5초마다 저장
                 self._save_image_async(original_image, "notdetected/Original")
                 self.last_detection_time = current_time_ms # 마지막 저장 시간 업데이트
             return # 탐지된 객체 없음

        try:
            # 가장 높은 confidence 값 찾기
            confidences = result.boxes.conf.cpu().numpy() # CPU로 이동 후 numpy 배열로
            max_confidence = np.max(confidences) if len(confidences) > 0 else 0

            # 디버깅 로그
            # print(f"탐지됨: {result.boxes.shape[0]}개, 최대 Confidence: {max_confidence:.3f}")

            # 특정 Confidence 이상일 경우만 처리 및 저장
            if max_confidence >= MIN_SAVE_CONFIDENCE:
                # 중복 탐지 방지 로직 (시간 기반)
                # if current_time_ms - self.last_detection_time < 100: # 예: 100ms 이내 중복 방지
                #     print("짧은 시간 내 중복 탐지, 건너뜀")
                #     return

                self.last_detection_time = current_time_ms # 마지막 유효 탐지 시간 업데이트
                self.detection_count += 1
                print(f"결함 탐지 (Confidence: {max_confidence:.3f})! Count: {self.detection_count}")

                # --- PLC 및 DB 처리 ---
                serial_number = self._get_plc_serial_number() or "UNKNOWN_SN" # 시리얼 번호 읽기
                error_count_plc = self._get_plc_error_count() # PLC 에러 카운트 읽기
                # PLC 카운트가 유효하면 +1, 아니면 내부 카운트 사용 (혹은 다른 정책)
                current_error_index = error_count_plc + 1 if error_count_plc is not None else self.detection_count

                detection_time_str = date_util.get_time_millisec()[0:16] # 파일명용 시간
                detection_date_str = date_util.get_date_in_yyyymmdd()
                detection_time_int = int(date_util.get_time_in_mmddss()) # DB 저장용 시간

                # PLC로 검출 신호 전송
                self._send_plc_detection_signal()

                # 에러 발생 미터 읽기 (신호 전송 후)
                error_meter = self._get_plc_error_meter(current_error_index) or 0 # 실패 시 0

                # 이미지 저장 (비동기)
                img_path_box = self._save_image_async(annotated_image, f"{detection_date_str}/box", f"{detection_time_str}.jpg", apply_gamma=True)
                self._save_image_async(original_image, f"{detection_date_str}/Original", f"{detection_time_str}.jpg", apply_gamma=True)

                # DB 저장 (비동기) - 면적(area) 값 필요시 계산 로직 추가
                area_value = 0 # 임시값, 실제 면적 계산 필요
                self._save_detection_to_db_async(
                    self.product_start_time_str, # 제품 시작 시간 (mmddhhnnss)
                    serial_number,
                    current_error_index,
                    error_meter,
                    "defect", # 오류 유형
                    detection_time_int,
                    img_path_box, # 저장된 이미지 경로
                    area_value
                )

            # Confidence가 낮은 경우 (옵션: 별도 폴더에 저장)
            elif max_confidence > self.confidence_threshold: # 설정된 임계값은 넘지만 저장 기준 미만
                 print(f"낮은 Confidence 탐지 ({max_confidence:.3f}), 별도 저장")
                 detection_time_str = date_util.get_time_millisec()[0:16]
                 detection_date_str = date_util.get_date_in_yyyymmdd()
                 self._save_image_async(annotated_image, f"{detection_date_str}_under{int(MIN_SAVE_CONFIDENCE*100)}/box", f"{detection_time_str}.jpg", apply_gamma=True)
                 self._save_image_async(original_image, f"{detection_date_str}_under{int(MIN_SAVE_CONFIDENCE*100)}/Original", f"{detection_time_str}.jpg", apply_gamma=True)

        except Exception as e:
            print(f"탐지 결과 처리 중 오류: {e}")
            logging.error(f"탐지 결과 처리 오류: {traceback.format_exc()}")

    # --- 비동기 작업 (파일 저장, DB 저장) ---
    def _save_image_async(self, image, sub_folder, filename=None, apply_gamma=False):
        """이미지를 별도 스레드에서 저장"""
        if image is None: return None

        try:
            timestamp = filename if filename else f"{date_util.get_time_millisec()[0:16]}.jpg"
            save_dir = os.path.join(IMAGE_SAVE_BASE_PATH, sub_folder)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, timestamp)

            # 감마 보정 적용
            img_to_save = image.copy() # 원본 유지 위해 복사
            if apply_gamma:
                img_to_save = self._apply_gamma_correction(img_to_save, GAMMA_CORRECTION_VALUE)

            # 스레드로 저장 실행
            thread = threading.Thread(target=cv2.imwrite, args=(save_path, img_to_save))
            thread.start()
            # thread.join() # join하면 비동기가 아님! 필요시 완료 콜백 구조 사용
            return save_path # 저장 경로 반환
        except Exception as e:
            print(f"이미지 저장 스레드 생성/시작 오류: {e}")
            logging.error(f"이미지 저장 스레드 생성/시작 오류: {traceback.format_exc()}")
            return None

    def _save_detection_to_db_async(self, start_time, serial, err_idx, meter, type, detect_time, img_path, area):
        """탐지 정보를 별도 스레드에서 DB에 저장"""
        try:
            thread = threading.Thread(target=detect_db.write_sql, args=(
                start_time, serial, err_idx, meter, type, detect_time, img_path, area
            ))
            thread.start()
        except Exception as e:
            print(f"DB 저장 스레드 생성/시작 오류: {e}")
            logging.error(f"DB 저장 스레드 생성/시작 오류: {traceback.format_exc()}")

    def _save_start_info_to_db_async(self, start_time, area_base):
        """시작 정보를 별도 스레드에서 DB에 저장"""
        try:
            # start_db 모듈의 함수명 확인 필요 (write_sql3?)
            thread = threading.Thread(target=start_db.write_sql3, args=(start_time, area_base))
            thread.start()
        except Exception as e:
            print(f"시작 정보 DB 저장 스레드 생성/시작 오류: {e}")
            logging.error(f"시작 정보 DB 저장 스레드 생성/시작 오류: {traceback.format_exc()}")

    def _apply_gamma_correction(self, image, gamma):
        """이미지에 감마 보정 적용"""
        try:
            lookUpTable = np.empty((1, 256), np.uint8)
            invGamma = 1.0 / gamma
            for i in range(256):
                lookUpTable[0, i] = np.clip(pow(i / 255.0, invGamma) * 255.0, 0, 255)
            return cv2.LUT(image, lookUpTable)
        except Exception as e:
            print(f"감마 보정 적용 오류: {e}")
            logging.warning(f"감마 보정 적용 오류: {traceback.format_exc()}")
            return image # 오류 시 원본 반환

    # --- 스레드 관리 및 메인 루프 ---
    def _camera_loop(self):
        """카메라 프레임 읽기, 처리 및 UI 업데이트 요청 루프 (별도 스레드에서 실행)"""
        last_status_check_time = time.time()

        while not self.stop_event.is_set():
            start_time = time.perf_counter() # 성능 측정 시작

            if not self.is_running: # 일시정지 상태
                # 일시정지 중에도 카메라는 보여주기 (옵션)
                merged_image = self._grab_and_merge_images()
                if merged_image is not None:
                    # UI 업데이트 큐에 넣기
                    self.ui_queue.put({"type": "image", "data": merged_image})
                time.sleep(0.1) # CPU 사용량 줄이기
                continue

            # --- 검사 실행 중 ---
            # PLC 상태 변경 확인 (메인 루프에서 주기적으로 확인하므로 여기서는 생략 가능)
            # self._check_plc_status_change() # 필요시 로직 추가

            # 이미지 가져오기 및 병합
            merged_image = self._grab_and_merge_images()
            if merged_image is None:
                time.sleep(0.1) # 이미지 가져오기 실패 시 잠시 대기
                continue

            # YOLO 탐지 수행
            detection_result, annotated_frame = self._run_detection(merged_image)

            # 탐지 결과 처리
            self._process_detection_result(detection_result, merged_image, annotated_frame)

            # 처리 시간 계산
            end_time = time.perf_counter()
            proc_time_ms = (end_time - start_time) * 1000

            # UI 업데이트 큐에 결과 넣기
            # 시각화된 이미지를 UI에 표시
            ui_image = annotated_frame if annotated_frame is not None else merged_image
            self.ui_queue.put({"type": "image", "data": ui_image})
            self.ui_queue.put({"type": "speed", "data": proc_time_ms})

            # 루프 지연 시간 계산 (목표 FPS 유지 등) - 필요시 추가
            # time.sleep(max(0, (1/TARGET_FPS) - (end_time - start_time)))

        print("카메라 루프 종료.")


    def _plc_polling_loop(self):
        """주기적으로 PLC 상태를 읽고 변경 사항을 UI 큐에 넣는 루프"""
        while not self.stop_event.is_set():
            status_read_success = self._read_plc_status()

            if status_read_success:
                # 상태 변경 여부 확인 (옵션: 변경 시에만 큐에 넣기)
                # if self.current_plc_status != self.last_plc_status:
                self.ui_queue.put({"type": "plc_status", "data": self.current_plc_status.copy()})
                # self.last_plc_status = self.current_plc_status.copy() # 마지막 상태 업데이트

                # --- PLC 상태 기반 로직 처리 ---
                # 예: M53/M54 상태 변경 시 제품 시작 처리
                self._handle_plc_start_condition()

            # 폴링 간격만큼 대기
            self.stop_event.wait(PLC_POLL_INTERVAL_MS / 1000.0) # 초 단위로 변환

        print("PLC 폴링 루프 종료.")

    def _handle_plc_start_condition(self):
        """PLC 상태(M53, M54) 변경에 따른 시작 조건 처리"""
        m53 = self.current_plc_status.get('m53')
        m54 = self.current_plc_status.get('m54')
        last_m53 = self.last_plc_status.get('m53')
        last_m54 = self.last_plc_status.get('m54')

        # 상태가 유효하고, 이전 상태와 다를 때만 처리
        if m53 is not None and m54 is not None and \
           (m53 != last_m53 or m54 != last_m54):

            print(f"PLC 시작 조건 변경 감지: M53={m53}, M54={m54} (이전: {last_m53}, {last_m54})")

            # 시작 조건: (M53=True, M54=False) 또는 (M53=False, M54=True) -> 이 로직이 맞는지 확인 필요
            # 원본 코드의 조건: not((m53m == m53) & (m54m == m54))
            is_new_start = True # 위 조건은 항상 변경 시 True가 됨, 구체적인 시작 조건 명시 필요

            if is_new_start:
                print("새로운 작업 시작 조건 감지됨.")
                self.detection_count = 0 # 감지 카운트 초기화

                # 면적 DB 관련 폴더 생성 (실제 사용 여부 확인 필요)
                # area_path = os.path.join(AREA_DB_BASE_PATH, date_util.get_date_in_yyyymm(), date_util.get_date_in_yyyymmdd())
                # os.makedirs(area_path, exist_ok=True)

                # PLC에서 시작 시간 읽기
                start_time = self._get_plc_start_time()
                if start_time:
                    self.product_start_time_str = start_time
                    print(f"제품 시작 시간 읽음: {self.product_start_time_str}")

                    # 노출 시간 조정 실행
                    self._adjust_camera_exposure() # 별도 스레드로 실행 고려

                    # 면적 기준값 계산/설정 (별도 로직 필요)
                    # self.cable_area_base = self._calculate_area_base()
                    # print(f"케이블 면적 기준값 설정: {self.cable_area_base}")

                    # DB에 시작 정보 저장 (비동기)
                    self._save_start_info_to_db_async(self.product_start_time_str, self.cable_area_base)
                else:
                    print("PLC에서 시작 시간을 읽을 수 없어 DB 저장을 건너<0xEB><0x9B><0x9C>니다.")

                # UI 업데이트 (검사 상태 등)
                self.ui_queue.put({"type": "status_update"})

            # 현재 상태를 마지막 상태로 업데이트 (루프 마지막에서 처리하는 것이 더 안전할 수 있음)
            self.last_plc_status = self.current_plc_status.copy()


    def _process_ui_queue(self):
        """UI 큐를 확인하고 메인 스레드에서 UI 업데이트 수행"""
        try:
            while not self.ui_queue.empty():
                message = self.ui_queue.get_nowait()
                msg_type = message.get("type")
                msg_data = message.get("data")

                if msg_type == "image":
                    self._update_image_display(msg_data)
                elif msg_type == "speed":
                    self._update_speed_display(msg_data)
                elif msg_type == "plc_status":
                    # self.current_plc_status = msg_data # 직접 업데이트보다는 표시만
                    self._update_plc_display() # UI 표시 함수 호출
                elif msg_type == "status_update":
                    self._update_ui_status_labels() # 일반 상태 라벨 업데이트
                # 다른 메시지 유형 추가 가능 (e.g., 에러 메시지 표시)

        except queue.Empty:
            pass # 큐가 비어있으면 아무것도 안 함
        except Exception as e:
            print(f"UI 큐 처리 중 오류: {e}")
            logging.error(f"UI 큐 처리 오류: {traceback.format_exc()}")
        finally:
            # 다음 업데이트 예약
            self.root.after(UI_UPDATE_INTERVAL_MS, self._process_ui_queue)

    def _start_plc_polling(self):
        """PLC 폴링 스레드 시작"""
        if self.plc_thread is None or not self.plc_thread.is_alive():
            self.plc_thread = threading.Thread(target=self._plc_polling_loop, daemon=True)
            self.plc_thread.start()
            print("PLC 폴링 스레드 시작됨.")

    def _stop_threads(self):
        """모든 백그라운드 스레드 중지 요청"""
        print("스레드 중지 요청...")
        self.stop_event.set()

        if self.camera_thread and self.camera_thread.is_alive():
            print("카메라 스레드 종료 대기 중...")
            self.camera_thread.join(timeout=THREAD_STOP_TIMEOUT)
            if self.camera_thread.is_alive():
                print("카메라 스레드 종료 시간 초과!")

        if self.plc_thread and self.plc_thread.is_alive():
            print("PLC 스레드 종료 대기 중...")
            self.plc_thread.join(timeout=THREAD_STOP_TIMEOUT)
            if self.plc_thread.is_alive():
                 print("PLC 스레드 종료 시간 초과!")

        print("모든 스레드 중지 완료 (또는 시간 초과).")


    # --- UI 이벤트 핸들러 ---
    def start_inspection(self):
        """검사 시작/재개 버튼 클릭"""
        if not self.is_running:
            self.is_running = True
            self._update_ui_status_labels()
            print("검사 시작/재개")

            # 카메라 스레드가 없으면 시작
            if self.camera_thread is None or not self.camera_thread.is_alive():
                self.stop_event.clear() # 중지 이벤트 초기화
                self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
                self.camera_thread.start()
                print("카메라 처리 스레드 시작됨.")

    def pause_inspection(self):
        """일시 정지 버튼 클릭"""
        if self.is_running:
            self.is_running = False
            self._update_ui_status_labels()
            print("검사 일시 정지")
            # 카메라 스레드는 계속 실행하여 화면은 보여줄 수 있음 (is_running 플래그로 제어)

    def change_confidence(self):
        """Confidence 변경 버튼 클릭"""
        try:
            new_conf = float(self.ui_vars['confidence_entry'].get())
            if 0.0 <= new_conf <= 1.0:
                self.confidence_threshold = new_conf
                self.ui_vars['current_confidence'].set(f"{self.confidence_threshold:.2f}")
                print(f"Confidence 임계값 변경됨: {self.confidence_threshold}")
            else:
                messagebox.showwarning("입력 오류", "Confidence 값은 0.0과 1.0 사이여야 합니다.")
        except ValueError:
            messagebox.showwarning("입력 오류", "Confidence 값은 숫자여야 합니다.")
        except Exception as e:
             messagebox.showerror("오류", f"Confidence 변경 중 오류:\n{e}")

    def reset_confidence(self):
        """Confidence 기본값 버튼 클릭"""
        self.confidence_threshold = DEFAULT_CONFIDENCE
        self.ui_vars['confidence_entry'].set(f"{self.confidence_threshold:.2f}")
        self.ui_vars['current_confidence'].set(f"{self.confidence_threshold:.2f}")
        print(f"Confidence 임계값 기본값으로 재설정: {self.confidence_threshold}")

    def manual_start_button(self):
        """수동 Start 버튼 클릭 (M1 토글)"""
        print("수동 Start 버튼 클릭")
        current_m1 = self.current_plc_status.get('m01')
        if current_m1 is not None:
            self._write_plc_coil(PLC_COILS['START_STOP'], not current_m1)
        else:
            print("현재 M1 상태를 알 수 없어 실행할 수 없습니다.")
            # 필요시 강제로 On 또는 Off 시키는 로직 추가 가능
            # self._write_plc_coil(PLC_COILS['START_STOP'], True)

    def manual_reset_button(self):
        """수동 리셋 버튼 클릭 (M1, M53, M54 -> OFF)"""
        print("수동 리셋 버튼 클릭")
        # 순차적으로 OFF 시도
        self._write_plc_coil(PLC_COILS['START_STOP'], False)
        self._write_plc_coil(PLC_COILS['STATUS_1'], False)
        self._write_plc_coil(PLC_COILS['STATUS_2'], False)
        # UI 상태 업데이트 요청
        self.ui_queue.put({"type": "status_update"})
        print("수동 리셋 완료 (PLC 응답 확인 필요).")

    def reset_area_base(self):
         """면적 기준값 초기화 (구현 필요)"""
         print("면적 기준값 초기화 기능 구현 필요")
         # 1. 현재 프레임에서 케이블 영역 추출
         # 2. 해당 영역의 면적 계산
         # 3. self.cable_area_base 업데이트
         # 4. UI 업데이트
         messagebox.showinfo("알림", "면적 기준값 초기화 기능은 아직 구현되지 않았습니다.")


    # --- 자원 해제 ---
    def release_resources(self):
        """카메라, PLC 등 자원 해제"""
        print("자원 해제 시작...")
        # 스레드 중지
        self._stop_threads()

        # 카메라 해제
        if self.cameras:
            for i, camera in enumerate(self.cameras):
                try:
                    if camera.IsGrabbing():
                        camera.StopGrabbing()
                    if camera.IsOpen():
                        camera.Close()
                    print(f"카메라 {i} 해제 완료.")
                except Exception as e:
                    print(f"카메라 {i} 해제 중 오류: {e}")
                    logging.error(f"카메라 {i} 해제 오류: {traceback.format_exc()}")
            self.cameras = []

        # PLC 연결 해제
        if self.plc_client and self.plc_client.is_socket_open():
            try:
                self.plc_client.close()
                print("PLC 연결 해제 완료.")
            except Exception as e:
                print(f"PLC 연결 해제 중 오류: {e}")
                logging.error(f"PLC 연결 해제 오류: {traceback.format_exc()}")

        # OpenCV 창 닫기 (필요시)
        cv2.destroyAllWindows()
        print("자원 해제 완료.")

    def on_closing(self):
        """창 닫기 버튼 클릭 시"""
        if messagebox.askokcancel("종료 확인", "프로그램을 종료하시겠습니까?"):
            self.release_resources()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()