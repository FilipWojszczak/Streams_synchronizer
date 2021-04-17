import cv2
import sys
import os
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
        self.gui_state = "STOP"
        self.use_buffer = False
        self.videos = [Video(source, max_bfr_size, min_start_bfr_size) for source in source_list]
        self.is_displaying = [False for source in source_list]
        self.min_start_bfr_size = min_start_bfr_size
        self.capture_errors = [0 for source in source_list]
        self.check_state()
        self.videos_threads = []
        for index, video in enumerate(self.videos):
            self.videos_threads.append(threading.Thread(target=self.handle_video, args=(index,)))
            self.videos_threads[-1].daemon = True
            self.videos_threads[-1].start()

    def check_state(self):
        for video in self.videos:
            video.state = self.gui.state
        self.gui_state = self.gui.state
        if self.gui_state == "STOP":
            self.use_buffer = False
        self.gui.window.after(1, self.check_state)

    def handle_video(self, index):
        while True:
            self.videos[index].capture()
            if index == len(self.videos) - 1:
                len_frames_list = [self.videos[a].get_frames_list_size() for a in range(len(self.videos))]
                print(len_frames_list)
            if self.gui_state == "PLAY":
                if self.check_all_buffers():
                    try:
                        processed_frame = self.videos[index].get_processed_frame()
                        self.gui.add_frame(index, processed_frame)
                        self.check_buffer_difference(index)
                        self.is_displaying[index] = True
                        self.capture_errors[index] = 0
                    except IndexError:
                        pass
                        # self.capture_errors[index] += 1
                        # if self.capture_errors[index] >= self.min_start_bfr_size:
                        #     print("use buffer")
                        #     self.use_buffer = True
                else:
                    self.is_displaying[index] = False
                    # self.capture_errors[index] += 1
                    # if self.capture_errors[index] >= self.min_start_bfr_size * 2:
                    #     print("use buffer")
                    #     self.use_buffer = True
            # if index == 0:
            # print(self.videos[0].get_frames_list_size(), self.videos[1].get_frames_list_size())

    def check_buffer_difference(self, index):
        if self.min_start_bfr_size > 30 and self.check_is_displaying():
            min_list = min([v.get_frames_list_size() for v in self.videos])
            diff = self.videos[index].get_frames_list_size() - min_list
            if diff > 30:
                print("diff", index)
                self.videos[index].delete_frames(diff - 1)

    def check_is_displaying(self):
        result = True
        for element in self.is_displaying:
            if not element:
                result = False
                break
        return result

    def check_all_buffers(self):
        result = True
        for video in self.videos:
            if not video.buffer_ready:
                result = False
                break
        return result

    def display_GUI(self):
        self.gui.window.mainloop()

    # def adjust_frame_size(self, image, old_size):
    #     # try:
    #     ratio = old_size[0] // old_size[1]
    #     if self.gui.default_size[0] > self.gui.default_size[1] \
    #             or (self.gui.default_size[0] == self.gui.default_size[1] and old_size[0] < old_size[1]):
    #         return image.resize((self.gui.default_size[1] * ratio, self.gui.default_size[1]))
    #     elif self.gui.default_size[0] < self.gui.default_size[1] \
    #             or (self.gui.default_size[0] == self.gui.default_size[1] and old_size[0] > old_size[1]):
    #         return image.resize((self.gui.default_size[0], self.gui.default_size[0] // ratio))
    #     # except:
    #     #     return image.resize((320, 240))


