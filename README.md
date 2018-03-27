# Python Sentiment Service SSE for Qlik Sense

## REQUIREMENTS

- **Assuming prerequisite: [Python with Qlik Sense AAI – Environment Setup](https://www.dropbox.com/s/dhmd3vm7oqurn2m/DPI%20-%20Qlik%20Sense%20AAI%20and%20Python%20Environment%20Setup.pdf?dl=0)**
	- This is not mandatory and is intended for those who are not as familiar with Python to setup a virtual environment. Feel free to follow the below instructions flexibly if you have experience.
- Qlik Sense February 2018+
- Python 3.5.3 64 bit
- Python Libraries: grpcio, vaderSentiment, requests

## LAYOUT

- [Prepare your Project Directory](#prepare-your-project-directory)
- [Install Python Libraries and Required Software](#install-python-libraries-and-required-software)
- [Setup an AAI Connection in the QMC](#setup-an-aai-connection-in-the-qmc)
- [Copy the Package Contents and Import Examples](#copy-the-package-contents-and-import-examples)
- [Prepare And Start Services](#prepare-and-start-services)
- [Leverage Sentiment Analysis from within Qlik Sense](#leverage-sentiment-analysis-from-within-qlik-sense)

 
## PREPARE YOUR PROJECT DIRECTORY
>### <span style="color:red">ALERT</span>
><span style="color:red">
>Virtual environments are not necessary, but are frequently considered a best practice when handling multiple Python projects.
></span>

1. Open a command prompt
2. Make a new project folder called QlikSenseAAI, where all of our projects will live that leverage the QlikSenseAAI virtual environment that we’ve created. Let’s place it under ‘C:\Users\{Your Username}’. If you have already created this folder in another guide, simply skip this step.

3. We now want to leverage our virtual environment. If you are not already in your environment, enter it by executing:

```shell
$ workon QlikSenseAAI
```

4. Now, ensuring you are in the ‘QlikSenseAAI’ folder that you created (if you have followed another guide, it might redirect you to a prior working directory if you've set a default, execute the following commands to create and navigate into your project’s folder structure:
```
$ cd QlikSenseAAI
$ mkdir Sentiment
$ cd Sentiment
```


5. Optionally, you can bind the current working directory as the virtual environment’s default. Execute (Note the period!):
```shell
$ setprojectdir .
```
6. We have now set the stage for our Sentiment environment. To navigate back into this project in the future, simply execute:
```shell
$ workon QlikSenseAAI
```

This will take you back into the environment with the default directory that we set above. To change the
directory for future projects within the same environment, change your directory to the desired path and reset
the working directory with ‘setprojectdir .’


## INSTALL PYTHON LIBRARIES AND REQUIRED SOFTWARE

1. Open a command prompt or continue in your current command prompt, ensuring that you are currently within the virtual environment—you will see (QlikSenseAAI) preceding the directory if so. If you are not, execute:
```shell
$ workon QlikSenseAAI
```
2. Execute the following commands. If you have followed a previous guide, you have more than likely already installed grpcio):

```shell
$ pip install grpcio
$ pip install vaderSentiment
$ pip install requests
```

## SET UP AN AAI CONNECTION IN THE QMC

1. Navigate to the QMC and select ‘Analytic connections’
2. Fill in the **Name**, **Host**, and **Port** parameters -- these are mandatory.
    - **Name** is the alias for the analytic connection. For the example qvf to work without modifications, name it 'PythonSentiment'
    - **Host** is the location of where the service is running. If you installed this locally, you can use 'localhost'
    - **Port** is the target port in which the service is running. This module is setup to run on 50055, however that can be easily modified by searching for ‘-port’ in the ‘\_\_main\_\_.py’ file and changing the ‘default’ parameter to an available port.
3. Click ‘Apply’, and you’ve now created a new analytics connection.


## COPY THE PACKAGE CONTENTS AND IMPORT EXAMPLES

1. Now we want to setup our sentiment service and app. Let’s start by copying over the contents of the example
    from this package to the ‘..\QlikSenseAAI\Sentiment\’ location. Alternatively you can simply clone the repository.
2. After copying over the contents, go ahead and import the example qvfs found [here](https://www.dropbox.com/s/3v3usx6afav30te/AAI%20-%20Python%20VADER%20Sentiment.qvf?dl=0) and [here](https://www.dropbox.com/s/2hjkitfawlnvhya/AAI%20-%20Python%20VADER%20Sentiment%20Script.qvf?dl=0).
3. Lastly, import the qsvariable extension zip file found [here](https://github.com/erikwett/qsVariable) using the QMC.


## PREPARE AND START SERVICES

1. At this point the setup is complete, and we now need to start the sentiment extension service. To do so, navigate back to the command prompt. Please make sure that you are inside of the virtual environment.
2. Once at the command prompt and within your environment, execute (note two underscores on each side):
```shell
$ python __main__.py
```
3. We now need to restart the Qlik Sense engine service so that it can register the new AAI service. To do so,
    navigate to windows Services and restart the ‘Qlik Sense Engine Service’
4. You should now see in the command prompt that the Qlik Sense Engine has registered the functions *Sentiment()*, *SentimentScript()*, *CleanTweet()*, and *CleanTweetScript()* from the extension service over port 50055, or whichever port you’ve chosen to leverage.


## LEVERAGE SENTIMENT ANALYSIS FROM WITHIN SENSE

1. The *Sentiment()* function leverages the [VADER Sentiment package](https://github.com/cjhutto/vaderSentiment) and accepts two mandatory arguments:
    - *Text (string)*: i.e. a sentence, paragraph, etc
    - *Score (string)*: this is what type of data you'd like to return and can be:
    	- *all* - returns the raw result containing all information (pipe delimited)
    	- *pos* - returns the positive polarity
    	- *neg* - returns the negative polarity
    	- *neu* - returns the neutral polarity
    	- *compound* - returns the compound (overall) polarity
2. Example function calls:
	
    *Returns all sentiment scores pipe delimited*:
    ``` PythonSentiment.Sentiment(text,'all') ``` 
    
    *Returns the positive polarity score*:
    ``` PythonSentiment.Sentiment(text,'pos') ```
3. There is another script function exposed called *SentimentScript()*. This function can only be used in the script and is leveraged via the [**LOAD ... EXTENSION ...**](https://help.qlik.com/en-US/sense/February2018/Subsystems/Hub/Content/Scripting/ScriptRegularStatements/Load.htm) mechanism which was added as of the February 2018 release of Qlik Sense. This function takes two fields:
       
       id (numeric), text

See the below example of how to utilize the *SentimentScript()* function in the load script:

*Note you can also use the *Sentiment()* function in the script like any other native function, but it will operate record by record (*Scalar*) vs in one call (*Tensor*) as seen below:

```
Articles:
LOAD
    ID,
    "Article Author",
    "Article Title",
    "Article Description",
    "Article Url",
    "Article Image",
    "Article Published At",
    "Source ID",
    "Article Published Timestamp",
    "Article Published Date",
    "Article Published Month",
    "Article Published Day",
    "Article Published Year",
    "Article Published Quarter",
    "Article Published Week",
    "Article Published Hour",
    "Article Published Minute",
    "Article Published Second",
    "Article Published YearMonth"
FROM [lib://Qonnections (qlik_qservice)/QVDs\ArticleTitlesForSentimentAnalysis.qvd](qvd);

// TENSOR
ArticleSentiment:
LOAD
	*,
	If([Article Title Sentiment - Compound]<=-.66,'Very Negative',
    If([Article Title Sentiment - Compound]<=-.33,'Negative',
    If([Article Title Sentiment - Compound]<=-0,'Somewhat Negative',
    If([Article Title Sentiment - Compound]<=.33,'Somewhat Positive',
    If([Article Title Sentiment - Compound]<=.66,'Positive','Very Positive'))))) AS "Article Title Sentiment - Compound Buckets"
    ;
LOAD
	*,
    TextBetween("Article Title Sentiment",'neg: ','|') AS "Article Title Sentiment - Negative",
    TextBetween("Article Title Sentiment",'compound: ','|') AS "Article Title Sentiment - Compound",
    TextBetween("Article Title Sentiment",'pos: ','|') AS "Article Title Sentiment - Positive",
    TextBetween("Article Title Sentiment",'neu: ','|') AS "Article Title Sentiment - Neutral"
    ;
LOAD
	Field1 AS ID,
	Field2 AS "Article Title Sentiment"
EXTENSION PythonSentiment.SentimentScript(Articles{"ID","Article Title"});
```

**You more than likely want to use this sentiment package in the script, as the data will not be changing, therefore there is no benefit to real-time analysis on the front-end.**


4. As you saw above, there are two additional functions that I've included that are intended for use with Twitter data. I have not provided examples of these functions in the qvfs.
	- The *CleanTweet()* function applies a regular expression that is designed to cleanse tweets down to just the text.
		- Example ``` PythonSentiment.CleanTweet(text) ```
	- The *CleanTweetScript()* function is the same function but for load script use. It takes a numeric id and text.
		- Example below of first cleaning the tweet and then running sentiment analysis on it in the script

```
// CLEAN TWEETS IN BULK USING REGEX IN PYTHON
PythonRegexSentiment:
LOAD
	Field1 AS ID,
    Field2 AS CleansedTweet 
EXTENSION PythonSentiment.CleanTweetScript(TextData{"ID","Text"});

// RUN SENTIMENT ANALYSIS ON CLEANSED TWEETS
LEFT JOIN(PythonRegexSentiment)
LOAD
	*,
    TextBetween("Tweet Sentiment",'neg: ','|') AS 		"Tweet Sentiment - Negative",
    TextBetween("Tweet Sentiment",'compound: ','|') AS 	"Tweet Sentiment - Compound",
    TextBetween("Tweet Sentiment",'pos: ','|') AS 		"Tweet Sentiment - Positive",
    TextBetween("Tweet Sentiment",'neu: ','|') AS 		"Tweet Sentiment - Neutral"
    ;
LOAD
	Field1 AS ID,
	Field2 AS "Tweet Sentiment"
EXTENSION PythonSentiment.SentimentScript(PythonRegexSentiment{"ID","CleansedTweet"});
```