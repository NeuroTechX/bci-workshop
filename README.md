## README

This is my fork of the workshop code that sends relaxation and focus metrics to vrchat avatar paramaters via OSC

**Demos** 
- [VRCHAT OSC MAGIC! (Last 30 seconds)](https://twitter.com/kentrl_z/status/1497020472046800897)
- [Old version of Brain Controlled Ears](https://www.youtube.com/watch?v=WjWc51xNgKg)

**Instructions**
1. See the document `INSTRUCTIONS.md` for instructions on how to prepare your pc hardware, bluetooth, and install the base packages. Specifically: the intro, sections A1 and A2
2. Instead of following section A3, download the [Petal Experimental Metrics App](https://petal.tech/downloads).
3. Turn on your Muse headset and click on Stream in the Petal App. The headset will connect automatically and stream data via LSL
4. Run the script `python\osc_multichannel.py`. That will start sending OSC messages to set Avatar Parameters

**OSC Avatar Parameters**

Avatar parameters being sent are floats that range from -1.0 to 1.0. Negative and Positive values correspond to low and high focus/relaxation. Left and right sides of the brain are measured and can be recieved by VRC seperately. Update your avatar paramaters as needed to influnece animations and the like. Have fun!


- `/avatar/parameters/osc_relax_left`
- `/avatar/parameters/osc_relax_right`
- `/avatar/parameters/osc_focus_left`
- `/avatar/parameters/osc_focus_right`

These paramaters have been deprecated. They will always report the left channels since taking the average of each side of the brain averages the noise as well:

- `/avatar/parameters/osc_relax_avg`
- `/avatar/parameters/osc_focus_avg`

## License
[MIT](http://opensource.org/licenses/MIT).



