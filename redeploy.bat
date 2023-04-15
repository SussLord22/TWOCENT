@echo off
echo Redeploying your Heroku app...

REM Replace "your-app-name" with your Heroku app's name
set HEROKU_APP_NAME=twocent

REM Add your project files to the Git repository
git add .

REM Commit your changes to the Git repository
git commit -m "Deploying updates to Heroku"

REM Push your changes to Heroku
git push heroku master

echo Your app has been redeployed on Heroku!
