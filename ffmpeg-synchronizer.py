import ffmpeg
import subprocess

in_filename = "http://192.168.0.100:8080/video"
in_filename2 = "http://192.168.0.102:8080/video"

probe = ffmpeg.probe(in_filename)
video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
width = int(video_stream['width'])
height = int(video_stream['height'])
print(width, type(width))
# width, height = 640, 480  # (or use ffprobe or whatever)

# '-fflags', 'nobuffer',
# '-fflags', 'discardcorrupt',
# '-flags', 'low_delay',
# '-strict', 'experimental',
# '-avioflags', 'direct',
first = ffmpeg.input(in_filename, fflags='nobuffer', flags='low_delay', avioflags='direct', probesize=32, analyzeduration=0, thread_queue_size=100)
second = ffmpeg.input(in_filename2, fflags='nobuffer', flags='low_delay', avioflags='direct', probesize=32, analyzeduration=0, thread_queue_size=100)
# .filter('scale', width=width, height=height, force_original_aspect_ratio='disable')

process1 = (
    # ffmpeg.filter([first, second], 'vstack')
    ffmpeg.filter([first, second], 'xstack', layout="0_0|w0_0")
        .output('pipe:', format='rawvideo', pix_fmt='rgb24')
        .run_async(pipe_stdout=True)

    # ffmpeg
    # .input(in_filename)
    # # (filters/etc. go here)
    # .output('pipe:', format='rawvideo', pix_fmt='rgb24')
    # .run_async(pipe_stdout=True)
)
process2 = subprocess.Popen(
    [
        'ffplay',
        '-f', 'rawvideo',
        '-pixel_format', 'rgb24',
        '-fflags', 'nobuffer',
        '-fflags', 'discardcorrupt',
        '-flags', 'low_delay',
        # '-strict', 'experimental',
        '-avioflags', 'direct',
        '-video_size', '{}x{}'.format(width*2, height),
        '-i', 'pipe:',
        '-autoexit'
    ],
    stdin=process1.stdout,
)
process1.wait()
process2.wait()

# import ffmpeg
# (
#     ffmpeg
#     .input("http://192.168.0.100:8080/video")
#     .hflip()
#     .output('pipe:', format='rawvideo', pix_fmt='rgb24')
#     .run()
# )
