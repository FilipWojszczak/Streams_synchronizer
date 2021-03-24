import cv2
import queue
import time
import threading
from datetime import datetime
from datetime import timedelta
import tkinter as tk
from PIL import Image, ImageTk


class Scheduler:
    def __init__(self, source_list, max_bfr_size, min_start_bfr_size):
        self.gui = GUI(len(source_list))
        self.min_start_bfr_size = min_start_bfr_size
        self.videos = [Video(source, max_bfr_size, min_start_bfr_size) for source in source_list]
        self.playing_state = False
        self.capture_errors = [0 for source in source_list]

    def play(self, index):
        if self.playing_state or self.check_all_buffers():
            self.playing_state = True
            try:
                frame_to_display = self.videos[index].get_frame()
                # if index == 1:
                #     print(len(self.videos[index].frames_list))
                frame_to_display = cv2.cvtColor(frame_to_display, cv2.COLOR_BGR2RGB) # OpenCV treat images as having BGR layers, Pillow as RGB
                img = Image.fromarray(frame_to_display)
                img = img.resize((320, 240))
                imgtk = ImageTk.PhotoImage(image=img)
                self.gui.add_frame(index, imgtk)
                self.capture_errors[index] = 0
                # cv2.imshow("window" + str(i), frame_to_display)
            except IndexError:
                self.capture_errors[index] += 1
                if self.capture_errors[index] >= 50:
                    self.playing_state = False
        self.gui.videos_area[0].after(10, self.play, index)

    def play_all(self):
        for i in range(len(self.videos)):
            self.play(i)

    def check_all_buffers(self):
        result = True
        for video in self.videos:
            if video.get_frames_list_size() <= self.min_start_bfr_size:
                result = False
                break
        return result

    def display_GUI(self):
        self.gui.window.mainloop()


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
                pass
                # break
                # self.cap.release()
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

    def get_frames_list_size(self):
        return len(self.frames_list)


class GUI:
    def __init__(self, cameras_number):
        self.window = tk.Tk()
        self.window.wm_title("Synchronizer")

        self.videos_frame = tk.Frame(self.window, width=600, height=500)
        self.videos_frame.grid(row=0, column=0)

        self.videos_area = []
        for row in range(((cameras_number - 1) // 3) + 1):
            for column in range(3):
                self.videos_area.append(tk.Label(self.videos_frame))
                self.videos_area[-1].grid(row=row, column=column, padx=2, pady=2)

    def add_frame(self, index, imgtk):
        self.videos_area[index].imgtk = imgtk
        self.videos_area[index].configure(image=imgtk)


# cap = Video("http://192.168.0.100:8080/video", 10)
cameras = [
           # "http://192.168.0.100:8080/video",
           "http://192.168.0.102:8080/video",
           "http://192.168.0.104:8080/video",
           # 0
           ]
scheduler = Scheduler(cameras, 100, 50)
scheduler.play_all()
scheduler.display_GUI()
