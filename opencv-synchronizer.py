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
                # if index == 0:
                #     print(len(self.videos[index].frames_list))
                frame_to_display = cv2.cvtColor(frame_to_display, cv2.COLOR_BGR2RGB) # OpenCV treat images as having BGR layers, Pillow as RGB
                img = Image.fromarray(frame_to_display)
                # img = self.adjust_frame_size(img, img.size)
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

    def adjust_frame_size(self, image, old_size):
        # try:
        ratio = old_size[0] // old_size[1]
        if self.gui.default_size[0] > self.gui.default_size[1]\
                or (self.gui.default_size[0] == self.gui.default_size[1] and old_size[0] < old_size[1]):
            return image.resize((self.gui.default_size[1] * ratio, self.gui.default_size[1]))
        elif self.gui.default_size[0] < self.gui.default_size[1]\
                or (self.gui.default_size[0] == self.gui.default_size[1] and old_size[0] > old_size[1]):
            return image.resize((self.gui.default_size[0], self.gui.default_size[0] // ratio))
        # except:
        #     return image.resize((320, 240))


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
        self.default_size = (320, 240)
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

        # self.videos_frame = tk.Frame(self.window)
        # self.videos_frame.pack(expand=tk.YES)
        # # self.videos_frame.grid(row=0, column=0)
        #
        # self.videos_area = []
        # for row in range(((cameras_number - 1) // 3) + 1):
        #     for column in range(3):
        #         self.videos_area.append(tk.Label(self.videos_frame))
        #         self.videos_area[-1].grid(row=row, column=column, padx=2, pady=2)

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
        print(self.videos_area[0].winfo_width(), self.videos_area[0].winfo_height())
        print(self.videos_area[3].winfo_width(), self.videos_area[3].winfo_height())
        # print(self.buttons_frame.winfo_width(), self.buttons_frame.winfo_height())

    def on_pause(self):
        pass

    def on_stop(self):
        pass

    def add_frame(self, index, imgtk):
        self.videos_area[index].imgtk = imgtk
        self.videos_area[index].configure(image=imgtk)


# cap = Video("http://192.168.0.100:8080/video", 10)
cameras = [
           "http://192.168.0.101:8080/video",
           # "rtsp://192.168.0.104:8080/h264_pcm.sdp",
           # "rtsp://192.168.0.102:8080/h264_pcm.sdp",
           "http://192.168.0.102:8080/video",
           "http://192.168.0.104:8080/video",
           0
           ]
scheduler = Scheduler(cameras, 100, 50)
scheduler.play_all()
scheduler.display_GUI()
