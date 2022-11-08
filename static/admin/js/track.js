const accordion = document.getElementsByClassName('container');

for (i=0; i<accordion.length; i++) {
  accordion[i].addEventListener('click', function () {
    this.classList.toggle('active')
  })
}

var element = document.body;

const check=document.getElementById("check")

//If darkMode doesn’t exist in the LocalStorage, create it. False by default
if (localStorage.getItem('darkMode')===null){
  localStorage.setItem('darkMode', "false");
}

//Create a link tag to later link the CSS file we want

//Or we can create the tag in the HTML and later reference in our code
//const link=document.getElementsByTagName("link");  

//checkStatus is only called one time in the program, when you reload the page
//It gives the page it's default look, depening on waht darkMode is set to it will load one css or another
checkStatus()

function checkStatus(){
  if (localStorage.getItem('darkMode')==="true"){
      check.checked = true;                           //the checkbox is checked (if you load the page by default it isn’t)
      element.classList.add("dark-mode");                  //since it's true we load the dark theme CSS
  }else{
      check.checked = false;                          //the checkbox is unchecked
      element.classList.remove("dark-mode");
  }
}

function changeStatus(){                                //This function gets called every time the checkbox is clicked
  if (localStorage.getItem('darkMode')==="true"){     //if darkMode was active and this function is called it means the user now wants light
      localStorage.setItem('darkMode', "false");      //so we set it to false, to indicate we are in light mode
      element.classList.remove("dark-mode");  
  } else{
      localStorage.setItem('darkMode', "true");       //same code but adapted for dark theme
      element.classList.add("dark-mode");
  }
}
