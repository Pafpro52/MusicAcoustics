% Hamit Batuhan Aydin, stud. M.Sc. Music Acoustic 
% 20.08.2026
% Simple frequency response measurement using an audio interface.
% Includes sweep generation, latency calibration, repeated measurements,
% reference comparison, and FRF plotting.
%%
clear
close all
clc

% Measurement settings
fs = 48000;
amp = 0.7;
averages = 3;
duration = 5;
device = "none";

if ~exist("results","dir")
    mkdir("results")
end

%% Main menu
while true
    choice = input("\n1: New measurement\n2: Compare measurements\n3: Exit\nSelect: ");

    if choice == 1
        % Audio device
        answer = input("Configure audio settings? (y/n): ","s");

        if strcmpi(answer,"y")
            test = audioPlayerRecorder('SampleRate',fs);
            devices = getAudioDevices(test);

            for i = 1:length(devices)
                fprintf("%d: %s\n",i,devices{i});
            end

            n = input("Select device number: ");
            device = devices{n};
            release(test)
        end

        fprintf("Selected device: %s\n",device)

        io = audioPlayerRecorder( ...
            'Device',device, ...
            'SampleRate',fs, ...
            'PlayerChannelMapping',1, ...
            'RecorderChannelMapping',1, ...
            'SupportVariableSize',true, ...
            'BufferSize',512);

        % Latency calibration
        input("Connect Output 1 -> Input 1. ENTER...","s");

        noise = randn(fs,1);
        noise = noise * amp/max(abs(noise));
        pre = zeros(fs/2,1);
        x = [pre; noise; pre];
        y = io(x);

        % Find where the recorded noise starts
        [c,lags] = xcorr(y,noise);
        [~,i] = max(abs(c));
        latency = lags(i) - length(pre);

        fprintf("Latency: %d samples (%.1f ms)\n", ...
            latency,latency/fs*1000);

        % Run measurement
        sweep = make_sweep(fs,amp,duration);
        input("Connect setup and press ENTER...","s");

        signal = measure(io,sweep,latency,averages);

        % Save measurement
        name = input("Measurement name: ","s");
        save(fullfile("results",[name '.mat']),"signal")
        fprintf("Saved: %s.mat\n",name);

        release(io)

    elseif choice == 2
        % Show saved measurements
        files = dir(fullfile("results","*.mat"));

        if length(files) < 2
            fprintf("Not enough measurements.\n");
            continue
        end

        for i = 1:length(files)
            fprintf("%d: %s\n",i,files(i).name);
        end

        r = input("Reference number: ");
        m = input("Measurement number: ");

        ref = load(fullfile("results",files(r).name));
        meas = load(fullfile("results",files(m).name));

        plot_frf(ref.signal,meas.signal,fs)


    elseif choice == 3
        break
    else
        fprintf("Invalid selection.\n");
    end
end

%% Make sweep
function x = make_sweep(fs,amp,duration)

% Linear sweep from 20 Hz to 20 kHz
t = (0:duration*fs-1)'/fs;
sweep = amp * chirp(t,20,duration,20000,'log');

% Silence before and after
x = [zeros(fs/2,1); sweep; zeros(fs,1)];

end

%% Run measurement
function y = measure(io,x,latency,averages)

runs = [];
i = 1;

while i <= averages
    fprintf("Measurement %d/%d\n",i,averages);

    [temp,underrun,overrun] = io(x);

    % Ignore bad recordings and try again. This happens because MATLAB
    % sometimes is not able to fill or read the audio buffer in time.
    % Underrun means missed output samples, overrun means missed input samples.
    if underrun > 0 || overrun > 0
        fprintf("Audio error - don't worry, retrying...\n");
        continue
    end

    runs(:,i) = temp(latency+1:end);
    i = i + 1;
end

% Average the good recordings
y = mean(runs,2);
fprintf("Peak: %.1f dBFS\n",20*log10(max(abs(y))));

end


%% Plot - Frequency response
function plot_frf(ref,meas,fs)

n = min(length(ref),length(meas));
ref = ref(1:n);
meas = meas(1:n);

% FFT and keep only positive frequencies
N = floor(n/2)+1;

REF = fft(ref);
MEAS = fft(meas);

REF = REF(1:N);
MEAS = MEAS(1:N);

% Frequency axis
f = (0:N-1)' * fs/n;

% Measurement compared with reference
H = MEAS ./ REF;
dB = 20*log10(abs(H));

% Show only 20 Hz - 20 kHz
m = f >= 20 & f <= 20000;

figure('Position',[50 50 700 350])

semilogx(f(m),dB(m),'LineWidth',1.5)
hold on

% 0 dB reference line
yline(0,'r--','LineWidth',1.2)

hold off

% Automatic y-axis with 5 dB margin
ymin = min(dB(m)) - 5;
ymax = max(dB(m)) + 5;

if min(dB(m)) > 0
    ylim([-5 ymax])      % everything is above 0 dB
elseif max(dB(m)) < 0
    ylim([ymin 5])       % everything is below 0 dB
else
    ylim([ymin ymax])    % response crosses 0 dB
end

xlim([20 20000])
grid on

% Bigger text for report / export
set(gca,'FontSize',16,'LineWidth',1.2)

xlabel('Frequency [Hz]','FontSize',18)
ylabel('Gain [dB]','FontSize',18)
title('Frequency Response','FontSize',19)

% Reduce empty space around the plot
set(gca,'Position',[0.08 0.18 0.90 0.72])

end