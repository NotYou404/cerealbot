# cerealbot
cerealbot is an open source Discord Bot created by NotYou#2907.


**HOST IT YOURSELF**
*This little guide might partly only work for Windows user*

First decide where you want the folder with the source to be on your local computer.
Here I will choose the Desktop but you can use any other directory, you will just need to change the paths used here.

First open the command prompt by clicking the windows logo and typing `cmd`. Click enter.
Use the command `cd Desktop` to navigate to the desktop. If this doesn't work for you, or you decided to use a different directory, use an absolute path, starting with `C:` (for the C: disc). Don't close the command window yet!

Then to download the source use `git clone https://github.com/NotYou404/cerealbot`. If you get an error that the command git was not found, you need to install git: https://git-scm.com/downloads
After you cloned the repository, leave the command prompt open!

Now you will notice a new folder called `cerealbot`. Inside this folder you create a file called `.env`.
Edit this file and write:
`TOKEN = yourBotToken`
You get the token of your bot in the dev portal where you created it. If you didn't create a bot yet, go to https://discord.com/developers/applications and create one.
If you struggle, please google `creating a discord bot dev portal`.
Now, go back to your command prompt and type `cd cerealbot`. Still, let it open.

The following section requires you to have python. You can check if you have python installed by using the command `python --version` in your command prompt.
If you don't have it yet, install it at https://www.python.org/downloads/.
When you installed python, use the command `python -m venv venv` to create a virtual environment. You command prompt will get a `(venv)` prefix.
Now, you need to install the required dependencies with the command `python -m pip install -r requirements.txt`.

Now you are ready to run the bot, to do so use the command `python main.py`!


**ADDING YOUR OWN FEATURES**
To learn how to add your own features, read the official pycord guide here: https://guide.pycord.dev/popular-topics/subclassing-bots
However it will require you to know at least a bit python.


**IF YOU HAVE ANY QUESTIONS OR GET ANY ERRORS, PLEASE CONTACT ME VIA DISCORD: `NotYou#2907` OR OPEN AN ISSUE!**
