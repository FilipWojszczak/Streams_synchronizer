#!/usr/bin/env python3
import gi
import time

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, GLib, GObject, Gtk

Gst.init(None)
Gst.init_check(None)


class Scheduler:
    def __init__(self, uri_list):
        self.uri_list = uri_list
        self.videos = Videos(self.uri_list)
        self.gui = GUI(self.videos)

    def start_videos_buffering(self):
        self.videos.play()

    def start_working(self):
        self.gui.window.show_all()
        Gtk.main()

    def play_all(self):
        pass

    def pause_all(self):
        pass

    def stop_all(self):
        pass


class Videos:
    def __init__(self, uri_list):
        self.uri_list = uri_list
        self.pipeline = Gst.Pipeline().new()
        self.pipeline.set_property("async-handling", True)
        self.sources = []
        self.vconverts = []
        self.queues = []
        self.gtksinks = []
        self.multiqueue = Gst.ElementFactory.make("multiqueue", "multiqueue")
        self.pipeline.add(self.multiqueue)
        self.multiqueue.set_property('sync-by-running-time', True)
        self.multiqueue.connect("pad-added", self.on_multiqueue_pad_added)

        for index, uri in enumerate(self.uri_list):
            source_string = "source" + str(index + 1)
            vconvert_string = "vconvert" + str(index + 1)
            gtksink_string = "sink" + str(index + 1)
            queue_string = "queue" + str(index + 1)
            self.sources.append(Gst.ElementFactory.make("uridecodebin", source_string))
            self.vconverts.append(Gst.ElementFactory.make("videoconvert", vconvert_string))
            self.queues.append(Gst.ElementFactory.make("queue", queue_string))
            self.gtksinks.append(Gst.ElementFactory.make("gtksink", gtksink_string))

            self.pipeline.add(self.sources[index])
            self.pipeline.add(self.vconverts[index])
            self.pipeline.add(self.queues[index])
            self.pipeline.add(self.gtksinks[index])

        for index, uri in enumerate(self.uri_list):
            self.sources[index].connect("pad-added", self.on_source_pad_added)
            self.sources[index].set_property('uri', uri)
            # self.queues[index].set_property('max-size-buffers', 0)
            self.queues[index].set_property('max-size-bytes', 0)
            # self.queues[index].set_property('max-size-time', 0)
            # self.queues[index].set_property('min-threshold-buffers', 0)
            self.queues[index].set_property('min-threshold-bytes', 200485760)
            # self.queues[index].set_property('min-threshold-time', 10000000000)

            self.vconverts[index].link(self.queues[index])
            queue_pad = self.queues[index].get_static_pad("src")
            multiqueue_pad = self.multiqueue.request_pad(self.multiqueue.get_pad_template("sink_%u"), None, None)
            queue_pad.link(multiqueue_pad)

    def play(self):
        for queue in self.queues:
            queue.set_state(Gst.State.PLAYING)
        self.multiqueue.set_state(Gst.State.PLAYING)
        for gtksink in self.gtksinks:
            gtksink.set_state(Gst.State.PLAYING)

        for i in range(len(self.uri_list)):
            time.sleep(3)
            self.vconverts[i].set_state(Gst.State.PLAYING)
            self.sources[i].set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def stop(self):
        self.pipeline.set_state(Gst.State.READY)

    def on_source_pad_added(self, src, new_pad):
        for index, source in enumerate(self.sources):
            print(index)
            # for i in range(new_pad.get_current_caps().get_size()):
            #     print(index, "***", new_pad.get_current_caps().get_structure(i))
            if source == src:
                sink_pad = self.vconverts[index].get_static_pad("sink")
                if not sink_pad.is_linked():
                    new_pad.link(sink_pad)
                    print("link")
                    break

    def on_multiqueue_pad_added(self, src, new_pad):
        if new_pad.direction == Gst.PadDirection.SRC:
            for gtksink in self.gtksinks:
                sink_pad = gtksink.get_static_pad("sink")
                if not sink_pad.is_linked():
                    new_pad.link(sink_pad)
                    print("multiqueue - link")
                    break

    def show_widget(self):
        for gtksink in self.gtksinks:
            gtksink.props.widget.show()


