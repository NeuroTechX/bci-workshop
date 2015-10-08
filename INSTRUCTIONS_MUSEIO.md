# A Quick Practical Introduction to Brain-Computer Interfacing

TODO:

- Continue modifying the text to remove MuLES and add Muse-io (I stopped at section E1.1)
- Choose an OSC library and write the Muse server accordingly
- In code: change while loop to process data only where there's enough new points in the buffer
- Add pictures, screenshots, snippets of code, jokes, it must be easy and fun to read!
- Move to some blog format instead of one markdown document?

Introduction...

- BCI are more accessible (available technology, machine learning, open source projects)
- Many people want to know, where can I start? What should I do to start? If you have access to a computer and some kind of EEG device, you should be ready to start.

This document will guide you through the installation of the necessary software, the configuration of the device we will use, and the two exercises that are at the core of this workshop.

This workshop is intended for people with no or limited experience with Brain-Computer Interfaces (BCIs). The workshop will teach them the basic principles that are necessary to "hack" and develop new applications with BCIs: background on brain activity and brain activity measurement with EEG, structure of a BCI, feature extraction and machine learning. Two hands-on exercises will allow the participants to 1) visualize their EEG signals and some relevant features, and 2) experiment with a very simple BCI design. This should give the participants sufficient knowledge to understand the advantages and limitations of current BCIs, and to devise their own applications.

If you are working on Windows and would like to have the ability to work with any consumer EEG device, I recommend you look at the version of this workshop that works with MuLES, an EEG server that allows the use of many current EEG devices out of the box. Sadly, MuLES does not support other operating systems for the moment.

## Installation of software for the workshop

The workshop is based on the following tools:

1. **Python 2.7 (and packages)**: a popular, powerful, free and simple to read scripting language
2. **Muse SDK**: the software development kit provided to play around with the Muse EEG headband
3. **Muse headband**: a consumer-grade wireless EEG headset 

