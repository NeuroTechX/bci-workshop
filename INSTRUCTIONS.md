c# BCI workshop - NeuroTechTO

This document will lead users through NeuroTechX's introductory BCI Workshop.

This workshop is intended for people with no or limited experience with Brain-Computer Interfaces (BCIs). The workshop will teach them the basic principles that are necessary to "hack" and develop new applications with BCIs: background on brain activity and brain activity measurement with EEG, structure of a BCI, feature extraction and machine learning. Two hands-on exercises will allow the participants to 1) visualize their EEG signals and some relevant features, and 2) experiment with a very simple BCI design. This should give the participants sufficient knowledge to understand the advantages and limitations of current BCIs, and to devise their own applications.

## Programming languages for the workshop exercises

This version of the workshop currently only supports **Python** 3. (The [original version](https://github.com/NeuroTechX/bci-workshop) also supports MATLAB and GNU Octave, but only works on Windows).
Python is a very popular, multi-purpose powerful, free, open and simple to read scripting language.

## Supported operating systems

The workshop has been tested and works on Ubuntu 17.10, Windows 10, and macOS.

## Required hardware for the workshop

The [Muse 2016](http://www.choosemuse.com/research/) model is required for this version of the workshop. However, the [original version of the workshop](https://github.com/NeuroTechX/bci-workshop) works with many different consumer EEG devices.

![muse_diagram](fig/muse.png?raw=true "The Muse EEG headband.")

If you are working on macOS or Windows, you will also need a BLED112 Bluetooth dongle.

## A. Installation of software for the workshop

There are many other programming languages ( C, C++, Java, Processing, etc.); a diversity of **BCI toolboxes** ([OpenVIBE](http://openvibe.inria.fr/), [BCI2000](http://www.bci2000.org/wiki/index.php/Main_Page), [BCILAB](http://sccn.ucsd.edu/wiki/BCILAB), etc.); and of course **other EEG devices** (OpenBCI, Emotiv EPOC, Neurosky Mindwave, etc.).

Among those, we chose the **Python-`muse-lsl`-Muse** combination as it provides a lot of flexibility to hackers, but at the same time is simple enough that novice users can understand what they are doing. Keep in mind though that the goal of this workshop is to teach you about BCIs in general, so that you are able to apply this knowledge to the environment and tools of your choice. We won't focus much on tools here.

These are the steps to setup your computer

**A.1.** Installing Python and required packages
**A.2.** Download the code for the workshop
**A.3.** Pairing the Muse EEG headset with `muse-lsl`

### A.1 Installing Python and required packages

Python is a high-level scripting language that has been widely adopted in a many fields. It is open, free, simple to read, and has an extensive standard library. Many packages can also be downloaded online to complement its features.

Two packages are especially useful when dealing with scientific computing (as for BCIs): [`numpy`](http://www.numpy.org/) and [`matplotlib`](http://matplotlib.org/). `numpy` allows easy manipulation of arrays and matrices (very similar to [MATLAB](http://mathesaurus.sourceforge.net/matlab-numpy.html)), which is necessary when dealing with data such as neurophysiological signals. `matplotlib` is similar to MATLAB's plotting functionalities, and can be used to visualize the signals and features we will be working with.

Other packages we will use in this workshop are:

* [`pylsl`](https://pypi.python.org/pypi/pylsl): the Python interface to the [Lab Streaming Layer](https://github.com/sccn/labstreaminglayer) (LSL), a protocol for real-time streaming of time series data over a network.
* [`muse-lsl`](https://github.com/alexandrebarachant/muse-lsl): a pure-Python library to connect to a Muse headband and stream data using `pylsl`,
* [`scikit-learn`](http://scikit-learn.org/stable/): a machine learning library.

To install Python 3 and some of these required packages, we suggest you download and install the [Anaconda distribution](http://continuum.io/downloads). Anaconda is a Python distribution that includes Python 3.6 (in the case of Anaconda 3), most of the packages we will need for the workshop (as well as plenty other useful packages), and [Spyder](https://pythonhosted.org/spyder/), a great IDE for scientific computing in Python.

#### Installation of Python with Anaconda (recommended)

1. Download the [Anaconda graphical installer](http://continuum.io/downloads) (if your OS version is 32-bit, make sure to download the 32-bit installer).
2. Follow the instructions to install.

This installs Python, Spyder and some of the packages we will need for the workshop (`numpy`, `matplotlib` and `scikit-learn`).

#### Individual installation of Python and packages (optional)

Alternatively, you can [download Python 3.6 independently](https://www.python.org/downloads/). Make sure to install `pip` and then grab `numpy`, `matplotlib` and ``scikit-learn`` by calling ```pip install <package_name>``` in the command line (or any other way you prefer). Make sure you have a text editor or IDE you can work with as well.

#### Installation of additional Python packages

Run the following command in a terminal __*__ to install `pygatt` and `pylsl`:

```
pip install git+https://github.com/peplin/pygatt pylsl
```

__*__ The way to open a terminal depends on your OS. On Windows, press <kbd>Windows</kbd> + <kbd>R</kbd>, type `cmd`, and then press <kbd>Enter</kbd>. On macOS, press <kbd>spacebar</kbd>, type `terminal`, and press <kbd>Enter</kbd>. On Ubuntu, <kbd>Ctrl</kbd>+<kbd>alt</kbd>+<kbd>T</kbd> will open a terminal.

### A.2. Download the code for the workshop

The code for the workshop consists of Python scripts that you can find [here](https://github.com/jdpigeon/bci-workshop).
You can download everything as a ```.zip``` file using the button ![downloadzip](fig/download_zip.jpg?raw=true "Download zip button") on the right. You then need to unzip the folder on your computer.

Alternatively, if you have ```git``` installed on your computer, you can clone the repository by calling ```git clone https://github.com/jdpigeon/bci-workshop.git``` in a terminal.

### A.3. Connecting the Muse to `muse-lsl`

To figure out the name of your Muse, look for the last 4 digits on the inner left part of the headband. The headband name will then just be `Muse-<LAST 4 DIGITS>`, e.g., `Muse-0A14`. Alternatively, if you are on Linux, you can use `hcitool` to find your devices's MAC address: ```sudo hcitool lescan```.

With your Muse turned on, you should now be able to connect to it with your computer by running `muse-lsl` Python script with the name of your headset in a terminal:

```python muse-lsl.py --name <YOUR_DEVICE_NAME>```

You can also directly pass the MAC address if you found it with `hcitool` or by some other way (this option is faster at startup):

```python muse-lsl.py --address <YOUR_DEVICE_ADDRESS>```

Depending on your OS and hardware, you might need to repeat this command a few times before the connection is established.

Once the stream is up and running, you can test the stream by calling the following in another terminal:

```python lsl-viewer.py```

![ex1_figures](fig/lsl_viewer.png?raw=true "Visualizing EEG with `lsl-viewer.py`")

## Exercise 1: A simple neurofeedback interface

In this first exercise, we will learn how to visualize the raw EEG signals that come from the Muse inside a Python application. We will also extract and visualize basic features of the raw EEG signals. This will showcase a first basic use of a Brain-Computer Interface: a so-called neurofeedback interface.

> Neurofeedback (also called neurotherapy or neurobiofeedback) uses real-time representation of brain-activity (e.g., as sound or visual effects) to teach users to control their brain activity.

### E1.1 Running Exercise 1 script

1. Open the script ```exercise_01.py``` in **Spyder** or the text editor of your choice.
2. Read the code - it is thoroughly commented - and modify the experiment parameters as you wish in the **2. SET EXPERIMENTAL PARAMETERS** section.
3. Run the script. In **Spyder**, select an IPython console on the bottom right of the screen, then click on the *Run File* button on top of the editor.
4. Two figures should appear: one displaying the raw signals of the Muse's 4 EEG sensors, and another one showing the basic band power features we are computing on one of the EEG signals. __**__
5. To stop the execution of the script, press <kbd>Ctrl</kbd>+<kbd>C</kbd> in the IPython console.

![ex1_figures](fig/ex1_figures_new.png?raw=true "Visualization in E1.1")

__**__ If you are using **Spyder** and are not seeing the two figures, you might have to setup the IPython console differently. Using the top dropdown menu, open up the `Preferences` dialog. Then, under the `IPython console` section, click on the `Graphics` tab, and change the backend to `Automatic`.

### E1.2 Playing around

Here are some things we suggest you do to understand what the script does.

#### Visualizing your raw EEG signals

Run the script and look at the first figure (raw EEG visualization). What makes your signal change?

1. Try blinking, clenching your jaw, moving your head, etc.
2. Imagine repeatedly throwing a ball for a few seconds, then imagine talking to a good friend for another few seconds, while minimizing any movement or blinks.

In the first case, you can see that the first movements (blinking, etc.) strongly disturb the EEG signal. We call these **artifacts**. Some artifacts are so huge that they can completely obscure the actual EEG signal coming from your brain. We typically divide artifacts according to their source: *physiological artifacts* (caused by the electrical activity of the heart, muscles, movement of the eyes, etc.), and *motion artifacts* (caused by a relative displacement of the sensor and the skin).

In the second case, you can see that different mental activities (e.g. imagining eating or talking) are not easily recognizable in the EEG signals.
First, this is because mental activity is distributed across the brain: for example, sensorimotor processing occurs on top of the brain, in the central cortex, while speech-related functions occurs at the sides of the brain, in the temporal cortex. Therefore, the 4 sensors on the Muse are not necessarily on the right "spot" to capture those EEG signals.
Second, EEG is very, very, very noisy. Indeed, the electrical signals that we pick up on the scalp are "smeared" by the skull, muscles and skin. As you saw, eye balling the signals is often not enough to analyze brain activity. (That is why we need to extract descriptive characteristics from the signals -- what we call features!)

#### Visualizing your EEG features

Since the raw EEG signals are not easy to read, we will extract **features** that will hopefully be more insightful. Features are simply a different representation, or an individual measurable property, of the EEG signal. Good features give clearer information about a phenomenon being observed.

The most often used features to describe EEG are frequency band powers.

1. Open the script ```bci_workshop_tools.py```.
2. Locate the function ```compute_feature_vector()```.

This function uses the [Fast Fourier Transform](http://en.wikipedia.org/wiki/Fast_Fourier_transform), an algorithm that extracts the frequency information of a time signal. It transforms the EEG time series (i.e., the raw EEG signal that you visualized above) into a list of amplitudes each corresponding to a specific frequency.

In EEG analysis, we typically look at ranges of frequencies, that we call *frequency bands*:

- Delta (< 4 Hz)
- Theta (4-7 Hz)
- Alpha (8-15 Hz)
- Beta  (16-31 Hz)
- Gamma (> 31 Hz)

These are the features that you visualized in E1.1 in Figure 2.

We expect each band to loosely reflect different mental activities. For example, we know that closing one's eyes and relaxing provokes an increase in Alpha band activity and a decrease in Beta band activity, especially at the back of the head. This is thought to be due to the quieting down of areas of the brain involved in processing visual information. We will try to reproduce this result now.

1. Open the script ```exercise_01.py```.
2. Change the value of the ```buffer_length``` parameter to around 40.
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

* Extract the features for each of the Muse's 4 sensors. Each sensor measures brain activity from different parts of the brain with different strengths, and so features from different sensors can provide more specific information.
* Similarly, ratios of features between different sensors (e.g. Alpha in frontal region/Beta in temporal region) can provide additional useful information.

## Exercise 2: A basic BCI

In this second exercise, we will learn how to use an automatic algorithm called a *classifier* to recognize somebody's mental states from their EEG.

> A *classifier* is an algorithm that, provided some data, learns to recognize patterns. A well-trained classifier can then be used to classify similar, but never-before-seen data.

For example, let's say we have many [images of either cats or dogs that we want to classify](https://www.kaggle.com/c/dogs-vs-cats). A classifier would first require *training data*: in this case we could give the classifier 1000 pictures of cats that we identify as cats, and 1000 pictures of dogs that we identify as dogs. The classifier will then learn specific patterns to discriminate a dog from a cat. Once it is trained, the classifier can now output *decisions*: if we give it a new, unseen picture, it will try its best to correctly determine whether the picture contains a cat or a dog.

In a Brain-Computer Interface, we might use classifiers to identify what type of mental operation someone is performing. For example, in the previous exercise, you saw that opening and closing your eyes modifies the features of the EEG signal. To use a classifier, we would need to proceed like this:

1. Collect EEG data of a user performing two mental activities (e.g. eyes open vs eyes closed, reading vs relaxing).
2. Input this data to the classifier, while specifying which data corresponds to which mental activity.
3. *Train* the classifier.
4. Use the trained classifier by giving it new EEG data, and asking for a decision on which mental activity this represents.

Brain-Computer Interfaces rely heavily on **machine learning**, the field devoted to algorithms that learn from data, such as classifiers. You might have already understood why: in a typical EEG application we have several features (e.g. many band powers) and we might not know *a priori* what the mental activity we need to classify looks like. Letting the machine find the optimal combination of features by itself simplifies the whole process.

Let's try it now.

### E2.1 Running the Python basic BCI script

1. Open the script ```exercise_02.py```.
2. Read the code - it is thoroughly commented - and modify the experiment parameters as you wish in the **Set the experiment parameters section**. You will see it's very similar to the code of **Exercise 1**, but with a few new sections.
3. When you feel confident about what the code does, run the script.
4. When you hear a **first beep**; keep your eyes open and concentrate (while minimizing your movements).
5. When you hear a **second beep**; close your eyes and relax (while minimizing your movements).
6. When you hear a **third beep**, the classifier is trained and starts outputting decisions in the IPython console: ```0``` when your eyes are open, and ```1``` when you close them. Additionally, a figure will display the decisions over a period of 30 seconds.
7. To stop the execution of the script, press <kbd>Ctrl</kbd>+<kbd>C</kbd> in the IPython console.

![ex2_figures](fig/decision_plotter.png?raw=true "Visualization of decisions in E2.1")

### E2.2 Playing around

Here are some things we suggest you do to understand what the script does.

#### Visualizing the classifier decisions

Try the above procedure to train and use the classifier. If it does not work well, make sure the EEG signals are stable (you can reuse the code of Exercise 1 to visualize the raw signals) and try again. Some people will typically have a stronger Alpha response than others, and it also takes practice to be able to modulate it at will.

#### Using other mental tasks

Try the same procedure again, but train your classifier with different mental activities. For example, perform some random mental mutliplication during the first 20 seconds, and try to come up with as many words as possible starting with the letter *T* during the next 20 seconds. Once the classifier is trained, repeat the two mental tasks. Is the classifier able to recognize the task you are performing?

Additionally, try the first training procedure again (concentration  vs. relaxation). However, don't close your eyes during the second task; instead, relax with your eyes open. Can the classifier recognize your mental state?

#### Machine learning tricks and other considerations

If you have some experience with machine learning or are interested by the topic, consider adding the following things to the script:

* Get an estimate of the classifier's performance by dividing the data into training and testing sets. Perhaps cross-validation would be informative with such a small data set?
* How much data is necessary to attain stable performance?
* Can a classifier trained with one person's data be used on someone else?
* Visualize the importance of each feature. Are the most important features the one you expect?
* Run model selection and hyperparameter search. Can you find an algorithm that is better suited to our task? (This is relatively easy to perform with the [TPOT](https://github.com/rhiever/tpot) library)

Also, keeping in mind our earlier discussion of **artefacts**, what is the impact of artefacts during training and/or live testing?

#### Sending decisions to an external application

Once your BCI framework is functional, you can start thinking about sending your EEG features or classifier decisions to an external application. Many different libraries can be used for that, including standard TCP/IP communication implementations (e.g. Python's [socket](https://docs.python.org/3/library/socket.html) module). Another option is [`pyZMQ`](https://zeromq.github.io/pyzmq/), which allows simple communication between a Python application and any programming language supporting the [ZMQ](http://zeromq.org/) protocol.

One idea you could work on would be sending the classifier's decisions to a [`Processing`](https://processing.org/) script to create simple animations based on your mental activity. Or how about sending the information to a Unity environment to create a brain-sensing video game?

## Conclusion

In this workshop, we saw **1)** how to run a simple neurofeedback interface, and **2)** use a basic Brain-Computer Interface. To do so, we covered the basic principles behind the use of electroencephalography signals in modern BCI applications: properties of the raw EEG time series, extraction of band power features, physiological and motion artifacts, and machine learning-based classification of mental activities.

We used the following tools in this workshop: the **Python** scripting language and the **Muse EEG headset**. All the necessary scripts for this workshop are available [online](https://github.com/NeuroTechX/bci-workshop) and their re-use is strongly encouraged.

Now is **your turn** to come up with inventive ways of using neurophysiological data! You can follow the pointers in the *References* section for inspiration.

## References

### Tutorials and neurohacks
- A blog with very cool and detailed posts about EEG/BCI hacking: [http://eeghacker.blogspot.ca/](http://eeghacker.blogspot.ca/)
- The [neuralDrift](http://neuraldrift.net/), a neurogame based in MATLAB that exploits the same concept as was seen in this workshop: [https://github.com/hubertjb/neuraldrift](https://github.com/hubertjb/neuraldrift)
- Series of introductory lectures on Brain-Computer Interfacing: [http://sccn.ucsd.edu/wiki/Introduction_To_Modern_Brain-Computer_Interface_Design](http://sccn.ucsd.edu/wiki/Introduction_To_Modern_Brain-Computer_Interface_Design)
- A visualizer in [Unity](https://github.com/syswsi/BCI_Experiments)
- [Using spotify and the Muse](https://github.com/eisendrachen00/musemusic)
- Other NeurotechX [resource](https://github.com/NeuroTechX/awesome-bci)

## Authors

* Original version (2015): Hubert Banville & Raymundo Cassani
* Current version (September 2017): updated by Hubert Banville & Dano Morrison

If you use code from this workshop please don't forget to follow the terms of the [MIT License](http://opensource.org/licenses/MIT).