class Video:
    def __init__(self, name, max_bfr_frms, min_bfr_frms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.min_bfr_frms = min_bfr_frms
        self.max_bfr_frms = max_bfr_frms
        self.buffer_ready = False
        self.cap = cv2.VideoCapture(self.name)
        self.frame_size = self.measure_frame_size()
        self.state = "STOP"
        self.frames_list = []
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.last_frame_timestamp = datetime.now()

    def __del__(self):
        self.cap.release()

    def measure_frame_size(self):
        ret = False
        while not ret:
            ret, frame = self.cap.read()
            frame_size = sys.getsizeof(frame)
            return frame_size

    def capture(self):
        ret, frame = self.cap.read()
        # if self.name == "http://178.8.150.125:80/mjpg/video.mjpg":
        #     print(self.name, self.fps)
        if not ret:
            pass
            # break
            # self.cap.release()
            self.cap = cv2.VideoCapture(self.name)
        else:
            if (len(self.frames_list) > self.max_bfr_frms and self.state == "PLAY") or self.state == "STOP":
                try:
                    self.frames_list.pop(0)
                except IndexError:
                    pass
            if self.state != "STOP":
                self.frames_list.append(frame)
            else:
                self.frames_list.clear()
                self.buffer_ready = False

            if not self.buffer_ready:
                if self.get_frames_list_size() >= self.min_bfr_frms:
                    self.buffer_ready = True

    def get_frame(self):
        return self.frames_list.pop(0)

    def delete_frames(self, amount):
        del self.frames_list[:amount]

    def get_frames_list_size(self):
        return len(self.frames_list)

    def get_processed_frame(self):
        frame_to_display = self.get_frame()
        img_tk = self.process_image(frame_to_display)
        return img_tk

    def process_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCV treat images as having BGR layers, Pillow as RGB
        image = Image.fromarray(image)
        # image = self.adjust_frame_size(image, image.size)
        image = image.resize((320, 240))
        return ImageTk.PhotoImage(image=image)

    def update_last_frame_timestamp(self, new_timestamp):
        self.last_frame_timestamp = new_timestamp


class GUI:
    def __init__(self, cameras_number):
        self.default_size = (320, 240)
        self.state = "STOP"
        self.window = tk.Tk()
        self.window.wm_title("Synchronizer")

        self.videos_frames = []
        self.videos_area = []
        for cam_nr in range(cameras_number):
            if cam_nr % 5 == 0:
                self.videos_frames.append(tk.Frame(self.window))
                self.videos_frames[-1].pack(expand=tk.YES, fill=tk.BOTH)
            self.videos_area.append(tk.Label(self.videos_frames[-1]))
            self.videos_area[-1].pack(expand=tk.YES, side=tk.LEFT, fill=tk.BOTH)

        self.blank_videos_places = 0
        if cameras_number > 5 and cameras_number % 5 != 0:
            self.blank_videos_places = 5 - (cameras_number % 5)
            for i in range(self.blank_videos_places):
                self.videos_area.append(tk.Label(self.videos_frames[-1]))
                self.videos_area[-1].pack(expand=tk.YES, side=tk.LEFT, fill=tk.BOTH)

        image = Image.new("RGB", self.default_size, (0, 0, 0))
        image = ImageTk.PhotoImage(image=image)
        for i, area in enumerate(self.videos_area):
            self.add_frame(i, image)

        self.buttons_frame = tk.Frame(self.window, pady=5)
        self.buttons_frame.pack(fill=tk.BOTH)
        self.play_button = tk.Button(self.buttons_frame, text="Play", command=self.on_play)
        self.pause_button = tk.Button(self.buttons_frame, text="Pause", command=self.on_pause)
        self.stop_button = tk.Button(self.buttons_frame, text="Stop", command=self.on_stop)
        self.play_button.pack(expand=tk.YES, side=tk.LEFT)
        self.pause_button.pack(expand=tk.YES, side=tk.LEFT)
        self.stop_button.pack(expand=tk.YES, side=tk.LEFT)

        self.window.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        self.default_size = (self.videos_area[0].winfo_width(), self.videos_area[0].winfo_height())

        # image = Image.new("RGB", (self.default_size[0] - 2, self.default_size[1] - 2), (0, 0, 0))
        # image = ImageTk.PhotoImage(image=image)
        # for i, area in enumerate(self.videos_area):
        #     self.add_frame(i, image)

    def on_play(self):
        self.state = "PLAY"

    def on_pause(self):
        self.state = "PAUSE"

    def on_stop(self):
        self.state = "STOP"

    def add_frame(self, index, img_tk):
        self.videos_area[index].configure(image=img_tk)
        self.videos_area[index].imgtk = img_tk


cameras = [
    "http://213.184.127.123:82/mjpg/video.mjpg",
    "http://178.8.150.125:80/mjpg/video.mjpg",
    "http://90.146.10.190:80/mjpg/video.mjpg",
    "http://92.220.173.101:80/mjpg/video.mjpg",
    "http://82.77.203.219:8080/cgi-bin/faststream.jpg?stream=half&fps=15&rand=COUNTER",
    "http://174.6.126.86:80/mjpg/video.mjpg",
    "http://46.35.192.141:80/mjpg/video.mjpg",
    "http://81.8.160.235:80/mjpg/video.mjpg",
    "http://194.68.122.244:83/mjpg/video.mjpg",
    "http://94.72.19.58:80/mjpg/video.mjpg",
    "http://217.92.73.116:80/mjpg/video.mjpg",
    "http://194.66.34.9:80/mjpg/video.mjpg",
    "http://107.0.231.40:8082/mjpg/video.mjpg",
    "http://89.231.23.159:8081/image?speed=0",
    "http://109.206.96.247:8080/cam_1.cgi"

    # "http://192.168.0.105:8080/video",
    # "rtsp://192.168.0.104:8080/h264_pcm.sdp",
    # "rtsp://192.168.0.102:8080/h264_pcm.sdp",
    # "http://192.168.0.102:8080/video",
    # "http://192.168.0.104:8080/video",
    # 0
]
scheduler = Scheduler(cameras, 1000, 50)
scheduler.display_GUI()