class GUI:
    def __init__(self, videos):
        self.window = Gtk.ApplicationWindow()
        self.window.connect("destroy", Gtk.main_quit)
        self.window.resize(1366, 768)

        self.main_grid = Gtk.Grid()
        self.main_grid.set_row_spacing(5)

        self.videos_boxes = []
        videos_boxes_amount = len(videos.gtksinks) // 5 + 1 if len(videos.gtksinks) % 5 else len(videos.gtksinks) // 5
        for i in range(videos_boxes_amount):
            self.videos_boxes.append(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5))
            self.videos_boxes[i].props.expand = True
        self.buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.buttons_box.props.expand = True

        self.play_button = Gtk.Button.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON)
        self.pause_button = Gtk.Button.new_from_icon_name("media-playback-pause", Gtk.IconSize.BUTTON)
        self.stop_button = Gtk.Button.new_from_icon_name("media-playback-stop", Gtk.IconSize.BUTTON)

        self.create_buttons_events(videos)
        self.set_widgets_positions(videos)

    def create_buttons_events(self, videos):
        self.play_button.connect("clicked", self.on_play, videos)
        self.pause_button.connect("clicked", self.on_pause, videos)
        self.stop_button.connect("clicked", self.on_stop, videos)

    def set_widgets_positions(self, videos):
        self.window.add(self.main_grid)

        columns = 40 / len(self.videos_boxes)
        for i in range(len(self.videos_boxes)):
            if i == 0:
                self.main_grid.attach(self.videos_boxes[i], 0, 0, 1, columns)
            else:
                self.main_grid.attach_next_to(self.videos_boxes[i], self.videos_boxes[i - 1], Gtk.PositionType.BOTTOM,
                                              1, columns)
        self.main_grid.attach_next_to(self.buttons_box, self.videos_boxes[len(self.videos_boxes) - 1],
                                      Gtk.PositionType.BOTTOM, 1, 1)

        for i, gtksink in enumerate(videos.gtksinks):
            self.videos_boxes[i // 5].pack_start(gtksink.props.widget, True, True, 0)
        videos.show_widget()

        self.buttons_box.pack_start(self.play_button, True, True, 0)
        self.buttons_box.pack_start(self.pause_button, True, True, 0)
        self.buttons_box.pack_start(self.stop_button, True, True, 0)

    def on_play(self, button, videos):
        # print(videos.queues[0].get_property("current-level-buffers"))
        videos.play()

    def on_pause(self, button, videos):
        videos.pause()

    def on_stop(self, button, videos):
        videos.stop()


links = ["http://213.184.127.123:82/mjpg/video.mjpg",
         "http://178.8.150.125:80/mjpg/video.mjpg",
         "http://90.146.10.190:80/mjpg/video.mjpg",
         "http://92.220.173.101:80/mjpg/video.mjpg",
         "http://82.77.203.219:8080/cgi-bin/faststream.jpg?stream=half&fps=15&rand=COUNTER",
         "http://94.158.99.9:80/mjpg/video.mjpg",
         "http://46.35.192.141:80/mjpg/video.mjpg",
         "http://81.8.160.235:80/mjpg/video.mjpg",
         "http://194.68.122.244:83/mjpg/video.mjpg",
         "http://94.72.19.58:80/mjpg/video.mjpg",
         "http://217.92.73.116:80/mjpg/video.mjpg",
         "http://194.66.34.9:80/mjpg/video.mjpg",
         "http://213.219.157.15:80/mjpg/video.mjpg",
         "http://89.231.23.159:8081/image?speed=0",
         "http://109.206.96.247:8080/cam_1.cgi"
]
# links = ["rtsp://192.168.0.104:8080/h264_pcm.sdp",
#          "rtsp://192.168.0.102:8080/h264_pcm.sdp"]
#          "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm"
scheduler = Scheduler(links)
# scheduler.start_videos_buffering()
scheduler.start_working()
