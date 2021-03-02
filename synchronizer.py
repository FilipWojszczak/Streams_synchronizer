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
        # Link: "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm"
        self.uri_list = uri_list
        self.pipeline = Gst.Pipeline().new()
        self.sources = []
        self.vconverts = []
        self.gtksinks = []
        self.multiqueue = Gst.ElementFactory.make("multiqueue", "multiqueue")
        self.pipeline.add(self.multiqueue)
        self.multiqueue.set_property('sync-by-running-time', True)
        self.multiqueue.connect("pad-added", self.on_multiqueue_pad_added)

        for index, uri in enumerate(self.uri_list):
            source_string = "source" + str(index + 1)
            vconvert_string = "vconvert" + str(index + 1)
            gtksink_string = "sink" + str(index + 1)
            self.sources.append(Gst.ElementFactory.make("uridecodebin", source_string))
            self.vconverts.append(Gst.ElementFactory.make("videoconvert", vconvert_string))
            self.gtksinks.append(Gst.ElementFactory.make("gtksink", gtksink_string))

            self.pipeline.add(self.sources[index])
            self.pipeline.add(self.vconverts[index])
            self.pipeline.add(self.gtksinks[index])

        for index, uri in enumerate(self.uri_list):
            self.sources[index].connect("pad-added", self.on_source_pad_added)
            self.sources[index].set_property('uri', uri)

            vconvert_pad = self.vconverts[index].get_static_pad("src")
            multiqueue_pad = self.multiqueue.request_pad(self.multiqueue.get_pad_template("sink_%u"), None, None)
            vconvert_pad.link(multiqueue_pad)

        # self.multiqueue.set_property('max-size-bytes', 0)
        # self.multiqueue.set_property('max-size-buffers', 0)
        # self.multiqueue.set_property('max-size-time', 0)

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def stop(self):
        self.pipeline.set_state(Gst.State.READY)

    def on_source_pad_added(self, src, new_pad):
        for index, source in enumerate(self.sources):
            for i in range(new_pad.get_current_caps().get_size()):
                print(index, "***", new_pad.get_current_caps().get_structure(i))
            if source == src:
                sink_pad = self.vconverts[index].get_static_pad("sink")
                if not sink_pad.is_linked():
                    new_pad.link(sink_pad)
                    print("link")
                    break

    def on_multiqueue_pad_added(self, src, new_pad):
        for gtksink in self.gtksinks:
            sink_pad = gtksink.get_static_pad("sink")
            if not sink_pad.is_linked():
                new_pad.link(sink_pad)
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

        self.videos_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.videos_box.props.expand = True
        self.slider_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.slider_box.props.expand = True
        self.buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.buttons_box.props.expand = True

        self.slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.slider.set_draw_value(False)

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

        self.main_grid.attach(self.videos_box, 0, 0, 1, 40)
        self.main_grid.attach_next_to(self.slider_box, self.videos_box, Gtk.PositionType.BOTTOM, 1, 1)
        self.main_grid.attach_next_to(self.buttons_box, self.slider_box, Gtk.PositionType.BOTTOM, 1, 1)

        for gtksink in videos.gtksinks:
            self.videos_box.pack_start(gtksink.props.widget, True, True, 0)
        videos.show_widget()

        self.slider_box.pack_start(self.slider, True, True, 0)

        self.buttons_box.pack_start(self.play_button, True, True, 0)
        self.buttons_box.pack_start(self.pause_button, True, True, 0)
        self.buttons_box.pack_start(self.stop_button, True, True, 0)

    def on_play(self, button, videos):
        videos.play()

    def on_pause(self, button, videos):
        videos.pause()

    def on_stop(self, button, videos):
        videos.stop()
        # print(str(videos[0].pipeline.get_clock().get_time()) + "\n" +
        #       str(videos[1].pipeline.get_clock().get_time()) + "\n*****\n" +
        #       str(videos[0].pipeline.query_position(Gst.Format.TIME)) + "\n" +
        #       str(videos[1].pipeline.query_position(Gst.Format.TIME)) + "\n*****\n" +
        #       str(videos[0].pipeline.get_base_time()) + "\n" +
        #       str(videos[1].pipeline.get_base_time()) + "\n")


links = ["http://192.168.0.100:8080/video", "http://192.168.0.100:8080/video"]
# links = ["https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm",
#          "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm"]
scheduler = Scheduler(links)
# scheduler.start_videos_buffering()
scheduler.start_working()
