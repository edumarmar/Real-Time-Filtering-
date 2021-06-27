'''This program records an audio signal from a selected
recording device and filters it in real time with spectral gating.

The audio signal and its filtered version is plotted in real time
with PyQTgraph.

The signal is filtered with a modified version of
noisereduce module https://pypi.org/project/noisereduce/'''


from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyaudio
from audacity_noise_removal.audacity_noise_removal_mine import reduce_noise
from scipy.io import wavfile
import numpy as np
import sys

signal = np.array([0,0]) #empty array that we will fill with the audio data that comes in
clean = np.array([0,0]) #empty array thtat we will fill with the filtered signal
counter = 0
seconds = int((16000)/1024) #this var will let us work with seconds later on
noisy_part = 0

class AudioStream(object):

    def __init__(self):

        # To aid the recording, I have used PyQTGraph. It is a module
        # that can plot in real time, much faster than matplotlib.
        # Most of the code and features are predetermined.
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='Spectrum Analyzer')
        self.win.setWindowTitle('Spectrum Analyzer')
        self.win.setGeometry(5, 115, 1910, 1070)

        wf_xlabels = [(0, '0'), (2048, '2048'), (4096, '4096')]
        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setTicks([wf_xlabels])

        wf_ylabels = [(0, '0'), (127, '128'), (255, '255')]
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])

        #This is a logarithmic scale for a spectogram. I removed the spectogram
        # feature since it was taking more processing force than needed to filter
        # the signal.
        sp_xlabels = [
            (np.log10(10), '10'), (np.log10(100), '100'),
            (np.log10(1000), '1000'), (np.log10(22050), '22050')
        ]
        sp_xaxis = pg.AxisItem(orientation='bottom')
        sp_xaxis.setTicks([sp_xlabels])

        self.waveform = self.win.addPlot(
            title='WAVEFORM', row=1, col=1, axisItems={'bottom': wf_xaxis, 'left': wf_yaxis},
        )
        self.spectrum = self.win.addPlot(
            title='SPECTRUM', row=2, col=1, axisItems={'bottom': sp_xaxis},
        )

        '''Here we use PyAudio. It is a python module that will let us record signal
        from the outside. Now, it is implemented with the builtin microphone of the
        computer, but can be tweaked to receive the audio from the device:
        
        See https://stackoverflow.com/questions/36894315/how-to-select-a-specific-input-device-with-pyaudio'''

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000 #sample frequency
        self.CHUNK = 1024 * 1 #how many samples we will process at a time

        #initializing the Pyaudio module, with the desired parameters
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )
        # waveform and spectrum x points
        self.x = np.arange(0, 2 * self.CHUNK, 2)
        self.f = np.linspace(0, int(self.RATE / 2), int(self.CHUNK / 2))

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()


    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                #plots in blue the original audio
                self.traces[name] = self.waveform.plot(pen='c', width=3)
                self.waveform.setYRange(-1, 1, padding=0) #The range of audio is standarized from -1 to 1
                self.waveform.setXRange(0, 2 * self.CHUNK, padding=0.005)
            if name == 'spectrum':
                # plots in magenta the filtered audio
                self.traces[name] = self.waveform.plot(pen='m', width=3)
                self.waveform.setYRange(-1, 1, padding=0)
                self.waveform.setXRange(0, 2 * self.CHUNK, padding=0.005)


    def update(self):
        global counter
        global noisy_part
        global signal
        global clean
        global seconds

        counter = counter + 1

        wf_data = self.stream.read(self.CHUNK) #read the present chunk of audio
        wf_data = np.frombuffer(wf_data, dtype = '<i2') #The signal is 16 bit integer, then the range is [-32768, 32767]
        wf_data = (wf_data / 32768) #we standarize the data into -1, 1 range.


        wf_data_clean = wf_data #the first 3 seconds, we do not filter the signal
                                #so we just plot the original
        signal = (np.concatenate((signal, wf_data), axis=None))
        if counter <= seconds * 3:
            clean = (np.concatenate((clean, wf_data_clean), axis=None))
        else:
        #When we surpass the 3 seconds, we start filtering.

            # we filter the 10 last CHUNKS of data
            wf_data_clean, ignore1, ignore2 = reduce_noise(audio_clip=signal[-45*self.CHUNK:], noise_clip=signal[-45*self.CHUNK:],n_grad_time=0,n_std_thresh=1.5, prop_decrease=1)
            # but we grab just the last one (present one)
            wf_data_clean = wf_data_clean[-self.CHUNK:]
            #and add it to the array containing the clean signal
            clean = (np.concatenate((clean, wf_data_clean), axis=None))

        #We plot the audio signal in real time
        self.set_plotdata(name='waveform', data_x=self.x, data_y=wf_data,)
        self.set_plotdata(name='spectrum', data_x=self.x, data_y=wf_data_clean, )


    def animation(self):
        #similar to FuncAnimation of matplotlib
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()


if __name__ == '__main__':

    audio_app = AudioStream()
    audio_app.animation()

    #Once we have stopped recording, we generate a wav file for the noisy
    # and denoised signal.
    wavfile.write("SIGNAL.wav", 16000, signal)
    wavfile.write("SIGNAL CLEAN.wav", 16000, clean)
