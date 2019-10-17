


// Chat base HTML (without user list and messages)
const chatHTML = `<main class="flex flex-column">
  <header class="title-bar flex flex-row flex-center">
    <div class="title-wrapper block center-element">
      <img class="logo" src="http://feathersjs.com/img/feathers-logo-wide.png"
        alt="Feathers Logo">
      <span class="title">Chat</span>
    </div>
  </header>

  <div class="flex flex-row flex-1 clear">
    <aside class="sidebar col col-3 flex flex-column flex-space-between">
      <header class="flex flex-row flex-center">
        <h4 class="font-300 text-center">
          <span class="font-600 online-count">0</span> services
        </h4>
      </header>

      <ul class="flex flex-column flex-1 list-unstyled user-list"></ul>
      <footer class="flex flex-row flex-center">
        <a href="#" id="logout" class="button button-primary">
          Sign Out
        </a>
      </footer>
    </aside>

    <div class="flex flex-column col col-9">
      <main class="chat flex flex-column flex-1 clear"></main>

      <form class="flex flex-row flex-space-between" id="send-message">
        <input type="text" name="text" class="flex flex-1">
        <button class="button-primary" type="submit">Send</button>
      </form>
    </div>
  </div>
</main>`;

// // Add a new user to the list
const addUser = user => {
    const userList = document.querySelector('.user-list');
    if(userList) {
        // Add the user to the list
        userList.innerHTML += `<li>
      <a class="block relative" href="#">
        <img src="${user.avatar}" alt="" class="avatar">
        <span class="absolute username">${user.email}</span>
      </a>
    </li>`;
        // Update the number of users
        document.querySelector('.online-count').innerHTML = document.querySelectorAll('.user-list li').length;
    }
};
const admin={
    'avatar':'/favicon.ico',
    'email':'AWS Chatbot'
};

let random=Math.random();
console.log(random+"");
let ID=hex_md5(random+"");

document.addEventListener("DOMContentLoaded", function() {
    addUser(admin);
});


// Renders a message to the page
const addMessage = message => {
    // The user that sent this message (added by the populate-user hook)
    const chat = document.querySelector('.chat');
    // Escape HTML to prevent XSS attacks
    var user=message.user;

    const text = message.text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;').replace(/>/g, '&gt;');
    if(chat) {
        chat.innerHTML += `<div class="message flex flex-row">
      <img src=${user.avatar} alt="User" class="avatar">
      <div class="message-wrapper">
        <p class="message-header">
          <span class="username font-600">${user.email}</span>
          <span class="sent-date font-300">${message.createdAt.toLocaleString()}</span>
        </p>
        <p class="message-content font-300">${text}</p>
      </div>
    </div>`;
        // Always scroll to the bottom of our message list
        chat.scrollTop = chat.scrollHeight - chat.clientHeight;
    }
};

// Shows the chat page
const showChat = async () => {
    document.getElementById('app').innerHTML = chatHTML;
};
// Shows the chat page
// const showChat = async () => {
//     document.getElementById('app').innerHTML = chatHTML;
//
//     // Find the latest 25 messages. They will come with the newest first
//     const messages = await client.service('messages').find({
//         query: {
//             $sort: { createdAt: -1 },
//             $limit: 25
//         }
//     });
//
//     // We want to show the newest message last
//     messages.data.reverse().forEach(addMessage);
//
//     // Find all users
//     const users = await client.service('users').find();
//
//     // Add each user to the list
//     users.data.forEach(addUser);
// };

showChat();


const addEventListener = (selector, event, handler) => {
    document.addEventListener(event, async ev => {
        if (ev.target.closest(selector)) {
            handler(ev);
        }
    });
};

const sendMessage = async(message)=>{
    let response = await new Promise((resolve, reject) => {

        var apigClient = apigClientFactory.newClient();
        var params = {
            //This is where any header, path, or querystring request params go. The key is the parameter named as defined in the API
            'content-type': 'application/json'
        };

        var body = {
            "messages": [
                {
                    "type": "string",
                    "unstructured": {
                        "id": ID,
                        "text": message,
                        "timestamp": new Date().toLocaleString()
                    }
                }
            ]
        };
        var additionalParams={};
        apigClient.chatbotPost(params, body, additionalParams)
            .then(function(result){
                if(result.headers["content-type"]==='application/json'){
                    var body = result.data.body;
                    console.log(body);
                    var output=JSON.parse(body).messages[0].unstructured.text;
                    resolve(output);
                } else {
                    console.log(result.headers["content-type"]);
                }
                //This is where you would put a success callback
            }).catch( function(result){
                console.error("Error callback:\n"+result);
            //This is where you would put an error callback
        });
    });
    return response;
};


// "Send" message form submission handler
addEventListener('#send-message', 'submit', async ev => {
    // This is the message text input field
    const input = document.querySelector('[name="text"]');

    ev.preventDefault();

    // Create a new message and then clear the input field
    if(input.value===''||input.value.match("^\\s*$")){
        input.value = '';
        return;
    }

    var message=input.value.substring(0,400);

    addMessage({
        user:{
            'avatar':"https://s.gravatar.com/avatar?s=50",
            'email':'User'
        },
        text:message,
        createdAt:new Date()
    });

    input.value = '';

    const response = await sendMessage(message);
    await addMessage({
        user:admin,
        text:response.toString(),
        createdAt:new Date()
    });
});


