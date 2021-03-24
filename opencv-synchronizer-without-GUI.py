import cv2
import queue
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk


class Scheduler:
    def __init__(self, source_list, max_bfr_size):
        self.videos = [Video(source, max_bfr_size) for source in source_list]
        for i in range(len(source_list)):
            cv2.namedWindow("window" + str(i), cv2.WINDOW_NORMAL)
            row = 0
            if i <= 2:
                row = 0
            elif i <= 5:
                row = 1
            else:
                row = 2
            cv2.moveWindow("window" + str(i),
                           (i % 3) * cv2.getWindowImageRect("window" + str(i))[2],
                           row * cv2.getWindowImageRect("window" + str(i))[3])

    def play(self):
        while True:
            for i, video in enumerate(self.videos):
                try:
                    frame_to_display = video.get_frame()
                    cv2.imshow("window" + str(i), frame_to_display)
                except IndexError:
                    pass
                if chr(cv2.waitKey(1) & 255) == 'q':
                    break


class Video(cv2.VideoCapture):
    def __init__(self, name, max_bfr_frms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.cap = cv2.VideoCapture(self.name)
        self.frames_list = []
        self.thread = threading.Thread(target=self._capture, args=(max_bfr_frms,))
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.cap.release()

    def _capture(self, max_buffer_frames):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                # break
                self.cap = cv2.VideoCapture(self.name)
            else:
                if len(self.frames_list) > max_buffer_frames:
                    try:
                        self.frames_list.pop(0)
                    except IndexError:
                        pass
                self.frames_list.append(frame)

    def get_frame(self):
        return self.frames_list.pop(0)


cameras = [0,
           "http://192.168.0.104:8080/video",
           "http://192.168.0.102:8080/video"
           ]
scheduler = Scheduler(cameras, 10)
scheduler.play()