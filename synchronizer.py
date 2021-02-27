#!/usr/bin/env python3
import gi

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
        self.videos = [Video(uri) for uri in self.uri_list]
        self.gui = GUI(self.videos)

    def start_videos_buffering(self):
        for video in self.videos:
            video.pause()

    def start_working(self):
        self.gui.window.show_all()
        Gtk.main()

    def play_all(self):
        pass

    def pause_all(self):
        pass

    def stop_all(self):
        pass


class Video:
    def __init__(self, uri):
        # Link: "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm"

        self.source = Gst.ElementFactory.make("uridecodebin", "source")
        self.source.set_property('uri', uri)
        self.vconvert = Gst.ElementFactory.make("videoconvert", "vconvert")
        self.gtksink = Gst.ElementFactory.make("gtksink", "sink")
        self.pipeline = Gst.Pipeline().new()

        self.pipeline.add(self.source)
        self.pipeline.add(self.vconvert)
        self.pipeline.add(self.gtksink)

        self.vconvert.link(self.gtksink)
        self.source.connect("pad-added", self.on_pad_added)

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def stop(self):
        self.pipeline.set_state(Gst.State.READY)

    def on_pad_added(self, src, new_pad):
        sink_pad = self.vconvert.get_static_pad("sink")
        new_pad.link(sink_pad)

    def show_widget(self):
        self.gtksink.props.widget.show()


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

        for video in videos:
            self.videos_box.pack_start(video.gtksink.props.widget, True, True, 0)
            video.show_widget()

        self.slider_box.pack_start(self.slider, True, True, 0)

        self.buttons_box.pack_start(self.play_button, True, True, 0)
        self.buttons_box.pack_start(self.pause_button, True, True, 0)
        self.buttons_box.pack_start(self.stop_button, True, True, 0)

    def on_play(self, button, videos):
        for video in videos:
            video.play()

    def on_pause(self, button, videos):
        for video in videos:
            video.pause()

    def on_stop(self, button, videos):
        for video in videos:
            video.stop()


links = ["https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm",
         "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm"]
scheduler = Scheduler(links)
scheduler.start_videos_buffering()
scheduler.start_working()
