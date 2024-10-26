# H8_SDK
H8 SDK

This SDK is for H8 automation. 

1. Setup python venv: "python -m venv venv"
2. source venv/bin/activate
3. pip install --upgrade pip
4. pip install -r requirements.txt
5. Make sure that you have a database created - run createdb.py 
6. Have Fun!

### Info for me! I don't want the venv/ files in the repo.
git add .gitignore
git commit -m "Add venv to .gitignore"
git push

Check that service Web Access is default service group on fortigate
Service ONLY use TCP in the protocol, UDP does not work
