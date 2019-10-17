var AWS = require('aws-sdk');

// Initialize the Amazon Cognito credentials provider
AWS.config.region = 'us-east-1'; // Region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
IdentityPoolId: 'us-east-1:a541b1d8-9777-49c5-917e-6aeb144de05b',
});


const pushChat = async(event)=> {

    let result = await new Promise((resolve, reject) => {
            // if there is text to be sent...
	    var requestText =  event.messages[0].unstructured.text;
    	var requestDate = event.messages[0].unstructured.timestamp;
    	if (requestText && requestText.trim().length > 0) {
    	   	// disable input to show we're sending it
    	    var inputText = requestText.trim();
            var lexruntime = new AWS.LexRuntime();
            var lexUserId = event.messages[0].unstructured.id;
            var sessionAttributes = {};
		    // send it to the Lex runtime
		    var params = {
			    botAlias: 'dcb',
			    botName: 'DinningConciergeBot',
			    inputText: inputText,
			    userId: lexUserId,
			    sessionAttributes: sessionAttributes
		    };
		    console.log("Posting Text to Lex...");
		    lexruntime.postText(params, function(err, data) {
		        if (err) {
			        console.log("index.js:[postText err]"+err, err.stack);
			        reject('Error:  ' + err.message + ' (see console for details)');
		        }
		    	if (data) {
		    		// capture the sessionAttributes for the next cycle
			    	sessionAttributes = data.sessionAttributes;
			    	// show response and/or error/dialog status
			    	resolve(data);
		    	}
	    	});
	    }else{
	        reject('empty string');
	    }
    });
	return result;
}


exports.handler = async (event) => {
    var messageSentToClient;
    try{
        const lexResponse=await pushChat(event)

        messageSentToClient=lexResponse.message;
    
	    if (lexResponse.dialogState === 'ReadyForFulfillment') {
            console.log(lexResponse.intentName+" is "+lexResponse.dialogState);
		// TODO:  show slot values
	    } else {
	        console.log('(' + lexResponse.dialogState + ')');
	    }
    }catch(err){
        console.log(err.message);
    }
    // Initialize the Amazon Cognito credentials provider
    
    // TODO implement
    const response = {
        statusCode: 200,
        headers: {
          "Access-Control-Allow-Origin": "*"
        },
        body: JSON.stringify({
            "messages": [
            {
                "type": "string",
                "unstructured": {
                "id": event.messages[0].unstructured.id,
                "text":messageSentToClient,
                "timestamp": "string"
                }
            }
            ]
        }),
    };
    return response;
};