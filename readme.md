## Creating Python virtualenv in Windows

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

## Creating Python virtualenv on macOS
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