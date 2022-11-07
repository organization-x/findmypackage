const accordion = document.getElementsByClassName('container');

for (i=0; i<accordion.length; i++) {
  accordion[i].addEventListener('click', function () {
    this.classList.toggle('active')
  })
}

function myFunction() {
  var element = document.body;
  element.classList.toggle("dark-mode");
  initMap();
}