# Buzzboard

## Description
Model application with simple ML filter for OWASP Night Tokyo 2016

This is a special web application, which illustrates implementation of machine learning filters for users activity.
Basically it is a Decision Tree classifier for HTTP requests features.

## Installation

You need a Python 3.5 with ScikitLearn for this application. I'd recommend to install Anaconda IDE, because it has all libraries for this project (https://www.continuum.io/downloads).

Also as simple database this application needs Redis on localhost (with default parameters, take it on http://redis.io/download).

You also should define ReCAPTCHA API keys in settings.py file.

