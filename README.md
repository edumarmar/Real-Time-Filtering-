# Real-Time-Filtering-
Real Time Audio Filtering Using Spectral Gating


**Introduction**

Spectral denoise is designed to remove stationary or slowly changing tonal noise by generating a profile of the background noise, then subtracting that noise when a signal’s amplitude drops below a specified threshold. It is a flexible tool that can be used to quickly achieve accurate, high-quality noise reduction.

**How does it work? (offline)**

First, let us explain how the filter works offline:
The algorithm performs the STFT (Short Time Fourier Transform) of the noisy portion of the signal, generating a spectrogram that we can use to calculate a statistical profile of the noise. By using the mean and the standard deviation, we calculate a threshold that will tell if the signal can get through the filter or not. The threshold can be expressed as:
Threshold=Mean+Stdv*Stdv_user
Where “stdv user” is how many standard deviations away from the noise we want to consider signal. We have now calculated a threshold for each frequency.

Then we can calculate the STFT of the signal and compare it with the thresholds previously calculated. If the signal surpasses that threshold, it will get through, if not, it will be removed as it will be considered as noise. We do this procedure for each time/frequency bin, filling a logical matrix (mask) that will be convolved with a gaussian smoothing filter. The result will be the final mask that we will apply to the signal. 

This mask is applied to the signal and then an inverse STFT is performed to recover the filtered version in time.

**Implementation in real time**

To filter the signal in real time, we must process it by “chunks”. The software will continuously read the last 1024 samples at a time (if the sample frequency is 16000Hz, this will mean a 64ms delay).  We will be filling an array with all these chunks, that later will be used to calculate the noise statistics (and to export a .wav file at the end of the recording). 
We start the recording, but we do not filter the signal until the first 3 seconds have passed (to gather enough information of the noise and generate its proper profile). Once this period has passed, we consecutively grab the last 3 seconds of signal and apply the algorithm explained above. Now we have the last 3 seconds of recording filtered, but we are just interested in the last chunk (⁓present moment). This last filtered chunk will be then concatenated in a “denoised signal” array. 
Since we are updating the noise portion on each new chunk, and consequently the noise profile, we can consider this filter as adaptive.