Many alternative tools could have been chosen for this workshop, such as **BCI toolboxes** ([OpenVIBE](http://openvibe.inria.fr/), [BCI2000](http://www.bci2000.org/wiki/index.php/Main_Page), [BCILAB](http://sccn.ucsd.edu/wiki/BCILAB), etc.), other programming languages (MATLAB, Processing, Java, etc.), low-level SDKs/APIs, and even **other EEG devices** (OpenBCI, Emotiv EPOC, Neurosky Mindwave, etc.). 

We chose the Python/Muse combination as it provides a lot of flexibility to hackers, but at the same time is simple enough that novice users can understand what they are doing. The Muse's freely available SDK is great for our purpose and will work on all major OSs.

### 1. Python 2.7 and packages

Python is a high-level scripting language that has been widely adopted in a plethora of applications. It is free, simple to read, and has an extensive standard library. Many packages can also be downloaded online to complement its features.

Two packages are especially useful when dealing with scientific computing (as for BCIs): [NumPy](http://www.numpy.org/) and [matplotlib](http://matplotlib.org/). NumPy allows easy manipulation of arrays and matrices (very similar to [MATLAB](http://mathesaurus.sourceforge.net/matlab-numpy.html)), which is necessary when dealing with data such as neurophysiological signals. Matplotlib is similar to MATLAB's plotting functionalities, and can be used to visualize the signals and features we are working with.

Other packages we will use in this workshop are:

* [scikit-learn](http://scikit-learn.org/stable/): a machine learning library
* [pyOSC](https://trac.v2.nl/wiki/pyOSC): A pure-Pythone OSC library to receive the streamed EEG data
* [pyZMQ](https://zeromq.github.io/pyzmq/): the Python binding for ZMQ, a simple communication library

To install Python 2.7 and most of the required packages, we suggest you download and install the [Anaconda distribution](http://continuum.io/downloads). This Python distribution includes Python 2.7, and some packages we will need for the workshop (as well as plenty other useful packages), and [Spyder](https://pythonhosted.org/spyder/), a great IDE for scientific computing in Python. The OSC library will require a separate installation.

#### 1.1 Installation with Anaconda

1. Download the [Anaconda graphical installer](http://continuum.io/downloads) (if your Windows version is 32-bit, make sure to download the 32-bit installer).
2. Execute the installer.

#### 1.2 Individual installation of Python and packages

Alternatively, you can [download Python 2.7 independently](http://docs.python-guide.org/en/latest/starting/install/win/). Make sure to install ```pip``` (as explained [here]((http://docs.python-guide.org/en/latest/starting/install/win/))) and grab NumPy, matplotlib and scikit-learn by calling ```pip install <package_name>``` on the command line (or any other way you prefer). Make sure you have a text editor or IDE you can work with as well.

#### 1.3 Installation of the OSC library

Many Python libraries exist to allow communication with the OSC protocol, but each has its limitations. This workshop is based on pyOSC, a pure Python implementation, which works across platforms.

1. Download the library from [here](https://trac.v2.nl/wiki/pyOSC), and extract it somewhere on your computer. (Note that the version of pyOSC available with ```pip``` only works with Python 3.0, and so cannot be used in this workshop.)
2. Navigate to the extracted folder inside a terminal, and install the library by calling ```python setup.py install```.

### 2. Muse SDK

This workshop is based on the [Muse](http://www.choosemuse.com/) EEG headband. The Muse provides 4 EEG dry sensors located on the forehead and behind the ears. It communicates via Bluetooth to a computer or a mobile device. The [SDK](https://sites.google.com/a/interaxon.ca/muse-developer-site/home) is available for free and allows basic control over the Muse's recording capabilities. 

Our main tool from the SDK will be ```muse-io```, a program that handles the bluetooth connection with the Muse, and streams all incoming data using a simple network protocol called [OSC](https://en.wikipedia.org/wiki/Open_Sound_Control).

To install the SDK for your OS, follow the instructions [here](http://developer.choosemuse.com/research-tools).

### 3. Pairing the Muse

The Muse communicates to external devices using the Bluetooth protocol, and thus needs to be paired with your computer. To pair the Muse with your computer, follow these steps:

1. Switch Muse into Pairing Mode by holding the button down for ~5 seconds. The light should start flashing.
2. Under *Control Panel/Hardware and Sound*, click on *Add a device*.
3. A Bluetooth device named *Muse<-XXXX>* should appear. Select the Muse device and click *Next*. Remember that *XXXX* (corresponds to the last digits of your Muse's MAC address) as you'll need it when connecting later.
4. Click *Next* when being asked for a passcode.
5. Turn off the Muse by holding the button down for ~2 seconds.

Your computer should now be set up to recognize the Muse!

### 5. Download the code for the workshop

The code for the workshop is based on a few Python scripts that you can find [here](https://github.com/bcimontreal/bci_workshop).
You can download everything as a ```.zip``` file using the button ![downloadzip](fig/download_zip.jpg?raw=true "Download zip button") on the right. You then need to unzip the folder on your computer.

Alternatively, if you have ```git``` installed on your computer, you can clone the repository by calling ```git clone git://github.com/bcimontreal/bci_workshop.git``` in the command line.


## Exercise 1: A simple neurofeedback interface

In this first exercise, we will learn how to visualize the raw EEG signals that come from the Muse inside a Python application (note that the Muse SDK comes with a great tool for that, *MuseLab*, but we won't be using it here because we want to do everything ourselves!). We will also extract and visualize basic features of the raw EEG signals. This will showcase a first basic use of a Brain-Computer Interface: a so-called neurofeedback interface.

> Neurofeedback (also called neurotherapy or neurobiofeedback) uses real-time representation of brain-activity (as sound and visual effects) to teach users to control their brain activity.

### E1.1 Streaming data from the Muse

1. Switch on the Muse by holding the button down for ~1 second. The light should start oscillating.
2. From the command line or a terminal, call *muse-io* (replace the ```XXXX``` by your Muse's number as found at step 3. Pairing the Muse) : ```muse-io --device Muse-XXXX --osc osc.udp://localhost:5000```

If everything worked, you should see the connexion status displayed in the command line window. All incoming data (EEG, accelerometer, etc.) is now being broadcast on your local computer at UDP port 5000.

More details are available on the [official Muse Developer website](http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers).

### E1.2 Running the Python visualization script

1. Open the script ```exercise_museio_01.py``` in the text editor of your choice.
2. Read the code - it is thoroughly commented - and modify the experiment parameters as you wish (line 32 to 48).
3. Run the script. If you use Spyder, select a Python console on the bottom right of the screen, then click on the *Run File* button on top of the editor.
4. Two figures should appear: One displaying the raw signals of the Muse's 4 EEG sensors, and another one showing the basic band power features we are computing on one of the EEG signals.
5. To stop the execution of the script, press <Ctrl+C> in the Python console (don't forget MuLES is still running as well!).

![ex1_figures](fig/ex1_figures.png?raw=true "Visualization in E1.2")

### E1.3 Playing around

Here are some things we suggest you do to understand what the script does.

#### Visualizing your raw EEG signals

Run the script and look at the first figure (raw EEG visualization). What makes your signal change?

1. Try blinking, clenching your jaw, moving your head, etc.
2. Imagine repeatedly throwing a ball for a few seconds, then imagine talking to a good friend for another few seconds, while minimizing any movement or blinks.

In the first case, you can see that the first movements (blinking, etc.) strongly disturb the EEG signal. We call these **artifacts**. Some artifacts are so huge that they can completely obscure the actual EEG signal coming from your brain. We typically divide artifacts according to their source: *physiological artifacts* (caused by the electrical activity of the heart, muscles, movement of the eyes, etc.), and *motion artifacts* (caused by a relative displacement of the sensor and the skin).

In the second case, you can see that different mental activities (e.g. imagining eating or talking) are not easily recognizable in the EEG signals. 
First, this is because mental activity is distributed across the brain: for example, sensorimotor processing occurs on top of the brain, in the central cortex, while speech-related functions occurs at the sides of the brain, in the temporal cortex. Therefore, the 4 sensors on the Muse are not necessarily on the right "spot" to capture those EEG signals.
Second, the EEG signals are very, very, very noisy. Indeed, the electrical signals that we pick up on the scalp are smeared by the skull, muscles and skin. As you saw, eye balling the signals is often not enough to analyze brain activity. (That is why we need to extract descriptive characteristics from the signals: what we call features!)

#### Visualizing your EEG features

Since the raw EEG signals are not easy to read, we will extract **features** that will hopefully be more insightful. Features are simply a different representation, or an individual measurable property, of the EEG signal. Good features give clearer information about a phenomenon being observed.

The most often used features to describe EEG are frequency band powers.

1. Open the script ```bci_workshop_tools.py```.
2. Locate the function ```compute_feature_vector()``` (line 87).

This function uses the [Fast Fourier Transform](http://en.wikipedia.org/wiki/Fast_Fourier_transform), an algorithm that extracts the frequency information of a time signal. It transforms the EEG time series (i.e., the raw EEG signal that you visualized above) into a list of amplitudes each corresponding to a specific frequency.

In EEG analysis, we typically look at ranges of frequencies, that we call *frequency bands*:

- Delta (< 4 Hz)
- Theta (4-7 Hz)
- Alpha (8-15 Hz)
- Beta  (16-31 Hz)
- Gamma (> 31 Hz)

These are the features that you visualized in E1.2 in Figure 2.

We expect each band to reflect specific mental activities. For example, we know that closing the eyes and relaxing provokes an increase in Alpha band activity and a decrease in Beta band activity, especially at the back of the head. We will try to reproduce this result now.

1. Open the script ```exercise_01_one_channel.py```.
2. Change the value of the ```eeg_buffer_secs``` parameter to around 40.
3. Run the script and look at the second figure.
4. Keep your eyes open for 20 seconds (again, try to minimize your movements).
5. Close your eyes and relax for another 20 seconds (minimize your movements).

Do you see a difference between the first and the last 20-s windows for the Alpha and Beta features?

#### Advanced: computing supplementary features

Many other features can be used to describe the EEG activity: band powers, Auto-Regressive model coefficients, Wavelet coefficients, coherence, mutual information, etc. As a starting point, adapt the code in the ```compute_feature_vector()``` function to compute additional, finer bands, i.e. low Alpha, medium Alpha, high Alpha, low Beta, and high Beta:

- Low Alpha (8-10 Hz)
- Medium Alpha (9-11 Hz)
- High Alpha (10-12 Hz)
- Low Beta (12-21 Hz)
- High Beta (21-30 Hz)

These bands provide more specific information on the EEG activity, and can be more insightful than standard band powers. Additionally, adapt the code to compute ratios of band powers. For example, Theta/Beta and Alpha/Beta ratios are often used to study EEG.

Repeat the above eyes open/closed procedure with your new features. Can you see a clearer difference between the two mental states?

Other points you can consider to design better features:

* Extract the features for each of the Muse's 4 sensors. Each sensor measures a different part of the brain, and so features from different sensors can again provide more specific information.
* Similarly, ratios of features between different sensors (e.g. Alpha in frontal region/Beta in temporal region) can provide additional useful information.

## Exercise 2: A basic BCI

In this second exercise, we will learn how to use an automatic algorithm to recognize somebody's mental states from their EEG.
We will use a *classifier*: a classifier is an algorithm that, provided some data, learns to recognize patterns, and can then classify similar unseen information.

For example, let's say we have many [images of either cats or dogs that we want to classify](https://www.kaggle.com/c/dogs-vs-cats). A classifier would first require *training data*: in this case we could give the classifier 1000 pictures of cats that we identify as cats, and 1000 pictures of dogs that we identify as dogs. The classifier will then learn specific patterns to discriminate a dog from a cat. Once it is trained, the classifier can now output *decisions*: if we give it a new, unseen picture, it will try its best to correctly determine whether it's a cat or a dog in the picture.

In a Brain-Computer Interface, we use classifiers to identify which type of mental task somebody is doing. For example, in the previous exercise, you saw that opening and closing your eyes modifies the features of the EEG signal. To use a classifier, we would need to proceed like this:

1. Collect EEG data of you performing the two mental activities (eyes open and eyes closed).
2. Input this data to the classifier, while specifying which part corresponds to each mental activity.
3. *Train* the classifier.
4. Use the trained classifier by giving it new EEG data, and asking for a decision on which mental activity this represents.

Brain-Computer Interfaces rely heavily on **machine learning**, the field devoted to building classifiers (and other cool stuff). You might have already understood why: in a typical EEG application we have several features (e.g. many band powers) and the mental activity we want to classify is not easily recognizable.

Let's try it now.

### E2.1 Running the Python basic BCI script

1. Open the script ```exercise_02.py```.
2. Read the code - it is thoroughly commented - and modify the experiment parameters as you wish. You will see it's very similar to the code of Exercise 1, but with a few new sections.
3. When you feel confident about what the code does, run the script.
4. When you hear a **first beep**; keep your eyes open and concentrate (while minimizing your movements).
5. When you hear a **second beep**; close your eyes and relax (while minimizing your movements).
6. When you hear a **third beep**, the classifier is trained and starts outputting decisions in the Python console: ```0``` when your eyes are open, and ```1``` when you close them. Additionally, a figure will display the decisions over a period of 30 seconds.
7. To stop the execution of the script, press <Ctrl+C> in the Python console (don't forget MuLES is still running as well!).

![ex1_figures](fig/ex2_figure.png?raw=true "Visualization of decisions in E2.1")

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

For example, you could send the classifier's decisions to a Processing script to create simple animations based on your mental activity.

## Conclusion

In this workshop, we saw 1) how to run a simple neurofeedback interface, and 2) use a basic brain-computer interface. To do so, we covered the basic principles behind the use of electroencephalography signals in modern BCI applications: properties of the raw EEG time series, extraction of band power features, physiological and motion artifacts, and machine learning-based classification of mental activities.

We used the following tools in this workshop: the MuLES EEG server, the Python scripting language, and the Muse EEG headset. All the necessary scripts for this workshop are available [online](https://github.com/bcimontreal/bci_workshop) and their re-use is strongly encouraged. 

Now is **your turn** to come up with inventive ways of using neurophysiological data! You can follow the pointers in the *References* section for inspiration.

## References

### Tutorials and neurohacks
- A blog with very cool and detailed posts about EEG/BCI hacking: [http://eeghacker.blogspot.ca/](http://eeghacker.blogspot.ca/)
- The [neuralDrift](http://neuraldrift.net/), a neurogame based in MATLAB that exploits the same concept as was seen in this workshop: [https://github.com/hubertjb/neuraldrift](https://github.com/hubertjb/neuraldrift)
- Series of introductory lectures on Brain-Computer Interfacing: [http://sccn.ucsd.edu/wiki/Introduction_To_Modern_Brain-Computer_Interface_Design](http://sccn.ucsd.edu/wiki/Introduction_To_Modern_Brain-Computer_Interface_Design)


## Authors

Hubert Banville & Raymundo Cassani

Thanks to the [MuSAE Lab](http://musaelab.ca/), [District 3](http://d3center.ca/) and [BCI Montréal](http://bcimontreal.org/). Thanks also to Ana, Sydney, Rohit and William for initial feedback on the workshop. 

If you use code from this workshop please don't forget to follow the terms of the [MIT License](http://opensource.org/licenses/MIT).