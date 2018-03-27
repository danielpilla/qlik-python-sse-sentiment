#! /usr/bin/env python3
import argparse
import json
import logging
import logging.config
import os
import sys
import time
import re
from concurrent import futures
from datetime import datetime

# Add Generated folder to module path.
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PARENT_DIR, 'generated'))

import ServerSideExtension_pb2 as SSE
import grpc
from ssedata import FunctionType
from scripteval import ScriptEval

##IMPORT SENTIMENT ANALYZER
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyser = SentimentIntensityAnalyzer()

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class ExtensionService(SSE.ConnectorServicer):
    """
    A simple SSE-plugin created for the HelloWorld example.
    """

    def __init__(self, funcdef_file):
        """
        Class initializer.
        :param funcdef_file: a function definition JSON file
        """
        self._function_definitions = funcdef_file
        self.ScriptEval = ScriptEval()
        os.makedirs('logs', exist_ok=True)
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logger.config')
        logging.config.fileConfig(log_file)
        logging.info('Logging enabled')

    @property
    def function_definitions(self):
        """
        :return: json file with function definitions
        """
        return self._function_definitions

    @property
    def functions(self):
        """
        :return: Mapping of function id and implementation
        """
        return {
            0: '_sentiment',
            1: '_sentimentScript',
            2: '_cleanTweet',
            3: '_cleanTweetScript'
        }

    @staticmethod
    def _get_function_id(context):
        """
        Retrieve function id from header.
        :param context: context
        :return: function id
        """
        metadata = dict(context.invocation_metadata())
        header = SSE.FunctionRequestHeader()
        header.ParseFromString(metadata['qlik-functionrequestheader-bin'])

        return header.functionId

    """
    Implementation of added functions.
    """

    @staticmethod
    def _sentiment(request, context):
        global analyser
        sentimentList = []
       
        # Iterate over bundled rows
        for request_rows in request:     
            # Iterate over rows
            for row in request_rows.rows:             
                data = [d.strData for d in row.duals][0]

                ## analyse sentiment
                ## score can be: 'all','pos','neg', or 'comp'
                score = [d.strData for d in row.duals][1]
                
                if score=='all':
                    try:
                        sentiment = str(analyser.polarity_scores(str(data)))
                        sentiment = sentiment.replace('{','').replace('}','|').replace("'",'').replace(',','|') 
                    except:
                        sentiment = 'Error: ' + str(sys.exc_info()[0])
                else:
                    try:
                        sentiment = json.loads(str(analyser.polarity_scores(data)).replace("'",'"'))

                        if score=='pos':
                            sentiment = str(sentiment['pos'])
                        elif score=='neg':
                            sentiment = str(sentiment['neg'])
                        elif score=='neu':
                            sentiment = str(sentiment['neu'])
                        else:
                            sentiment = str(sentiment['compound'])
                    except:
                        sentiment = 'Error: ' + str(sys.exc_info()[0])                   
                        
                sentimentList.append(sentiment)

        # Create an iterable of dual with the result
        duals = iter([[SSE.Dual(strData=d)] for d in sentimentList])

        # Yield the row data as bundled rows
        yield SSE.BundledRows(rows=[SSE.Row(duals=d) for d in duals])

    @staticmethod
    def _sentimentScript(request, context):
        global analyser

        idNumList = []
        sentimentList = []
       
        # Iterate over bundled rows
        for request_rows in request:      
            # Iterate over rows
            for row in request_rows.rows:   
                # grab the id             
                idNum = [d.numData for d in row.duals][0]
                idNumList.append(idNum)

                # grab the text and run sentiment
                text = [d.strData for d in row.duals][1]

                try:
                    sentiment = str(analyser.polarity_scores(str(text)))
                except:
                    sentiment = 'Error: ' + str(sys.exc_info()[0])

                sentiment = sentiment.replace('{','').replace('}','|').replace("'",'').replace(',','|')        
                sentimentList.append(sentiment)

        # Create an iterable of dual with the result
        dualsList = []
        dualsList.append([SSE.Dual(numData=d) for d in idNumList])
        dualsList.append([SSE.Dual(strData=d) for d in sentimentList])

        response_rows = []
        for i in range(len(idNumList)):
            duals = [dualsList[z][i] for z in range(len(dualsList))]
            response_rows.append(SSE.Row(duals=iter(duals)))

        # Set and send Table header
        table = SSE.TableDescription(name='Sentiment')
        table.fields.add(dataType=SSE.NUMERIC)
        table.fields.add(dataType=SSE.STRING)
        md = (('qlik-tabledescription-bin', table.SerializeToString()),)
        context.send_initial_metadata(md)

        yield SSE.BundledRows(rows=response_rows)

    @staticmethod
    def _cleanTweet(request, context):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        https://www.geeksforgeeks.org/twitter-sentiment-analysis-using-python/
        '''

        tweetList = []

        # Iterate over bundled rows
        for request_rows in request:
            
            # Iterate over rows
            for row in request_rows.rows:
                        
                tweet = [d.strData for d in row.duals][0]
                tweet = tweet.replace("'",'999999')
                
                if tweet[:2]=='RT':
                    index = tweet.find(':')
                    tweet = tweet[index:]
                    
                tweetCleansed = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
                tweetCleansed = tweetCleansed.replace('999999',"'")
       
                tweetList.append(tweetCleansed)


        # Create an iterable of dual with the result
        duals = iter([[SSE.Dual(strData=d)] for d in tweetList])


        # Yield the row data as bundled rows
        yield SSE.BundledRows(rows=[SSE.Row(duals=d) for d in duals])

    @staticmethod
    def _cleanTweetScript(request, context):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        https://www.geeksforgeeks.org/twitter-sentiment-analysis-using-python/
        '''

        idNumList = []
        tweetList = []

        # Iterate over bundled rows
        for request_rows in request:
            
            # Iterate over rows
            for row in request_rows.rows:
                idNum = [d.numData for d in row.duals][0]
                idNumList.append(idNum)
        
                tweet = [d.strData for d in row.duals][1]
                tweet = tweet.replace("'",'999999')
                
                if tweet[:2]=='RT':
                    index = tweet.find(':')
                    tweet = tweet[index:]
                    
                tweetCleansed = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
                tweetCleansed = tweetCleansed.replace('999999',"'")
       
                tweetList.append(tweetCleansed)

        # Create an iterable of dual with the result
        dualsList = []
        dualsList.append([SSE.Dual(numData=d) for d in idNumList])
        dualsList.append([SSE.Dual(strData=d) for d in tweetList])

        response_rows = []
        for i in range(len(idNumList)):
            duals = [dualsList[z][i] for z in range(len(dualsList))]
            response_rows.append(SSE.Row(duals=iter(duals)))

        # Set and send Table header
        table = SSE.TableDescription(name='Sentiment')
        table.fields.add(dataType=SSE.NUMERIC)
        table.fields.add(dataType=SSE.STRING)
        md = (('qlik-tabledescription-bin', table.SerializeToString()),)
        context.send_initial_metadata(md)

        yield SSE.BundledRows(rows=response_rows)

        
    """
    Implementation of rpc functions.
    """

    def GetCapabilities(self, request, context):
        """
        Get capabilities.
        Note that either request or context is used in the implementation of this method, but still added as
        parameters. The reason is that gRPC always sends both when making a function call and therefore we must include
        them to avoid error messages regarding too many parameters provided from the client.
        :param request: the request, not used in this method.
        :param context: the context, not used in this method.
        :return: the capabilities.
        """
        logging.info('GetCapabilities')
        # Create an instance of the Capabilities grpc message
        # Enable(or disable) script evaluation
        # Set values for pluginIdentifier and pluginVersion
        capabilities = SSE.Capabilities(allowScript=True,
                                        pluginIdentifier='Sentiment',
                                        pluginVersion='v1.1.0')

        # If user defined functions supported, add the definitions to the message
        with open(self.function_definitions) as json_file:
            # Iterate over each function definition and add data to the capabilities grpc message
            for definition in json.load(json_file)['Functions']:
                function = capabilities.functions.add()
                function.name = definition['Name']
                function.functionId = definition['Id']
                function.functionType = definition['Type']
                function.returnType = definition['ReturnType']

                # Retrieve name and type of each parameter
                for param_name, param_type in sorted(definition['Params'].items()):
                    function.params.add(name=param_name, dataType=param_type)

                logging.info('Adding to capabilities: {}({})'.format(function.name,
                                                                     [p.name for p in function.params]))

        return capabilities

    def ExecuteFunction(self, request_iterator, context):
        """
        Execute function call.
        :param request_iterator: an iterable sequence of Row.
        :param context: the context.
        :return: an iterable sequence of Row.
        """
        # Retrieve function id
        func_id = self._get_function_id(context)

        # Call corresponding function
        logging.info('ExecuteFunction (functionId: {})'.format(func_id))

        return getattr(self, self.functions[func_id])(request_iterator, context)

    def EvaluateScript(self, request, context):
        """
        This plugin provides functionality only for script calls with no parameters and tensor script calls.
        :param request:
        :param context:
        :return:
        """
        # Parse header for script request
        metadata = dict(context.invocation_metadata())
        header = SSE.ScriptRequestHeader()
        header.ParseFromString(metadata['qlik-scriptrequestheader-bin'])

        # Retrieve function type
        func_type = self.ScriptEval.get_func_type(header)

        # Verify function type
        if (func_type == FunctionType.Aggregation) or (func_type == FunctionType.Tensor):
            return self.ScriptEval.EvaluateScript(header, request, context, func_type)
        else:
            # This plugin does not support other function types than aggregation  and tensor.
            # Make sure the error handling, including logging, works as intended in the client
            msg = 'Function type {} is not supported in this plugin.'.format(func_type.name)
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details(msg)
            # Raise error on the plugin-side
            raise grpc.RpcError(grpc.StatusCode.UNIMPLEMENTED, msg)

    """
    Implementation of the Server connecting to gRPC.
    """

    def Serve(self, port, pem_dir):
        """
        Sets up the gRPC Server with insecure connection on port
        :param port: port to listen on.
        :param pem_dir: Directory including certificates
        :return: None
        """
        # Create gRPC server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        SSE.add_ConnectorServicer_to_server(self, server)

        if pem_dir:
            # Secure connection
            with open(os.path.join(pem_dir, 'sse_server_key.pem'), 'rb') as f:
                private_key = f.read()
            with open(os.path.join(pem_dir, 'sse_server_cert.pem'), 'rb') as f:
                cert_chain = f.read()
            with open(os.path.join(pem_dir, 'root_cert.pem'), 'rb') as f:
                root_cert = f.read()
            credentials = grpc.ssl_server_credentials([(private_key, cert_chain)], root_cert, True)
            server.add_secure_port('[::]:{}'.format(port), credentials)
            logging.info('*** Running server in secure mode on port: {} ***'.format(port))
        else:
            # Insecure connection
            server.add_insecure_port('[::]:{}'.format(port))
            logging.info('*** Running server in insecure mode on port: {} ***'.format(port))

        # Start gRPC server
        server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', default='50055')
    parser.add_argument('--pem_dir', nargs='?')
    parser.add_argument('--definition_file', nargs='?', default='functions.json')
    args = parser.parse_args()

    # need to locate the file when script is called from outside it's location dir.
    def_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.definition_file)

    calc = ExtensionService(def_file)
    calc.Serve(args.port, args.pem_dir)
