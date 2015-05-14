# BCI workshop at Disctrict3

This document provides instructions and explanations for completing the BCI workshop given by BCI Montréal in May 2015. Specifically, it will guide you through the installation of the necessary software, the configuration of the device we will use, and the two exercises that are at the core of this workshop.

This workshop is intented for people with no or limited experience with Brain-Computer Interfaces (BCIs). The workshop will teach them the basic principles that are necessary to "hack" and develop new applications with BCIs: background on brain activity and brain activity measurement with EEG, structure of a BCI, feature extraction and machine learning. Two hands-on exercises will allow the participants to 1) visualize their EEG signals and some relevant features, and 2) experiment with a very simple BCI design. This should give the participants sufficient knowledge to understand the advantages and limitations of current BCIs, and to devise their own applications. 

## Installation of software for the workshop

The workshop is based on the following tools:

1. **Python 2.7 (and packages)**: a popular, powerful, free and simple to read scripting language
2. **Muse SDK**: the software development kit provided to play around with the Muse EEG headband
3. **MuLES**: an EEG server that allows device-agnostic applications

Many alternative tools could have been chosen for this workshop, such as **BCI toolboxes** ([OpenVIBE](http://openvibe.inria.fr/), [BCI2000](http://www.bci2000.org/wiki/index.php/Main_Page), [BCILAB](http://sccn.ucsd.edu/wiki/BCILAB), etc.), other programming languages (MATLAB, Processing, Java, etc.), low-level SDKs/APIs (such as Muse's [LibMuse](https://sites.google.com/a/interaxon.ca/muse-developer-site/libmuse)), and even **other EEG devices** (OpenBCI, Emotiv EPOC, Neurosky Mindwave, etc.). 

We chose the Python/Muse/MuLES combination as it provides a lot of flexibility to hackers, but at the same time is simple enough that novice users can understand what they are doing. Because of this choice, we are stuck with Windows; however, the goal of this workshop is to teach you about BCIs in general, so that you are able to apply this knowledge to the environment and tools of your choice. We won't focus much on tools here.

### 1. Python 2.7 and packages

Python is a high-level scripting language that has been widely adopted in a plethora of applications. It is free, simple to read, and has an extensive standard library. Many packages can also be downloaded online to complement its features.

Two packages are especially useful when dealing with scientific computing (as for BCIs): [NumPy](http://www.numpy.org/) and [matplotlib](http://matplotlib.org/). NumPy allows easy manipulation of arrays and matrices (very similar to [MATLAB](http://mathesaurus.sourceforge.net/matlab-numpy.html)), which is necessary when dealing with data such as neurophysiological signals. Matplotlib is similar to MATLAB's plotting functionalities, and can be used to visualize the signals and features we are working with.

Other packages we will use in this workshop are:

* [scikit-learn](http://scikit-learn.org/stable/): a machine learning library
* [pyZMQ](https://zeromq.github.io/pyzmq/): the Python binding for ZMQ, a simple communication library

To install Python 2.7 and the required packages, we suggest you download and install the [Anaconda distribution](http://continuum.io/downloads). This Python distribution includes Python 2.7, all the packages we will need for the workshop (as well as plenty other useful packages), and [Spyder](https://pythonhosted.org/spyder/), a great IDE for scientific computing in Python.

#### 1.1 Installation with Anaconda

1. Download the [Anaconda graphical installer](http://continuum.io/downloads) (for Windows 64-bit, Python 2.7, size: 331M).
2. Execute the installer.

#### 1.2 Individual installation of Python and packages
Alternatively, you can [download Python 2.7 independently](http://docs.python-guide.org/en/latest/starting/install/win/). Make sure to install ```pip``` (as explained [here]((http://docs.python-guide.org/en/latest/starting/install/win/))) and grab NumPy, matplotlib and scikit-learn by calling
```pip install <package_name>``` on the command line (or any other way, really). Make sure you have a text editor or IDE you can work with as well.

### 2. Muse SDK

This workshop is based on the [Muse](http://www.choosemuse.com/) EEG headband. The Muse provides 4 EEG dry sensors located on the forehead and behind the ears. It communicates via Bluetooth to a computer or a mobile device. An [SDK](https://sites.google.com/a/interaxon.ca/muse-developer-site/home) is available to allow basic control over the Muse's recording capabilities.

To install the SDK, download and execute the [Muse SDK Tools 3.4.1 installer for Windows](https://sites.google.com/a/interaxon.ca/muse-developer-site/download).

### 3. MuLES (MuSAE Lab EEG Server)

[MuLES](https://github.com/MuSAELab/MuLES) is an EEG streaming server, i.e. a piece of software that handles the communication with an EEG device and streams the recorded signals on a network. This is very useful in our case since:

1. It provides a high-level interface to EEG signals;
2. It can communicate with any of the following devices without requiring any modification: Muse, Emotiv EPOC, Neurosky Mindwave, OpenBCI, Neuroelectrics Enobio;
3. It can stream EEG signals over a single computer or a network (or the Internet).

MuLES is based on LabView, and is currently only available for Windows. Future releases might support other operating systems.

To install MuLES, download the [MuLES installer v1.3](https://github.com/MuSAELab/MuLES/releases) and follow the instructions given on the web page.

### 4. Pairing the Muse and configuring MuLES

The Muse communicates to external devices using the Bluetooth protocol, and thus needs to be paired with your computer. To pair the Muse with your computer, follow these steps:

1. Switch Muse into Pairing Mode by holding the button down for ~5 seconds. The light should start flashing.
2. Under *Control Panel/Hardware and Sound*, click on *Add a device*.
3. A Bluetooth device named *Muse<-something>* should appear. Select the Muse device and click *Next*.
4. Click *Next* when asking for a passcode.
5. Turn off the Muse by holding the button down for ~2 seconds.

Now that your computer is set up to recognize the Muse, we will configure MuLES so it knows which device it should be looking for.

1. Go to the MuLES installation directory (by default ```C:\Program Files (x86)\MuSAE_Lab\MuLES```).
2. Open ```config.ini``` in a text editor.
3. Under the section [DEVICE03], locate the ```EXTRA``` keyword.
4. Change the value of the ```BTNAME``` parameter to the name of your Muse. For example, if your Muse's Bluetooth name is ```Muse-6AB1```, you would have the line ```EXTRA = "FS=220,#CH=4,DATA=ffffi,PRESET=14,BTNAME=Muse-6AB1,OSCPORT=5000"```
5. Save and close the file.


### 5. Download the code for the workshop

Download the folder...


## Exercise 1: A simple neurofeedback interface

In this first exercise, we will learn how to visualize the raw EEG signals that come from the Muse inside a Python application. We will also extract and visualize basic features of the raw EEG signals. This will showcase a first basic use of a Brain-Computer Interface: a so-called neurofeedback interface.

> Neurofeedback (NFB), also called neurotherapy or neurobiofeedback, is a type of biofeedback that uses real-time displays of brain activity—most commonly electroencephalography (EEG), to teach self-regulation of brain function. Typically, sensors are placed on the scalp to measure activity, with measurements displayed using video displays or sound.

### E1.1 Streaming data from the Muse

1. Open MuLES (a shortcut should have been automatically added to your desktop, otherwise you can run it from the installation directory ```C:\Program Files (x86)\MuSAE_Lab\MuLES```).
2. In the dropdown menu, choose ```MUSE Consumer FW```.
3. Make sure the *Enable TCP Server* button is highlighted in green.
4. Switch on the Muse by holding the button down for ~1 second. The light should start oscillating.
5. Start streaming data from the Muse by clicking on the *Play* button. A command line window should appear giving details on the communication status.

### E1.2 Running the Python visualization script

In order to examinate and play around with the code, we recommend you open the provided Python scripts in an IDE or a text editor. However, the script should run without any modification and can be launched from the command line by running ```python <script_name>.py``` in the appropriate folder.

1. Open the script ```exercise_01_one_channel.py``` in Spyder (or your favorite IDE/text editor).
2. Read the code - it is heavily commented - and modify the experiment parameters as you wish (line 32 to 48).
3. When you feel confident about what the code does (or before), run the script. In Spyder, select a Python console on the bottom right of the screen, then click on the *Play* button on top of the editor.
4. Two figures should appear: One displaying the raw signals of the Muse's 4 EEG sensors, and another one showing the basic band power features we are computing on one of the EEG signals.
5. To stop the execution of the script, enter <Ctrl+C> in the Python console (don't forget MuLES is still running as well!).

### E1.3 Playing around

Here are some things we suggest you do to understand what the script does.

#### Visualizing your raw EEG signals

Run the script and look at the first figure (raw EEG visualization). What makes your signal change?

1. Try blinking, clenching your jaw, moving your head, etc.
2. Imagine repeatedly throwing a ball for a few seconds, then imagine talking to a good friend for another few seconds, while minimizing any movement or blinks.

In the first case, you can see that the first movements (blinking, etc.) produce high perturbations of the EEG signal. We call these **artifacts**. Some artifacts are so huge that they can completely obscure the actual EEG signal coming from your brain. We typically divide artifacts according to their source: *physiological artifacts* (caused by the electrical activity of the heart, muscles, movement of the eyes, etc.), and *motion artifacts* (caused by a relative displacement of the sensor and the skin).

In the second case, you can see that different mental activities (e.g. imagining eating or talking) are not easily recognizable in the EEG signals. 
First, this is because mental activity is distributed across the brain: for example, sensorimotor processing occurs on top of the brain, in the central cortex, while speech-related functions occurs at the sides of the brain, in the temporal cortex. Therefore, the 4 sensors on the Muse are not necessarily on the right "spot" to capture the relevant EEG signals.
Second, the EEG signals are very, very, very noisy. Indeed, the electrical signals that we pick up on the scalp are smeared by the skull, muscles and skin. As you saw, eye balling the signals is often not enough to analyze brain activity. (That is why we need to extract features!)

#### Visualizing your EEG features

Since the raw EEG signals are not easy to read, we will extract some features that will hopefully be more insightful. The most often used features to describe EEG are frequency band powers.

1. Open the script ```bci_workshop_tools.py```.
2. Locate the function ```compute_feature_vector()``` (line 87).

This function uses the Fast Fourier Transform, an algorithm that extracts the frequency information of a time signal. It transforms the EEG time series (i.e., the raw EEG signal that you visualized above) into a list of amplitudes each corresponding to a specific frequency.

In EEG analysis, we typically look at ranges of frequencies, that we call *frequency bands*:

- Delta (< 4 Hz)
- Theta (4-7 Hz)
- Alpha (8-15 Hz)
- Beta  (16-31 Hz)
- Gamma (> 31 Hz)

We expect each band to reflect specific mental processes and activities. For example, we know that closing the eyes and relaxing provokes an increase in Alpha activity, especially at the back of the head. We will try to reproduce this result now.

1. Open the script ```exercise_01_one_channel.py```.
2. Change the value of the ```eeg_buffer_secs``` parameter to around 40.
3. Run the script and look at the second figure.
4. Keep your eyes open for 20 seconds (again, minize your movements).
5. Close your eyes and relax for another 20 seconds (minize your movements).

Do you see a difference between the first and the last 20-s windows for the Alpha feature?

#### Advanced: computing supplementary features

Many other features can be used to describe the EEG activity: band powers, Auto-Regressive model coefficients, Wavelet coefficients, coherence, mutual information, etc. As a starting point, adapt the code in the ```compute_feature_vector()``` function to compute ratios of band powers. For example, Theta/Beta and Alpha/Beta ratios are often used to study EEG.

Repeat the above eyes open/closed procedure with your new features. Can you see a clearer difference between the two mental states?


## Exercise 2: A basic BCI

In this second exercise, we will learn how to use an automatic algorithm to recognize somebody's mental states from their EEG.
We will use a *classifier*: a classifier is an algorithm that, provided some data, learns to recognize patterns , and can then classify similar unseen information.

For example, let's say we have many [images of either cats or dogs that we want to classify](https://www.kaggle.com/c/dogs-vs-cats). A classifier would first require *training data*: in this case we could give the classifier 1000 pictures of cats that we identify as cats, and 1000 pictures of dogs that we identify as dogs. The classifier will then learn the patterns that make a picture a picture of a cat, or a picture of a dog. Once it is trained, the classifier can now output *decisions*: if we give it a new, unseen picture, it will try its best to correctly determine whether it's a cat or a dog in the picture.

In a Brain-Computer Interface, we use classifiers to identify which type of mental task somebody is doing. For example, in the previous exercise, you saw that opening and closing your eyes modifies the features of the EEG signal. To use a classifier, we would need to proceed like this:

1. Collect EEG data of you performing the two mental activities (eyes open vs. eyes closed).
2. Input this labelled data to the classifier.
3. *Train* the classifier.
4. Use the classifier by giving it new EEG data, and asking for a decision on which mental activity this represents.

Brain-Computer Interfaces rely heavily on **machine learning**, the field devoted to building classifiers (and other cool stuff). You might have already understood why: in a typical EEG application we have a lot of features (e.g. many band powers) and the mental activity we want to classify is not easily recognizable.

Let's try it now.

### E2.1 Running the Python basic BCI script

1. Open the script ```exercise_02.py```.
2. Read the code - it is heavily commented - and modify the experiment parameters as you wish. You will see it's very similar to the code of Exercise 1, but with a few new sections.
3. When you feel confident about what the code does (or again, before), run the script.
4. When you hear a **first beep**; keep your eyes open and concentrate (while minimizing your movements).
5. When you hear a **second beep**; close your eyes and relax (while minimizing your movements).
6. When you hear a **third beep**, the classifier is trained and starts outputting decisions in the Python console: ```0``` when your eyes are open, and ```1``` when you close them.
7. To stop the execution of the script, enter <Ctrl+C> in the Python console (don't forget MuLES is still running as well!).

### E2.2 Playing around

Here are some things we suggest you do to understand what the script does.

#### Visualizing the classifier decisions

Try the above procedure to train and use the classifier. If it does not work well, make sure the EEG signals are stable (you can reuse the code of Exercise 1 to visualize the raw signals) and try again. Some people will typically have a stronger Alpha response than others, and it also takes practice to be able to modulate it at will.

#### Using other mental tasks

Try the same procedure again, but train your classifier with different mental activities. For example, perform some random mental mutliplication during the first 20 seconds, and try to come up with as many words as possible starting with the letter *T* during the next 20 seconds. Once the classifier is trained, repeat the two mental tasks. Is the classifier able to recognize the task you are performing?

Additionally, try the first training procedure again (eyes open vs. eyes closed). However, don't close your eyes during the second task, but instead relax with your eyes open. Can the classifier recognize your mental state?

#### Sending decisions to an external application

Once your BCI framework is functional, you can start thinking about sending your EEG features or classifier decisions to an external application.
Many different libraries can be used for that, beginning with standard TCP/IP communication implementations (e.g. Python's [socket](https://docs.python.org/2/library/socket.html) module).
We suggest [pyZMQ](https://zeromq.github.io/pyzmq/), which allows simple communication between a Python application and any programming language supporting the [ZMQ](http://zeromq.org/) protocol.

TODO: Provide more info on that part...

For example, let's send our classifier decisions to a Processing script to create simple animations...

## Conclusion

Blablabla


## References

Blablabla

## Authors

Raymundo Cassani & Hubert Banville

Thanks to: [MuSAE Lab](http://musaelab.ca/), [District 3](http://d3center.ca/), [BCI Montréal](http://bcimontreal.org/), ...