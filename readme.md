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
Now if you are same directory then type,
```
myenv\Scripts\activate
```

Creating Python virtualenv on macOS
```
python3 -m venv env
```
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```