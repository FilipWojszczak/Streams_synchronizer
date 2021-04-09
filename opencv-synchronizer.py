import cv2
import sys
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
        self.gui.window.after(1, self.check_state)

    def handle_video(self, index):
        while True:
            self.videos[index].capture()
            if self.gui_state == "PLAY"\
                    and (self.videos[index].get_frames_list_size() >= self.min_start_bfr_size or self.use_buffer):
                try:
                    processed_frame = self.videos[index].get_processed_frame()
                    self.gui.add_frame(index, processed_frame)
                    self.capture_errors[index] = 0
                except IndexError:
                    print("indexerror")
                    self.capture_errors[index] += 1
                    if self.capture_errors[index] >= 50:
                        print("ready=false", index)
                        self.use_buffer = False
            # if index == 0:
            # print(self.videos[0].get_frames_list_size(), self.videos[1].get_frames_list_size())

    # def check_buffer_difference(self, index):
    #     min_list = min([v.get_frames_list_size() for v in self.videos])
    #     diff = self.videos[index].get_frames_list_size() - min_list
    #     if diff > self.min_start_bfr_size / 2:
    #         self.videos[index].delete_frames(diff - 1)

    # def check_all_buffers(self):
    #     result = True
    #     for video in self.videos:
    #         if video.get_frames_list_size() <= self.min_start_bfr_size:
    #             result = False
    #             break
    #     return result

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


class Video(cv2.VideoCapture):
    def __init__(self, name, max_bfr_frms, min_bfr_frms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.min_bfr_frms = min_bfr_frms
        self.max_bfr_frms = max_bfr_frms
        self.cap = cv2.VideoCapture(self.name)
        self.state = "STOP"
        self.frames_list = []
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.last_frame_timestamp = datetime.now()
        # self.thread = threading.Thread(target=self.capture, args=(max_bfr_frms,))
        # self.thread.daemon = True
        # self.thread.start()

    def __del__(self):
        self.cap.release()

    def capture(self):
        # if self.name == "http://213.184.127.123:82/mjpg/video.mjpg":
        #     print(self.name, self.fps)
        ret, frame = self.cap.read()
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
            if cam_nr % 3 == 0:
                self.videos_frames.append(tk.Frame(self.window))
                self.videos_frames[-1].pack(expand=tk.YES, fill=tk.BOTH)
            self.videos_area.append(tk.Label(self.videos_frames[-1]))
            self.videos_area[-1].pack(expand=tk.YES, side=tk.LEFT, fill=tk.BOTH)

        self.blank_videos_places = 0
        if cameras_number > 3 and cameras_number % 3 != 0:
            self.blank_videos_places = 3 - (cameras_number % 3)
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
        # print(self.videos_area[0].winfo_width(), self.videos_area[0].winfo_height())
        # print(self.videos_area[3].winfo_width(), self.videos_area[3].winfo_height())
        # print(self.buttons_frame.winfo_width(), self.buttons_frame.winfo_height())

    def on_pause(self):
        self.state = "PAUSE"

    def on_stop(self):
        self.state = "STOP"

    def add_frame(self, index, img_tk):
        self.videos_area[index].imgtk = img_tk
        self.videos_area[index].configure(image=img_tk)


cameras = [
    # "http://192.168.0.101:8080/video",
    # "rtsp://192.168.0.104:8080/h264_pcm.sdp",
    # "rtsp://192.168.0.102:8080/h264_pcm.sdp",
    "http://213.184.127.123:82/mjpg/video.mjpg",
    "http://192.168.0.102:8080/video",
    # "http://192.168.0.104:8080/video",
    # 0
]
scheduler = Scheduler(cameras, 1000, 50)
scheduler.display_GUI()
