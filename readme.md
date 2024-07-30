# CT-Guided Puncture Assistance System
![mainscreen](https://github.com/natekrth/puncture-system-python/blob/main/mainscreen.png?raw=true)
# Installation the application
1. Open terminal/command prompt
2. Clone the application from Github
```
git clone https://github.com/natekrth/puncture-system-python.git
```
### Creating Python virtualenv in Windows

Prerequisite
- Installed python version 3.10.7
- Using Window 10

Using command prompt

If python is installed in your system, then pip comes in handy. So simple steps are: 
- Install virtualenv using
```
pip install virtualenv
``` 
- Now in which ever directory you are, this line below will create a virtualenv there
```
python -m venv myenv
```
- Now if you are same directory then type to activate the virtual environment
```
myenv\Scripts\activate
```
- Install the application dependencies
```
pip install -r requirements.txt
```

### Creating Python virtualenv on macOS
Prerequisite
- Installed python version 3.10.7
- Using MacOS

Using terminal

- Install virtualenv using
```
pip install virtualenv
```
- Now in which ever directory you are, this line below will create a virtualenv there
```
python3 -m venv env
```
- Upgrade pip
```
python3 -m pip install --upgrade pip
```
- Start virtual environment
```
source ./venv/bin/activate
```
- Install the application dependencies
```
pip install -r requirements.txt
```

# Run the application
1. Open terminal/command prompt  
2. Go to the directory where main.py is in
```
cd puncutre-system-python
```
3. Start the application
- For Windows
```
python main.py
```
- For MacOS
```
python3 main.py
```

# Application Manual
[Application Manual Link](https://docs.google.com/document/d/182j2NCudUOpFVlQWubM5h_SFGsRfmuCIIGO2qvDP7qM/edit?usp=sharing)
